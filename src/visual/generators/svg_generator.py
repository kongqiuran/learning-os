from html import escape

from src.visual.generators.base import BaseVisualGenerator


class SvgGenerator(BaseVisualGenerator):
    name = "svg"

    def generate(self, spec):
        nodes = (spec.get("nodes") or [])[:8]
        if not nodes:
            raise ValueError("SVG generation requires at least one node.")
        width = 760
        height = max(180, 80 + len(nodes) * 82)
        center_x = width // 2
        positions = {}
        pieces = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img">',
            f"<title>{escape(str(spec.get('title') or 'Knowledge diagram'))}</title>",
            '<rect width="100%" height="100%" fill="#f8fafc"/>',
        ]
        for index, node in enumerate(nodes):
            x = center_x - 260 if index % 2 else center_x + 40
            if index == 0:
                x = center_x - 110
            y = 24 if index == 0 else 40 + index * 72
            positions[str(node.get("id"))] = (x, y)
        for edge in (spec.get("edges") or [])[:12]:
            source = positions.get(str(edge.get("from")))
            target = positions.get(str(edge.get("to")))
            if source and target:
                pieces.append(
                    f'<line x1="{source[0] + 110}" y1="{source[1] + 25}" '
                    f'x2="{target[0] + 110}" y2="{target[1] + 25}" '
                    'stroke="#94a3b8" stroke-width="2"/>'
                )
        for node in nodes:
            x, y = positions[str(node.get("id"))]
            label = escape(str(node.get("label") or "")[:72])
            pieces.extend([
                f'<rect x="{x}" y="{y}" width="220" height="50" rx="12" '
                'fill="#ffffff" stroke="#6366f1" stroke-width="2"/>',
                f'<text x="{x + 110}" y="{y + 30}" text-anchor="middle" '
                'font-family="sans-serif" font-size="14" fill="#1e293b">'
                f"{label}</text>",
            ])
        pieces.append("</svg>")
        return "".join(pieces)
