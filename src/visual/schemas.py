from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class VisualPlan:
    need_visual: bool
    type: str | None
    generator: str | None
    reason: str
    confidence: float
    complexity: float
    spec: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
