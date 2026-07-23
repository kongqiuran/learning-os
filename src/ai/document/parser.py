import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz


@dataclass(frozen=True)
class ParsedPdfPage:
    page_number: int
    text_content: str
    page_type: str
    content_hash: str
    features: dict[str, Any]


def parse_pdf_pages(file_path):
    path = Path(file_path)
    source_hash = _file_sha256(path)
    pages = []
    with fitz.open(path) as pdf:
        for index, page in enumerate(pdf):
            text = page.get_text("text").strip()
            image_count, image_area_ratio = _image_features(page)
            drawing_count = len(page.get_drawings())
            text_length = len(text)
            page_type = _classify_page(
                text_length=text_length,
                image_count=image_count,
                image_area_ratio=image_area_ratio,
                drawing_count=drawing_count,
            )
            pages.append(
                ParsedPdfPage(
                    page_number=index + 1,
                    text_content=text,
                    page_type=page_type,
                    content_hash=hashlib.sha256(
                        f"{source_hash}:{index + 1}".encode("utf-8")
                    ).hexdigest(),
                    features={
                        "text_length": text_length,
                        "image_count": image_count,
                        "image_area_ratio": round(image_area_ratio, 4),
                        "drawing_count": drawing_count,
                        "width": round(float(page.rect.width), 2),
                        "height": round(float(page.rect.height), 2),
                    },
                )
            )
    return pages


def render_pdf_page(file_path, page_number, output_path, dpi=144):
    path = Path(file_path)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(path) as pdf:
        page = pdf.load_page(int(page_number) - 1)
        pixmap = page.get_pixmap(dpi=int(dpi), alpha=False)
        pixmap.save(target)
    return target


def _image_features(page):
    page_area = max(float(page.rect.get_area()), 1.0)
    covered_area = 0.0
    image_count = 0
    seen_rects = set()
    for image in page.get_images(full=True):
        xref = image[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        for rect in rects:
            key = tuple(round(float(value), 2) for value in rect)
            if key in seen_rects:
                continue
            seen_rects.add(key)
            image_count += 1
            covered_area += max(float(rect.get_area()), 0.0)
    return image_count, min(covered_area / page_area, 1.0)


def _classify_page(text_length, image_count, image_area_ratio, drawing_count):
    has_visual = image_count > 0 or drawing_count >= 8
    if text_length < 40 and image_area_ratio >= 0.65:
        return "scanned"
    if has_visual and text_length > 0:
        return "mixed"
    if has_visual:
        return "image"
    return "text"


def _file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
