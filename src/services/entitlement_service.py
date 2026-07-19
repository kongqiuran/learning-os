from datetime import datetime, timezone

from sqlalchemy import select, update
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


def reserve_scene(entitlement_id, scene, now=None):
    field = SCENE_FIELDS[scene]
    column = getattr(CourseEntitlement, field)
    current = now or datetime.now(timezone.utc)
    with get_db_session() as session:
        result = session.execute(
            update(CourseEntitlement)
            .where(
                CourseEntitlement.id == int(entitlement_id),
                CourseEntitlement.status == "active",
                CourseEntitlement.expires_at >= current,
                column > 0,
            )
            .values({field: column - 1})
        )
        if result.rowcount != 1:
            raise EntitlementQuotaExceeded("This course scene allowance has been used up.")


def release_scene(entitlement_id, scene):
    field = SCENE_FIELDS[scene]
    column = getattr(CourseEntitlement, field)
    with get_db_session() as session:
        result = session.execute(
            update(CourseEntitlement)
            .where(CourseEntitlement.id == int(entitlement_id))
            .values({field: column + 1})
        )
        if result.rowcount != 1:
            raise ValueError("The course entitlement no longer exists.")


def consume_scene(entitlement_id, scene):
    field = SCENE_FIELDS[scene]
    with get_db_session() as session:
        item = session.get(CourseEntitlement, int(entitlement_id))
        if item is None or getattr(item, field) <= 0:
            raise EntitlementQuotaExceeded("This course scene allowance has been used up.")
        setattr(item, field, getattr(item, field) - 1)


def reserve_assistant(user_id, course_id, now=None):
    entitlement = get_active_entitlement(user_id, course_id)
    if entitlement is None:
        raise EntitlementQuotaExceeded("A paid course entitlement is required for the course assistant.")
    current = now or datetime.now(timezone.utc)
    with get_db_session() as session:
        result = session.execute(
            update(CourseEntitlement)
            .where(
                CourseEntitlement.id == entitlement.id,
                CourseEntitlement.status == "active",
                CourseEntitlement.expires_at >= current,
                CourseEntitlement.assistant_remaining > 0,
            )
            .values(assistant_remaining=CourseEntitlement.assistant_remaining - 1)
        )
        if result.rowcount != 1:
            raise EntitlementQuotaExceeded("The course assistant allowance has been used up.")
    return entitlement.id


def release_assistant(entitlement_id):
    with get_db_session() as session:
        result = session.execute(
            update(CourseEntitlement)
            .where(CourseEntitlement.id == int(entitlement_id))
            .values(assistant_remaining=CourseEntitlement.assistant_remaining + 1)
        )
        if result.rowcount != 1:
            raise ValueError("The course entitlement no longer exists.")


def consume_assistant(user_id, course_id):
    return reserve_assistant(user_id, course_id)
