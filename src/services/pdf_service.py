from pathlib import Path

import fitz

from src.config import BASE_DIR


def extract_text(file_path):
    path = Path(file_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF documents are supported for analysis.")
    with fitz.open(path) as document:
        pages = [page.get_text("text").strip() for page in document]
    text = "\n\n".join(page for page in pages if page)
    if not text.strip():
        raise ValueError("No text was found in the PDF. OCR is not supported.")
    return text
