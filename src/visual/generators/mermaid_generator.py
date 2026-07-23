import re

from src.visual.generators.base import BaseVisualGenerator


class MermaidGenerator(BaseVisualGenerator):
    name = "mermaid"

    def generate(self, spec):
        nodes = spec.get("nodes") or []
        edges = spec.get("edges") or []
        lines = ["flowchart TD"]
        known_ids = set()
        for node in nodes[:8]:
            node_id = _safe_id(node.get("id"))
            known_ids.add(node_id)
            lines.append(f'    {node_id}["{_safe_label(node.get("label"))}"]')
        for edge in edges[:12]:
            source = _safe_id(edge.get("from"))
            target = _safe_id(edge.get("to"))
            if source in known_ids and target in known_ids:
                lines.append(f"    {source} --> {target}")
        return "\n".join(lines)


def _safe_id(value):
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", str(value or "node"))
    return normalized if normalized[0].isalpha() else f"n_{normalized}"


def _safe_label(value):
    return (
        str(value or "")
        .replace("\\", "\\\\")
        .replace('"', "'")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("<", "＜")
        .replace(">", "＞")
    )[:100]
