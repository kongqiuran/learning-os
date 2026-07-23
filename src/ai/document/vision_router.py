from dataclasses import dataclass


@dataclass(frozen=True)
class VisionRoute:
    requires_vision: bool
    reason: str
    complexity: float


def route_page(page):
    features = page.features
    text_length = int(features.get("text_length", 0))
    image_count = int(features.get("image_count", 0))
    image_ratio = float(features.get("image_area_ratio", 0))
    drawing_count = int(features.get("drawing_count", 0))

    if page.page_type == "scanned":
        return VisionRoute(True, "page appears to be a scanned image", 0.98)
    if not text_length and (image_count or drawing_count):
        return VisionRoute(True, "page has visual content but no extracted text", 0.95)
    if image_ratio >= 0.35:
        return VisionRoute(True, "page contains a large embedded image", 0.9)
    if image_count >= 2 and image_ratio >= 0.12:
        return VisionRoute(True, "page contains multiple embedded images", 0.82)
    if image_count and text_length < 500:
        return VisionRoute(True, "page combines an image with limited text", 0.76)
    if drawing_count >= 20 and text_length < 800:
        return VisionRoute(True, "page contains a complex vector diagram", 0.72)
    return VisionRoute(False, "page is primarily extractable text", 0.15)
