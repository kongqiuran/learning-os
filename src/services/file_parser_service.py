from pathlib import Path

import fitz
from pptx import Presentation

from src.config import BASE_DIR


SUPPORTED_MIME_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PPTX",
    "text/plain": "TXT",
    "text/markdown": "MD",
    "text/x-markdown": "MD",
}


def extract_text(file_path, mime_type):
    path = Path(file_path)
    if not path.is_absolute():
        path = BASE_DIR / path

    source_type = get_source_type(path, mime_type)
    if source_type == "PDF":
        text = _extract_pdf(path)
    elif source_type == "PPTX":
        text = _extract_pptx(path)
    else:
        text = path.read_text(encoding="utf-8-sig")

    if not text.strip():
        raise ValueError(f"No text was found in the {source_type} file. OCR is not supported.")
    return text


def get_source_type(file_path, mime_type):
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".md":
        return "MD"
    if suffix == ".txt":
        return "TXT"
    source_type = SUPPORTED_MIME_TYPES.get((mime_type or "").lower().strip())
    if source_type is None:
        raise ValueError("Supported file types are PDF, PPTX, TXT, and MD.")
    return source_type


def _extract_pdf(path):
    with fitz.open(path) as document:
        pages = [page.get_text("text").strip() for page in document]
    return "\n\n".join(page for page in pages if page)


def _extract_pptx(path):
    presentation = Presentation(path)
    slides = []
    for slide in presentation.slides:
        parts = [shape.text.strip() for shape in slide.shapes if hasattr(shape, "text") and shape.text.strip()]
        if parts:
            slides.append("\n".join(parts))
    return "\n\n".join(slides)
