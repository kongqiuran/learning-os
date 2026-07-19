import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from src.database import create_database_tables, get_db_session
from src.models import Course, LearningPackage
from src.services.analysis_service import analyze_course
from src.config import DATA_DIR
from src.ops import send_alert
from src.services.quota_settlement_service import release_package_quota, settle_package_quota
from src.services.task_service import sync_package_task
from src.logging_config import configure_logging, get_logger


configure_logging()
logger = get_logger("learning_os.worker")
stop_event = threading.Event()


def _stop(*_args):
    stop_event.set()


def _worker_heartbeat():
    heartbeat_path = Path(DATA_DIR) / "database" / "worker-heartbeat"
    heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
    while not stop_event.is_set():
        heartbeat_path.touch()
        stop_event.wait(15)


def _recover_stale():
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=90)
    with get_db_session() as session:
        completed_reservations = list(session.scalars(select(LearningPackage.id).where(LearningPackage.status == "completed", LearningPackage.quota_state == "reserved")))
        for package_id in completed_reservations:
            settle_package_quota(session, package_id)
        failed_reservations = list(session.scalars(select(LearningPackage.id).where(LearningPackage.status == "failed", LearningPackage.quota_state == "reserved")))
        for package_id in failed_reservations:
            release_package_quota(session, package_id)
        tasks = list(session.scalars(select(LearningPackage).where(LearningPackage.status == "processing")))
        for task in tasks:
            heartbeat = task.heartbeat_at or task.claimed_at or task.created_at
            if heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            if heartbeat < cutoff:
                if task.task_attempts < 2:
                    task.status = "pending"
                    task.current_stage = "recovered"
                    course = session.get(Course, task.course_id)
                    if course is not None:
                        sync_package_task(session, task, course.user_id, status="PENDING", stage="recovered")
                else:
                    _fail_and_refund(session, task, "worker_lost", "Worker heartbeat expired twice.")


def _claim_next():
    with get_db_session() as session:
        task_id = session.scalar(select(LearningPackage.id).where(LearningPackage.status == "pending").order_by(LearningPackage.created_at, LearningPackage.id).limit(1))
        if task_id is None:
            return None
        claimed_at = datetime.now(timezone.utc)
        claimed = session.execute(
            update(LearningPackage)
            .where(LearningPackage.id == task_id, LearningPackage.status == "pending")
            .values(
                status="processing",
                claimed_at=claimed_at,
                heartbeat_at=claimed_at,
                task_attempts=LearningPackage.task_attempts + 1,
            )
            .returning(
                LearningPackage.id,
                LearningPackage.course_id,
                LearningPackage.scene,
                LearningPackage.scope_document_id,
                LearningPackage.scope_chapter_id,
                LearningPackage.scope_unassigned,
            )
        ).first()
        if claimed is None:
            return None
        course = session.get(Course, claimed.course_id)
        if course is None:
            return None
        package = session.get(LearningPackage, claimed.id)
        lifecycle_task_id = None
        if package is not None:
            lifecycle_task = sync_package_task(session, package, course.user_id, status="RUNNING", stage="starting")
            lifecycle_task_id = lifecycle_task.id
        return (claimed.id, claimed.course_id, course.user_id, claimed.scene, claimed.scope_document_id, claimed.scope_chapter_id, claimed.scope_unassigned, lifecycle_task_id)


def _heartbeat(task_id):
    while not stop_event.wait(15):
        with get_db_session() as session:
            task = session.get(LearningPackage, task_id)
            if task is None or task.status != "processing":
                return
            task.heartbeat_at = datetime.now(timezone.utc)
            course = session.get(Course, task.course_id)
            if course is not None:
                sync_package_task(session, task, course.user_id, status="RUNNING", stage=task.current_stage)


def _fail_and_refund(session, task, error_type, detail):
    task.status = "failed"
    task.error_type = error_type
    task.error_detail = detail
    task.finished_at = datetime.now(timezone.utc)
    course = session.get(Course, task.course_id)
    if course is not None:
        sync_package_task(session, task, course.user_id, status="FAILED", stage=task.current_stage, error_code=error_type, error_detail=detail)
    release_package_quota(session, task.id)


def _process_claimed(claimed):
    package_id, course_id, user_id, scene, scope_document_id, scope_chapter_id, scope_unassigned, task_id = claimed
    task_heartbeat = threading.Thread(target=_heartbeat, args=(package_id,), daemon=True)
    task_heartbeat.start()
    try:
        analyze_course(course_id, user_id, package_id=package_id, scene=None if scene == "legacy" else scene, scope_document_id=scope_document_id, scope_chapter_id=scope_chapter_id, scope_unassigned=scope_unassigned)
    except Exception as exc:
        logger.exception(
            "AI generation task failed.",
            extra={
                "event": "worker.generation.failed",
                "user_id": user_id,
                "task_id": task_id,
                "document_id": scope_document_id,
                "course_id": course_id,
                "package_id": package_id,
                "scene": scene,
                "exception": exc,
            },
        )
        send_alert("generation_failed", "AI generation task failed", task_id=package_id, scene=scene)
        with get_db_session() as session:
            task = session.get(LearningPackage, package_id)
            if task is not None:
                if task.task_attempts >= 2:
                    _fail_and_refund(session, task, type(exc).__name__, str(exc)[:2000])
                else:
                    task.status = "pending"
                    task.current_stage = "retry_queued"
                    sync_package_task(session, task, user_id, status="PENDING", stage="retry_queued")
        return

    try:
        with get_db_session() as session:
            settle_package_quota(session, package_id)
    except Exception as exc:
        logger.exception(
            "Quota settlement failed.",
            extra={
                "event": "worker.quota_settlement.failed",
                "user_id": user_id,
                "task_id": task_id,
                "document_id": scope_document_id,
                "course_id": course_id,
                "package_id": package_id,
                "scene": scene,
                "exception": exc,
            },
        )
        send_alert("quota_settlement_failed", "AI generation completed but quota settlement failed", task_id=package_id, scene=scene)
    logger.info(
        "AI generation task completed.",
        extra={
            "event": "worker.generation.success",
            "user_id": user_id,
            "task_id": task_id,
            "document_id": scope_document_id,
            "course_id": course_id,
            "package_id": package_id,
            "scene": scene,
            "status": "SUCCESS",
        },
    )


def run():
    create_database_tables()
    _recover_stale()
    worker_heartbeat = threading.Thread(target=_worker_heartbeat, daemon=True)
    worker_heartbeat.start()
    concurrency = max(1, min(4, int(os.getenv("LEARNING_OS_WORKER_CONCURRENCY", "2"))))
    active = set()
    last_recovery = time.monotonic()
    logger.info(
        "Worker started.",
        extra={"event": "worker.started", "status": "RUNNING"},
    )
    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="generation") as executor:
        while not stop_event.is_set():
            if time.monotonic() - last_recovery >= 30:
                _recover_stale()
                last_recovery = time.monotonic()
            active = {future for future in active if not future.done()}
            if len(active) >= concurrency:
                stop_event.wait(0.5)
                continue
            claimed = _claim_next()
            if claimed is None:
                stop_event.wait(2)
                continue
            active.add(executor.submit(_process_claimed, claimed))


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    run()
