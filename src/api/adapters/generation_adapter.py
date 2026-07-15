from datetime import datetime, timedelta, timezone
from threading import Lock

from src.services.analysis_service import analyze_course, get_learning_package


class GenerationInProgressError(RuntimeError):
    pass


_registry_lock = Lock()
_active_course_ids = set()
_RECENT_PROCESSING_WINDOW = timedelta(minutes=30)


def generate_course_package(course_id, user_id):
    """MVP single-process protection for synchronous package generation."""
    if not _claim_course(course_id):
        raise GenerationInProgressError("Course content generation is already in progress.")

    try:
        latest_package = get_learning_package(course_id, user_id)
        if _is_recent_processing_package(latest_package):
            raise GenerationInProgressError("Course content generation is already in progress.")
        return analyze_course(course_id, user_id, language="zh")
    finally:
        _release_course(course_id)


def _claim_course(course_id):
    with _registry_lock:
        if course_id in _active_course_ids:
            return False
        _active_course_ids.add(course_id)
        return True


def _release_course(course_id):
    with _registry_lock:
        _active_course_ids.discard(course_id)


def _is_recent_processing_package(package):
    if package is None or package.status != "processing":
        return False
    created_at = package.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created_at < _RECENT_PROCESSING_WINDOW
