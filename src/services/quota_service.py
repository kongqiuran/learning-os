import os
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from src.database import get_db_session
from src.models import UsageRecord, UserPlan


AI_GENERATION_METRIC = "ai_generation"
DEFAULT_FREE_MONTHLY_AI_GENERATIONS = 3
MAX_RESERVATION_ATTEMPTS = 3


class UsageQuotaExceededError(RuntimeError):
    def __init__(self, limit, used, resets_at):
        super().__init__("The monthly AI generation quota has been reached.")
        self.limit = limit
        self.used = used
        self.resets_at = resets_at


@dataclass(frozen=True)
class UsageReservation:
    id: int
    user_id: int
    period_key: str


def reserve_ai_generation(user_id, now=None):
    current_time = _as_utc(now or datetime.now(timezone.utc))
    period_key = current_time.strftime("%Y-%m")
    limit = _get_free_ai_generation_limit()

    for attempt in range(MAX_RESERVATION_ATTEMPTS):
        try:
            with get_db_session() as session:
                plan = session.scalar(
                    select(UserPlan).where(UserPlan.user_id == int(user_id))
                )
                if plan is None:
                    plan = UserPlan(user_id=int(user_id), plan_code="free", status="active")
                    session.add(plan)
                    session.flush()

                used = session.scalar(
                    select(func.coalesce(func.sum(UsageRecord.quantity), 0)).where(
                        UsageRecord.user_id == int(user_id),
                        UsageRecord.metric == AI_GENERATION_METRIC,
                        UsageRecord.period_key == period_key,
                    )
                )
                if int(used) >= limit:
                    raise UsageQuotaExceededError(
                        limit=limit,
                        used=int(used),
                        resets_at=_next_month(current_time),
                    )

                latest_sequence = session.scalar(
                    select(func.coalesce(func.max(UsageRecord.sequence), 0)).where(
                        UsageRecord.user_id == int(user_id),
                        UsageRecord.metric == AI_GENERATION_METRIC,
                        UsageRecord.period_key == period_key,
                    )
                )
                record = UsageRecord(
                    user_id=int(user_id),
                    metric=AI_GENERATION_METRIC,
                    quantity=1,
                    period_key=period_key,
                    sequence=int(latest_sequence) + 1,
                )
                session.add(record)
                session.flush()
                return UsageReservation(
                    id=record.id,
                    user_id=record.user_id,
                    period_key=record.period_key,
                )
        except IntegrityError:
            if attempt == MAX_RESERVATION_ATTEMPTS - 1:
                raise

    raise RuntimeError("The AI generation quota could not be reserved.")


def release_ai_generation(reservation):
    if reservation is None:
        return
    with get_db_session() as session:
        session.execute(
            delete(UsageRecord).where(
                UsageRecord.id == int(reservation.id),
                UsageRecord.user_id == int(reservation.user_id),
                UsageRecord.metric == AI_GENERATION_METRIC,
                UsageRecord.period_key == reservation.period_key,
            )
        )


def get_ai_generation_usage(user_id, now=None):
    current_time = _as_utc(now or datetime.now(timezone.utc))
    period_key = current_time.strftime("%Y-%m")
    with get_db_session() as session:
        used = session.scalar(
            select(func.coalesce(func.sum(UsageRecord.quantity), 0)).where(
                UsageRecord.user_id == int(user_id),
                UsageRecord.metric == AI_GENERATION_METRIC,
                UsageRecord.period_key == period_key,
            )
        )
    return int(used)


def get_ai_generation_quota(user_id, now=None):
    current_time = _as_utc(now or datetime.now(timezone.utc))
    used = get_ai_generation_usage(user_id, now=current_time)
    limit = _get_free_ai_generation_limit()
    return {
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "resets_at": _next_month(current_time),
    }


def _get_free_ai_generation_limit():
    configured = os.getenv(
        "FREE_MONTHLY_AI_GENERATIONS",
        str(DEFAULT_FREE_MONTHLY_AI_GENERATIONS),
    )
    try:
        limit = int(configured)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("FREE_MONTHLY_AI_GENERATIONS must be an integer.") from exc
    if limit < 1:
        raise RuntimeError("FREE_MONTHLY_AI_GENERATIONS must be at least 1.")
    return limit


def _next_month(value):
    if value.month == 12:
        return value.replace(year=value.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return value.replace(month=value.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def _as_utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
