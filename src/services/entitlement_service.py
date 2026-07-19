from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database import get_db_session
from src.models import CourseEntitlement


SCENE_FIELDS = {"follow": "follow_remaining", "textbook": "textbook_remaining", "exam": "exam_remaining"}


class EntitlementQuotaExceeded(ValueError):
    pass


def get_active_entitlement(user_id, course_id, now=None):
    current = now or datetime.now(timezone.utc)
    with get_db_session() as session:
        return session.scalar(select(CourseEntitlement).where(CourseEntitlement.user_id == int(user_id), CourseEntitlement.course_id == int(course_id), CourseEntitlement.status == "active", CourseEntitlement.expires_at >= current).order_by(CourseEntitlement.activated_at.desc()))


def list_entitlements(user_id):
    with get_db_session() as session:
        return list(session.scalars(select(CourseEntitlement).options(joinedload(CourseEntitlement.course)).where(CourseEntitlement.user_id == int(user_id)).order_by(CourseEntitlement.activated_at.desc())))


def require_scene_allowance(entitlement, scene):
    field = SCENE_FIELDS.get(scene)
    if field is None or getattr(entitlement, field) <= 0:
        raise EntitlementQuotaExceeded("This course scene allowance has been used up.")


def consume_scene(entitlement_id, scene):
    field = SCENE_FIELDS[scene]
    with get_db_session() as session:
        item = session.get(CourseEntitlement, int(entitlement_id))
        if item is None or getattr(item, field) <= 0:
            raise EntitlementQuotaExceeded("This course scene allowance has been used up.")
        setattr(item, field, getattr(item, field) - 1)


def consume_assistant(user_id, course_id):
    entitlement = get_active_entitlement(user_id, course_id)
    if entitlement is None:
        return
    with get_db_session() as session:
        item = session.get(CourseEntitlement, entitlement.id)
        if item.assistant_remaining <= 0:
            raise EntitlementQuotaExceeded("The course assistant allowance has been used up.")
        item.assistant_remaining -= 1
