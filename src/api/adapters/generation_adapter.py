from datetime import datetime, timedelta, timezone
from threading import Lock

from src.services.analysis_service import analyze_course, get_active_scoped_package, get_learning_package
from src.services.analysis_service import create_learning_package_task, get_scope_metadata


class GenerationInProgressError(RuntimeError):
    pass


_registry_lock = Lock()
_active_scope_keys = set()
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


def queue_course_package(course_id, user_id, scene="legacy", scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
    """Persist a task while holding only a request-local duplicate guard.

    The worker runs in a separate process, so retaining this in-memory lock after
    the task is created would permanently block later generations in the API
    process. Persisted pending/processing packages are the cross-process guard.
    """
    _, scope_key = get_scope_metadata(scope_document_id, scope_chapter_id, scope_unassigned)
    registry_key = (int(course_id), scene, scope_key)
    if not _claim_scope(registry_key):
        raise GenerationInProgressError("This content is already being generated.")

    try:
        latest_package = get_active_scoped_package(course_id, user_id, scene, scope_key)
        if _is_recent_processing_package(latest_package):
            raise GenerationInProgressError("This content is already being generated.")
        if scene == "legacy" and scope_document_id is None and scope_chapter_id is None and not scope_unassigned:
            return create_learning_package_task(course_id, user_id)
        return create_learning_package_task(course_id, user_id, scene, scope_document_id, scope_chapter_id, scope_unassigned)
    finally:
        _release_scope(registry_key)


def run_queued_course_package(package_id, course_id, user_id, scene=None, scope_document_id=None, scope_chapter_id=None, scope_unassigned=False):
    _, scope_key = get_scope_metadata(scope_document_id, scope_chapter_id, scope_unassigned)
    registry_key = (int(course_id), scene or "legacy", scope_key)
    try:
        if scene is None and scope_document_id is None and scope_chapter_id is None and not scope_unassigned:
            return analyze_course(course_id, user_id, language="zh", package_id=package_id)
        return analyze_course(course_id, user_id, language="zh", package_id=package_id, scene=scene, scope_document_id=scope_document_id, scope_chapter_id=scope_chapter_id, scope_unassigned=scope_unassigned)
    finally:
        _release_scope(registry_key)


def _claim_course(course_id):
    return _claim_scope((int(course_id), "legacy", "course"))


def _release_course(course_id):
    _release_scope((int(course_id), "legacy", "course"))


def _claim_scope(registry_key):
    with _registry_lock:
        if registry_key in _active_scope_keys:
            return False
        _active_scope_keys.add(registry_key)
        return True


def _release_scope(registry_key):
    with _registry_lock:
        _active_scope_keys.discard(registry_key)


def _is_recent_processing_package(package):
    if package is None or package.status not in {"pending", "processing"}:
        return False
    created_at = package.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - created_at < _RECENT_PROCESSING_WINDOW
