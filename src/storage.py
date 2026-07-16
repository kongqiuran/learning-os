from pathlib import Path
from uuid import uuid4

from src.config import BASE_DIR, UPLOAD_DIR


def build_document_path(user_id, course_id, extension):
    safe_extension = extension.lower()
    stored_filename = f"{uuid4().hex}{safe_extension}"
    directory = UPLOAD_DIR / f"user_{int(user_id)}" / f"course_{int(course_id)}"
    return directory / stored_filename, stored_filename


def save_document_bytes(user_id, course_id, extension, data):
    file_path, stored_filename = build_document_path(user_id, course_id, extension)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(data)
    try:
        stored_path = file_path.relative_to(BASE_DIR)
    except ValueError:
        stored_path = file_path.resolve()
    return stored_path.as_posix(), stored_filename


def delete_document_file(relative_path):
    uploads_root = UPLOAD_DIR.resolve()
    file_path = (BASE_DIR / relative_path).resolve()
    if not file_path.is_relative_to(uploads_root):
        raise ValueError("Document path is outside the upload directory.")
    if file_path.exists():
        file_path.unlink()
