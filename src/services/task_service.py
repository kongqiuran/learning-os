from datetime import datetime, timezone

from src.models import Task


PACKAGE_STATUS_TO_TASK_STATUS = {
    "pending": "PENDING",
    "processing": "RUNNING",
    "completed": "SUCCESS",
    "failed": "FAILED",
}

STAGE_PROGRESS = {
    "pending": ("queued", 0),
    "recovered": ("queued", 0),
    "retry_queued": ("queued", 0),
    "starting": ("preparing", 5),
    "document_analyzer": ("document_analysis", 25),
    "course_analyzer": ("knowledge_generation", 60),
    "follow_chapter_generator": ("knowledge_generation", 70),
    "learning_package_generator": ("content_generation", 85),
    "completed": ("completed", 100),
}


def create_package_task(session, user_id, course_id, scene):
    task = Task(
        user_id=int(user_id),
        course_id=int(course_id),
        task_type=f"{scene}_generation" if scene != "legacy" else "course_generation",
        status="PENDING",
        progress=0,
        current_stage="queued",
        resource_type="learning_package",
    )
    session.add(task)
    session.flush()
    return task


def sync_package_task(session, package, user_id, status=None, stage=None, error_code=None, error_detail=None):
    task = package.task
    if task is None:
        task = create_package_task(session, user_id, package.course_id, package.scene)
        task.resource_id = package.id
        package.task_id = task.id
        package.task = task

    target_status = status or PACKAGE_STATUS_TO_TASK_STATUS.get(package.status, "PENDING")
    normalized_stage, progress = _stage_details(stage or package.current_stage, target_status, task.progress)
    now = datetime.now(timezone.utc)

    task.status = target_status
    task.current_stage = normalized_stage
    task.progress = progress
    task.updated_at = now
    if target_status == "RUNNING" and task.started_at is None:
        task.started_at = now
    if target_status in {"SUCCESS", "FAILED"}:
        task.finished_at = now
    else:
        task.finished_at = None
    task.error_code = error_code if target_status == "FAILED" else None
    task.error_detail = error_detail if target_status == "FAILED" else None
    session.flush()
    return task


def fail_package_task(session, package, user_id, error_code, error_detail):
    now = datetime.now(timezone.utc)
    package.status = "failed"
    package.error_type = str(error_code)[:120]
    package.error_detail = str(error_detail)[:4000]
    package.finished_at = now
    return sync_package_task(
        session,
        package,
        user_id,
        status="FAILED",
        stage=package.current_stage,
        error_code=package.error_type,
        error_detail=package.error_detail,
    )


def _stage_details(stage, status, current_progress):
    if status == "SUCCESS":
        return "completed", 100
    normalized_stage, configured_progress = STAGE_PROGRESS.get(stage, (stage or "processing", current_progress or 0))
    if status == "PENDING":
        return "queued", 0
    return normalized_stage, configured_progress
