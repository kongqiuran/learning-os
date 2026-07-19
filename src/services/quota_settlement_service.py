from datetime import datetime, timezone

from sqlalchemy import and_, delete, or_, update

from src.models import CourseEntitlement, LearningPackage, UsageRecord
from src.services.entitlement_service import SCENE_FIELDS


def settle_package_quota(session, package_id):
    now = datetime.now(timezone.utc)
    result = session.execute(
        update(LearningPackage)
        .where(
            LearningPackage.id == int(package_id),
            or_(
                LearningPackage.quota_state == "reserved",
                and_(
                    LearningPackage.quota_state.is_(None),
                    or_(
                        LearningPackage.usage_record_id.is_not(None),
                        LearningPackage.entitlement_id.is_not(None),
                    ),
                ),
            ),
        )
        .values(quota_state="consumed", quota_settled_at=now)
    )
    return result.rowcount == 1


def release_package_quota(session, package_id):
    package = session.get(LearningPackage, int(package_id))
    if package is None or package.quota_state in {"consumed", "released"}:
        return False

    source = package.quota_source
    if source is None:
        if package.usage_record_id is not None:
            source = "free_monthly"
        elif package.entitlement_id is not None:
            source = "course_entitlement"

    now = datetime.now(timezone.utc)
    claimed = session.execute(
        update(LearningPackage)
        .where(
            LearningPackage.id == package.id,
            or_(
                LearningPackage.quota_state == "reserved",
                and_(
                    LearningPackage.quota_state.is_(None),
                    or_(
                        LearningPackage.usage_record_id.is_not(None),
                        LearningPackage.entitlement_id.is_not(None),
                    ),
                ),
            ),
        )
        .values(quota_source=source, quota_state="released", quota_settled_at=now)
    )
    if claimed.rowcount != 1:
        return False

    if source == "free_monthly" and package.usage_record_id is not None:
        session.execute(delete(UsageRecord).where(UsageRecord.id == package.usage_record_id))
    elif source == "course_entitlement" and package.entitlement_id is not None:
        field = SCENE_FIELDS.get(package.scene)
        if field is not None:
            column = getattr(CourseEntitlement, field)
            refunded = session.execute(
                update(CourseEntitlement)
                .where(CourseEntitlement.id == package.entitlement_id)
                .values({field: column + max(1, package.quota_units or 1)})
            )
            if refunded.rowcount != 1:
                raise ValueError("The course entitlement no longer exists.")
    return True
