import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select

from src.ai.document.page_analyzer import analyze_visual_page
from src.ai.document.parser import parse_pdf_pages, render_pdf_page
from src.ai.document.vision_router import route_page
from src.ai.providers.qwen_vision_provider import QwenVisionProvider
from src.config import get_vision_config
from src.database import get_db_session
from src.logging_config import get_logger
from src.models import DocumentPage
from src.storage import (
    build_document_page_path,
    resolve_document_path,
    store_derived_path,
)


DOCUMENT_INTELLIGENCE_PIPELINE_VERSION = "document-intelligence-v1"
logger = get_logger(__name__)


@dataclass(frozen=True)
class UnderstoodPage:
    page_number: int
    page_type: str
    text_content: str
    vision_result: dict[str, Any]
    requires_vision: bool
    analysis_status: str


@dataclass(frozen=True)
class DocumentUnderstandingResult:
    pages: list[UnderstoodPage]
    pipeline_version: str
    degraded: bool
    vision_provider_available: bool

    def to_prompt_payload(self, max_chars):
        if not self.pages:
            return {
                "pipeline_version": self.pipeline_version,
                "degraded": self.degraded,
                "pages": [],
            }
        compact_vision = [_compact_vision(page.vision_result) for page in self.pages]
        vision_size = sum(
            len(json.dumps(item, ensure_ascii=False)) for item in compact_vision
        )
        available_for_text = max(1000, int(max_chars) - vision_size - 1000)
        text_per_page = max(200, min(10000, available_for_text // len(self.pages)))
        return {
            "pipeline_version": self.pipeline_version,
            "degraded": self.degraded,
            "pages": [
                {
                    "page_number": page.page_number,
                    "page_type": page.page_type,
                    "text": page.text_content[:text_per_page],
                    "vision_result": compact_vision[index],
                    "requires_vision": page.requires_vision,
                    "analysis_status": page.analysis_status,
                }
                for index, page in enumerate(self.pages)
            ],
        }


def understand_pdf(
    document,
    *,
    user_id,
    course_id,
    task_id=None,
    progress_callback=None,
    vision_provider=None,
):
    config = get_vision_config()
    source_path = resolve_document_path(document.file_path)
    _emit_progress(progress_callback, "parsing", 10)
    parsed_pages = parse_pdf_pages(source_path)
    if not parsed_pages:
        raise ValueError("No pages were found in the PDF file.")
    _emit_progress(progress_callback, "parsing", 25)

    routes = {page.page_number: route_page(page) for page in parsed_pages}
    selected_for_vision = _select_vision_pages(
        routes,
        config.max_pages_per_document,
    )
    provider = vision_provider
    if provider is None and config.enabled and config.provider == "qwen":
        provider = QwenVisionProvider(config=config)
    provider_available = bool(provider and provider.is_available())

    understood_pages = []
    degraded = False
    visual_pages = [
        page for page in parsed_pages if routes[page.page_number].requires_vision
    ]
    visual_completed = 0

    for parsed_page in parsed_pages:
        route = routes[parsed_page.page_number]
        cached = _prepare_page_record(
            document,
            parsed_page,
            route,
            provider,
        )
        logger.info(
            "PDF page routed.",
            extra={
                "event": "document.page.routed",
                "user_id": user_id,
                "task_id": task_id,
                "document_id": document.id,
                "course_id": course_id,
                "page_number": parsed_page.page_number,
                "requires_vision": route.requires_vision,
                "routing_reason": route.reason,
                "status": "cached" if cached is not None else "pending",
            },
        )
        if cached is not None:
            understood_pages.append(cached)
            if route.requires_vision:
                visual_completed += 1
            continue

        if not route.requires_vision:
            page_result = _finish_without_vision(
                document.id,
                parsed_page,
                status="skipped",
                requires_vision=False,
            )
            understood_pages.append(page_result)
            continue

        if parsed_page.page_number not in selected_for_vision:
            degraded = True
            page_result = _finish_without_vision(
                document.id,
                parsed_page,
                status="failed",
                error_detail=(
                    "Vision page limit reached; extracted text fallback was used."
                ),
                requires_vision=True,
            )
            understood_pages.append(page_result)
            visual_completed += 1
            continue

        if not provider_available:
            degraded = True
            page_result = _finish_without_vision(
                document.id,
                parsed_page,
                status="failed",
                provider=getattr(provider, "provider_name", config.provider or None),
                model=getattr(provider, "model_name", config.model or None),
                error_detail=(
                    "Vision provider is unavailable; extracted text fallback was used."
                ),
                requires_vision=True,
            )
            understood_pages.append(page_result)
            visual_completed += 1
            continue

        try:
            _emit_progress(progress_callback, "rendering", 30)
            image_path = build_document_page_path(
                user_id,
                course_id,
                document.id,
                parsed_page.page_number,
            )
            render_pdf_page(
                source_path,
                parsed_page.page_number,
                image_path,
                dpi=config.render_dpi,
            )
            stored_image_path = store_derived_path(image_path)
            _update_page_status(
                document.id,
                parsed_page.page_number,
                status="rendered",
                image_path=stored_image_path,
                provider=provider.provider_name,
                model=provider.model_name,
            )
            _update_page_status(
                document.id,
                parsed_page.page_number,
                status="processing",
            )
            analysis = analyze_visual_page(
                provider,
                Path(image_path),
                parsed_page.text_content,
                {
                    "page_number": parsed_page.page_number,
                    "page_type": parsed_page.page_type,
                    **parsed_page.features,
                },
                user_id=user_id,
                task_id=task_id,
                document_id=document.id,
                page_number=parsed_page.page_number,
            )
            _update_page_status(
                document.id,
                parsed_page.page_number,
                status="completed",
                vision_result=analysis.content,
                provider=analysis.provider,
                model=analysis.model,
                input_tokens=analysis.input_tokens,
                output_tokens=analysis.output_tokens,
                error_detail=None,
            )
            page_result = _understood_page(
                parsed_page,
                analysis.content,
                route.requires_vision,
                "completed",
            )
        except Exception as exc:
            degraded = True
            error_detail = str(exc).strip()[:2000] or type(exc).__name__
            _update_page_status(
                document.id,
                parsed_page.page_number,
                status="failed",
                error_detail=error_detail,
            )
            page_result = _understood_page(
                parsed_page,
                {},
                route.requires_vision,
                "failed",
            )
        understood_pages.append(page_result)
        visual_completed += 1
        if visual_pages:
            progress = 35 + int(25 * visual_completed / len(visual_pages))
            _emit_progress(progress_callback, "vision_analysis", progress)

    if not any(
        page.text_content.strip() or page.vision_result for page in understood_pages
    ):
        raise ValueError(
            "No usable text or visual understanding was produced from the PDF."
        )
    return DocumentUnderstandingResult(
        pages=understood_pages,
        pipeline_version=DOCUMENT_INTELLIGENCE_PIPELINE_VERSION,
        degraded=degraded,
        vision_provider_available=provider_available,
    )


def _prepare_page_record(document, parsed_page, route, provider):
    with get_db_session() as session:
        page = session.scalar(
            select(DocumentPage).where(
                DocumentPage.document_id == document.id,
                DocumentPage.page_number == parsed_page.page_number,
            )
        )
        provider_name = getattr(provider, "provider_name", None)
        model_name = getattr(provider, "model_name", None)
        cache_hit = bool(
            page is not None
            and page.content_hash == parsed_page.content_hash
            and page.pipeline_version == DOCUMENT_INTELLIGENCE_PIPELINE_VERSION
            and (
                (
                    not route.requires_vision
                    and page.analysis_status == "skipped"
                )
                or (
                    route.requires_vision
                    and page.analysis_status == "completed"
                    and page.provider == provider_name
                    and page.model == model_name
                )
            )
        )
        if page is None:
            page = DocumentPage(
                document_id=document.id,
                page_number=parsed_page.page_number,
                content_hash=parsed_page.content_hash,
                pipeline_version=DOCUMENT_INTELLIGENCE_PIPELINE_VERSION,
            )
            session.add(page)
        page.page_type = parsed_page.page_type
        page.text_content = parsed_page.text_content
        page.requires_vision = route.requires_vision
        page.routing_reason = route.reason
        page.content_hash = parsed_page.content_hash
        page.pipeline_version = DOCUMENT_INTELLIGENCE_PIPELINE_VERSION
        if not cache_hit:
            page.analysis_status = "pending"
            page.vision_result = {}
            page.input_tokens = 0
            page.output_tokens = 0
            page.error_detail = None
        session.flush()
        if not cache_hit:
            return None
        return UnderstoodPage(
            page_number=page.page_number,
            page_type=page.page_type,
            text_content=page.text_content,
            vision_result=dict(page.vision_result or {}),
            requires_vision=page.requires_vision,
            analysis_status=page.analysis_status,
        )


def _finish_without_vision(
    document_id,
    parsed_page,
    *,
    status,
    provider=None,
    model=None,
    error_detail=None,
    requires_vision=False,
):
    _update_page_status(
        document_id,
        parsed_page.page_number,
        status=status,
        provider=provider,
        model=model,
        error_detail=error_detail,
    )
    return _understood_page(
        parsed_page,
        {},
        requires_vision,
        status,
    )


def _understood_page(parsed_page, vision_result, requires_vision, status):
    return UnderstoodPage(
        page_number=parsed_page.page_number,
        page_type=parsed_page.page_type,
        text_content=parsed_page.text_content,
        vision_result=dict(vision_result or {}),
        requires_vision=bool(requires_vision),
        analysis_status=status,
    )


def _update_page_status(document_id, page_number, *, status, **values):
    with get_db_session() as session:
        page = session.scalar(
            select(DocumentPage).where(
                DocumentPage.document_id == int(document_id),
                DocumentPage.page_number == int(page_number),
            )
        )
        if page is None:
            raise RuntimeError("Document page disappeared during analysis.")
        page.analysis_status = status
        for name, value in values.items():
            if value is not None or name == "error_detail":
                setattr(page, name, value)


def _select_vision_pages(routes, maximum):
    candidates = [
        (page_number, route.complexity)
        for page_number, route in routes.items()
        if route.requires_vision
    ]
    candidates.sort(key=lambda item: (-item[1], item[0]))
    return {page_number for page_number, _ in candidates[: int(maximum)]}


def _emit_progress(callback, stage, progress):
    if callback is not None:
        callback(stage=stage, progress=max(0, min(100, int(progress))))


def _compact_vision(value):
    if isinstance(value, dict):
        return {
            str(key)[:120]: _compact_vision(item)
            for key, item in list(value.items())[:30]
        }
    if isinstance(value, list):
        return [_compact_vision(item) for item in value[:20]]
    if isinstance(value, str):
        return value[:1200]
    return value
