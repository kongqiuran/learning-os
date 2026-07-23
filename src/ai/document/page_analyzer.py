import time

from src.logging_config import get_logger


logger = get_logger(__name__)


def analyze_visual_page(
    provider,
    image_path,
    page_text,
    metadata,
    *,
    user_id,
    task_id,
    document_id,
    page_number,
):
    started = time.monotonic()
    context = {
        "user_id": user_id,
        "task_id": task_id,
        "document_id": document_id,
        "page_number": page_number,
        "provider": provider.provider_name,
        "model": provider.model_name,
        "requires_vision": True,
    }
    logger.info(
        "Vision page analysis started.",
        extra={"event": "document.vision.started", **context},
    )
    try:
        result = provider.analyze_page(image_path, page_text, metadata)
    except Exception as exc:
        logger.exception(
            "Vision page analysis failed; text fallback will be used.",
            extra={
                "event": "document.vision.failed",
                **context,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "exception": exc,
            },
        )
        raise
    logger.info(
        "Vision page analysis completed.",
        extra={
            "event": "document.vision.success",
            **context,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
        },
    )
    return result
