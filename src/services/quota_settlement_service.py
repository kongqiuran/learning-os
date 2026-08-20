# 文件说明：学习包额度结算服务。SQLAlchemy 的 update/delete/or_/and_ 用来原子更新额度状态，保证成功任务扣额度、失败任务返还额度。
from datetime import datetime, timezone

from sqlalchemy import and_, delete, or_, update

from src.models import CourseEntitlement, LearningPackage, UsageRecord
from src.services.entitlement_service import SCENE_FIELDS


def settle_package_quota(session, package_id):
    # 学习包成功后调用：把 quota_state 从 reserved 改成 consumed。
    # reserved 是“预扣”，consumed 是“最终扣除”；这样失败任务可以返还。
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
    # 学习包失败或 Worker 丢失超过重试次数时调用：返还预扣额度。
    # session.get 是 SQLAlchemy ORM 方法，按主键读取 LearningPackage。
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
        # 免费月额度通过 UsageRecord 计数；返还时删除这条使用记录。
        session.execute(delete(UsageRecord).where(UsageRecord.id == package.usage_record_id))
    elif source == "course_entitlement" and package.entitlement_id is not None:
        # 单课权益通过 CourseEntitlement 的 scene 字段计数；返还时把对应次数加回去。
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
