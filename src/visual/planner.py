import re
from typing import Any

from src.visual.schemas import VisualPlan


PLANNER_VERSION = "rules-v1"
COMPLEXITY_THRESHOLD = 0.6
MAX_NODES = 8

FLOW_SIGNALS = ("步骤", "流程", "过程", "阶段", "首先", "然后", "最后", "step", "process")
RELATION_SIGNALS = ("关系", "影响", "依赖", "导致", "组成", "区别", "联系", "relation", "depend")
STRUCTURE_SIGNALS = ("分类", "结构", "层级", "包括", "分为", "类型", "组成", "体系")


class VisualPlanner:
    version = PLANNER_VERSION

    def plan(self, snapshot: dict[str, Any]) -> VisualPlan:
        title = _clean_text(snapshot.get("title")) or "Knowledge"
        importance = _integer(snapshot.get("importance"))
        points = _clean_points(snapshot.get("must_master"))
        body = " ".join(
            _clean_text(snapshot.get(key))
            for key in ("content", "core_explanation", "exam_value", "reason")
        )
        complexity = self.measure_complexity(snapshot)
        need_visual = importance >= 4 or complexity >= COMPLEXITY_THRESHOLD
        if not need_visual:
            return VisualPlan(
                need_visual=False,
                type=None,
                generator=None,
                reason="The knowledge structure is simple and does not require an automatic visual.",
                confidence=0.88,
                complexity=complexity,
            )

        if _contains_any(body, FLOW_SIGNALS):
            visual_type = "flowchart"
            reason = "The content contains an ordered process."
        elif len(points) >= 3 or _contains_any(body, STRUCTURE_SIGNALS):
            visual_type = "mindmap"
            reason = "The content contains multiple structured knowledge branches."
        else:
            visual_type = "diagram"
            reason = "The knowledge item is important or has connected concepts."

        nodes = [{"id": "n0", "label": title}]
        branch_labels = points or _sentence_points(body)
        if not branch_labels:
            branch_labels = [value for value in (
                _clean_text(snapshot.get("core_explanation")),
                _clean_text(snapshot.get("exam_value")),
                _clean_text(snapshot.get("memory_tips")),
            ) if value]
        for index, label in enumerate(branch_labels[: MAX_NODES - 1], start=1):
            nodes.append({"id": f"n{index}", "label": _truncate(label, 72)})

        edges = []
        if visual_type == "flowchart":
            for index in range(len(nodes) - 1):
                edges.append({"from": nodes[index]["id"], "to": nodes[index + 1]["id"]})
        else:
            for node in nodes[1:]:
                edges.append({"from": "n0", "to": node["id"]})

        generator = "mermaid" if visual_type in {"mindmap", "flowchart"} else "svg"
        confidence = min(0.98, 0.7 + complexity * 0.2 + (0.06 if importance >= 4 else 0))
        return VisualPlan(
            need_visual=True,
            type=visual_type,
            generator=generator,
            reason=reason,
            confidence=round(confidence, 2),
            complexity=complexity,
            spec={"title": title, "nodes": nodes, "edges": edges},
        )

    def measure_complexity(self, snapshot: dict[str, Any]) -> float:
        points = _clean_points(snapshot.get("must_master"))
        formulas = snapshot.get("source_formulas")
        body = " ".join(
            _clean_text(snapshot.get(key))
            for key in ("content", "core_explanation", "exam_value", "reason")
        )
        score = min(0.4, len(points) * 0.1)
        score += min(0.2, len(formulas) * 0.08) if isinstance(formulas, list) else 0
        score += min(0.2, len(body) / 1800)
        signal_groups = (
            _contains_any(body, FLOW_SIGNALS),
            _contains_any(body, RELATION_SIGNALS),
            _contains_any(body, STRUCTURE_SIGNALS),
        )
        score += sum(0.1 for found in signal_groups if found)
        return round(min(1.0, score), 2)


def _clean_points(value):
    if not isinstance(value, list):
        return []
    results = []
    for item in value:
        if isinstance(item, dict):
            text = _clean_text(item.get("name") or item.get("title") or item.get("content"))
        else:
            text = _clean_text(item)
        if text:
            results.append(text)
    return results


def _sentence_points(text):
    return [
        piece.strip()
        for piece in re.split(r"[。；;\n]+", text)
        if len(piece.strip()) >= 4
    ][: MAX_NODES - 1]


def _contains_any(text, words):
    folded = text.casefold()
    return any(word.casefold() in folded for word in words)


def _clean_text(value):
    return str(value or "").strip()


def _integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _truncate(value, length):
    text = _clean_text(value)
    return text if len(text) <= length else f"{text[: length - 1]}…"
