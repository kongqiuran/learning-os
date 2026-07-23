from pathlib import Path
import shutil
from uuid import uuid4

from src.config import BASE_DIR, DERIVED_DIR, UPLOAD_DIR


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


def resolve_document_path(path):
    file_path = Path(path)
    return file_path if file_path.is_absolute() else (BASE_DIR / file_path).resolve()


def build_document_page_path(user_id, course_id, document_id, page_number):
    directory = (
        DERIVED_DIR
        / f"user_{int(user_id)}"
        / f"course_{int(course_id)}"
        / f"document_{int(document_id)}"
    )
    file_path = directory / f"page_{int(page_number):04d}.png"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def store_derived_path(file_path):
    path = Path(file_path).resolve()
    derived_root = DERIVED_DIR.resolve()
    if not path.is_relative_to(derived_root):
        raise ValueError("Derived file path is outside the derived directory.")
    try:
        return path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return path.as_posix()


def delete_document_derivatives(user_id, course_id, document_id):
    derived_root = DERIVED_DIR.resolve()
    directory = (
        derived_root
        / f"user_{int(user_id)}"
        / f"course_{int(course_id)}"
        / f"document_{int(document_id)}"
    ).resolve()
    if not directory.is_relative_to(derived_root):
        raise ValueError("Derived document path is outside the derived directory.")
    if not directory.exists():
        return
    for item in directory.iterdir():
        if item.is_file():
            item.unlink()
    directory.rmdir()


def delete_course_derivatives(user_id, course_id):
    return _delete_derived_tree(
        DERIVED_DIR
        / f"user_{int(user_id)}"
        / f"course_{int(course_id)}"
    )


def delete_user_derivatives(user_id):
    return _delete_derived_tree(DERIVED_DIR / f"user_{int(user_id)}")


def _delete_derived_tree(directory):
    derived_root = DERIVED_DIR.resolve()
    target = Path(directory).resolve()
    if not target.is_relative_to(derived_root) or target == derived_root:
        raise ValueError("Derived cleanup path is outside the derived directory.")
    if not target.exists():
        return 0
    file_count = sum(1 for path in target.rglob("*") if path.is_file())
    shutil.rmtree(target)
    return file_count
