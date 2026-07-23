from datetime import datetime, timezone

from src.logging_config import get_logger
from src.models import Task


logger = get_logger(__name__)


def create_visual_task(session, asset):
    task = Task(
        user_id=asset.user_id,
        course_id=asset.course_id,
        task_type="visual_generation",
        status="PENDING",
        progress=0,
        current_stage="queued",
        resource_type="visual_asset",
        resource_id=asset.id,
    )
    session.add(task)
    session.flush()
    asset.task_id = task.id
    asset.task = task
    _log_change(asset, task)
    return task


def sync_visual_task(
    session,
    asset,
    status=None,
    stage=None,
    progress=None,
    error_code=None,
    error_detail=None,
):
    task = asset.task
    if task is None:
        task = create_visual_task(session, asset)
    now = datetime.now(timezone.utc)
    task.status = status or task.status
    task.current_stage = stage or task.current_stage
    task.progress = _progress(task.status, task.progress, progress)
    task.updated_at = now
    if task.status == "RUNNING" and task.started_at is None:
        task.started_at = now
    if task.status in {"SUCCESS", "FAILED"}:
        task.finished_at = now
    else:
        task.finished_at = None
    task.error_code = error_code if task.status == "FAILED" else None
    task.error_detail = error_detail if task.status == "FAILED" else None
    session.flush()
    _log_change(asset, task)
    return task


def _progress(status, current, requested):
    if status == "SUCCESS":
        return 100
    if status == "PENDING":
        return 0
    return max(int(current or 0), max(0, min(100, int(requested or 0))))


def _log_change(asset, task):
    log = logger.error if task.status == "FAILED" else logger.info
    log(
        "Visual task state changed.",
        extra={
            "event": "task.visual.status.changed",
            "user_id": asset.user_id,
            "task_id": task.id,
            "document_id": asset.document_id,
            "course_id": asset.course_id,
            "visual_asset_id": asset.id,
            "status": task.status,
            "stage": task.current_stage,
            "exception": task.error_detail,
        },
    )
