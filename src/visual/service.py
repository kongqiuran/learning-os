import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.database import get_db_session
from src.logging_config import get_logger
from src.models import Document, DocumentAnalysis, VisualAsset
from src.services.visual_task_service import create_visual_task, sync_visual_task
from src.visual.generators import MermaidGenerator, SvgGenerator
from src.visual.planner import PLANNER_VERSION, VisualPlanner
from src.visual.target_resolver import VisualTargetNotFoundError, resolve_target


GENERATOR_VERSION = "deterministic-v1"
MAX_AUTOMATIC_VISUALS_PER_DOCUMENT = 3
logger = get_logger(__name__)


class VisualService:
    def __init__(self, planner=None, generators=None):
        self.planner = planner or VisualPlanner()
        self.generators = generators or {
            "mermaid": MermaidGenerator(),
            "svg": SvgGenerator(),
        }

    def request_generation(self, target_type, target_id, user_id):
        item, snapshot = resolve_target(target_type, target_id, user_id)
        plan = self.planner.plan(snapshot)
        if not plan.need_visual:
            return None, plan
        source_hash = build_source_hash(snapshot)

        with get_db_session() as session:
            existing = session.scalar(
                select(VisualAsset).where(
                    VisualAsset.user_id == int(user_id),
                    VisualAsset.target_type == target_type,
                    VisualAsset.target_id == target_id,
                    VisualAsset.type == plan.type,
                    VisualAsset.generator == plan.generator,
                    VisualAsset.source_hash == source_hash,
                )
            )
            if existing is not None:
                return existing, plan
            asset = VisualAsset(
                user_id=int(user_id),
                course_id=item.course_id,
                document_id=item.document_id,
                target_type=target_type,
                target_id=target_id,
                type=plan.type,
                generator=plan.generator,
                status="pending",
                target_snapshot=snapshot,
                source_hash=source_hash,
                asset_metadata={
                    "planner_version": PLANNER_VERSION,
                    "generator_version": GENERATOR_VERSION,
                    "plan": plan.to_dict(),
                    "confidence": plan.confidence,
                    "reason": plan.reason,
                },
            )
            session.add(asset)
            session.flush()
            create_visual_task(session, asset)
            session.flush()
            return asset, plan

    def list_current(self, target_type, target_id, user_id):
        _item, snapshot = resolve_target(target_type, target_id, user_id)
        source_hash = build_source_hash(snapshot)
        with get_db_session() as session:
            return list(
                session.scalars(
                    select(VisualAsset)
                    .where(
                        VisualAsset.user_id == int(user_id),
                        VisualAsset.target_type == target_type,
                        VisualAsset.target_id == target_id,
                        VisualAsset.source_hash == source_hash,
                    )
                    .order_by(VisualAsset.created_at.desc(), VisualAsset.id.desc())
                )
            )

    def enqueue_for_documents(self, user_id, course_id, document_ids):
        candidates = []
        with get_db_session() as session:
            rows = session.execute(
                select(Document, DocumentAnalysis)
                .join(DocumentAnalysis, DocumentAnalysis.document_id == Document.id)
                .where(
                    Document.user_id == int(user_id),
                    Document.course_id == int(course_id),
                    Document.id.in_([int(value) for value in document_ids]),
                )
            ).all()
        from src.api.adapters.knowledge_adapter import create_knowledge_key

        for document, analysis in rows:
            topics = analysis.topics if isinstance(analysis.topics, list) else []
            document_candidates = []
            for index, topic in enumerate(topics):
                target_id = create_knowledge_key(analysis.id, index)
                try:
                    _item, snapshot = resolve_target("knowledge_item", target_id, user_id)
                except VisualTargetNotFoundError:
                    continue
                plan = self.planner.plan(snapshot)
                if plan.need_visual:
                    document_candidates.append(
                        (int(snapshot.get("importance") or 0), plan.complexity, target_id)
                    )
            document_candidates.sort(reverse=True)
            candidates.extend(
                target_id
                for _importance, _complexity, target_id
                in document_candidates[:MAX_AUTOMATIC_VISUALS_PER_DOCUMENT]
            )

        created = []
        for target_id in candidates:
            try:
                asset, _plan = self.request_generation(
                    "knowledge_item",
                    target_id,
                    user_id,
                )
                if asset is not None:
                    created.append(asset.id)
            except IntegrityError:
                # A concurrent enqueue won the unique target-version race.
                logger.info(
                    "Visual generation request already exists.",
                    extra={
                        "event": "visual.enqueue.duplicate",
                        "user_id": user_id,
                        "course_id": course_id,
                        "target_id": target_id,
                    },
                )
        return created

    def process_asset(self, asset_id):
        with get_db_session() as session:
            asset = session.get(VisualAsset, int(asset_id))
            if asset is None:
                raise LookupError("The visual asset does not exist.")
            if asset.status == "completed":
                return asset
            asset.status = "generating"
            sync_visual_task(
                session,
                asset,
                status="RUNNING",
                stage="generating",
                progress=55,
            )
            generator_name = asset.generator
            plan = dict((asset.asset_metadata or {}).get("plan") or {})
            spec = dict(plan.get("spec") or {})

        generator = self.generators.get(generator_name)
        if generator is None:
            raise ValueError(f"Unsupported visual generator: {generator_name}")
        content = generator.generate(spec)

        with get_db_session() as session:
            asset = session.get(VisualAsset, int(asset_id))
            if asset is None:
                raise LookupError("The visual asset does not exist.")
            asset.content = content
            asset.status = "completed"
            asset.error_code = None
            asset.error_detail = None
            asset.heartbeat_at = datetime.now(timezone.utc)
            sync_visual_task(
                session,
                asset,
                status="SUCCESS",
                stage="completed",
                progress=100,
            )
            logger.info(
                "Visual generation completed.",
                extra={
                    "event": "visual.generation.success",
                    "user_id": asset.user_id,
                    "task_id": asset.task_id,
                    "document_id": asset.document_id,
                    "course_id": asset.course_id,
                    "visual_asset_id": asset.id,
                    "generator": asset.generator,
                },
            )
            return asset


def build_source_hash(snapshot):
    payload = {
        "snapshot": snapshot,
        "planner_version": PLANNER_VERSION,
        "generator_version": GENERATOR_VERSION,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
