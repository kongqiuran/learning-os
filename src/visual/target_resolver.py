from dataclasses import asdict
from datetime import datetime
from typing import Any


SUPPORTED_TARGET_TYPE = "knowledge_item"


class VisualTargetNotFoundError(LookupError):
    pass


def resolve_target(target_type, target_id, user_id):
    if target_type != SUPPORTED_TARGET_TYPE:
        raise VisualTargetNotFoundError("The visual target was not found.")

    # Local import keeps the existing knowledge API independent from Visual.
    from src.api.adapters.knowledge_adapter import get_knowledge_item

    item = get_knowledge_item(target_id, user_id)
    if item is None:
        raise VisualTargetNotFoundError("The visual target was not found.")
    snapshot = _json_value(asdict(item))
    # Reading a knowledge item is user state, not a content revision. Keeping
    # it out of the snapshot avoids generating a new visual after "viewed".
    snapshot.pop("viewed", None)
    snapshot.pop("viewed_at", None)
    return item, snapshot


def _json_value(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value
