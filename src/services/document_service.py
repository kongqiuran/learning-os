from pathlib import Path

from sqlalchemy import delete, select

from src.config import get_max_upload_size
from src.database import get_db_session
from src.models import Course, Document
from src.storage import delete_document_file, save_document_bytes


ALLOWED_FILE_TYPES = {
    ".pdf": {"application/pdf"},
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    ".md": {"text/markdown", "text/plain", "text/x-markdown"},
}


class DocumentUploadError(ValueError):
    pass


def save_uploaded_document(user_id, course_id, uploaded_file):
    if user_id is None or course_id is None:
        raise DocumentUploadError("A user and course are required.")
    if not _course_belongs_to_user(course_id, user_id):
        raise DocumentUploadError("The course does not exist or access is denied.")

    original_filename = Path(getattr(uploaded_file, "name", "")).name
    extension = Path(original_filename).suffix.lower()
    mime_type = (getattr(uploaded_file, "type", "") or "").lower().strip()
    _validate_file_type(extension, mime_type)

    data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    file_size = len(data)
    if file_size == 0:
        raise DocumentUploadError("The uploaded file is empty.")
    if file_size > get_max_upload_size():
        raise DocumentUploadError("The uploaded file exceeds the size limit.")

    _validate_file_signature(extension, data)
    file_path, stored_filename = save_document_bytes(user_id, course_id, extension, data)
    document = Document(
        user_id=int(user_id),
        course_id=int(course_id),
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        mime_type=mime_type,
        file_size=file_size,
        processing_status="uploaded",
    )

    try:
        with get_db_session() as session:
            session.add(document)
            session.flush()
    except Exception:
        delete_document_file(file_path)
        raise

    return document


def list_documents_for_course(user_id, course_id):
    if user_id is None or course_id is None:
        return []

    with get_db_session() as session:
        statement = (
            select(Document)
            .where(
                Document.user_id == int(user_id),
                Document.course_id == int(course_id),
            )
            .order_by(Document.uploaded_at.desc(), Document.id.desc())
        )
        return list(session.scalars(statement))


def delete_document_for_user(document_id, user_id, course_id):
    if document_id is None or user_id is None or course_id is None:
        return False

    with get_db_session() as session:
        document = session.scalar(
            select(Document).where(
                Document.id == int(document_id),
                Document.user_id == int(user_id),
                Document.course_id == int(course_id),
            )
        )
        if document is None:
            return False
        file_path = document.file_path
        session.execute(
            delete(Document).where(
                Document.id == int(document_id),
                Document.user_id == int(user_id),
                Document.course_id == int(course_id),
            )
        )

    delete_document_file(file_path)
    return True


def _course_belongs_to_user(course_id, user_id):
    with get_db_session() as session:
        statement = select(Course.id).where(
            Course.id == int(course_id),
            Course.user_id == int(user_id),
        )
        return session.scalar(statement) is not None


def _validate_file_type(extension, mime_type):
    if extension not in ALLOWED_FILE_TYPES:
        raise DocumentUploadError("Supported file types are PDF, PPTX, DOCX, and Markdown.")
    if mime_type not in ALLOWED_FILE_TYPES[extension]:
        raise DocumentUploadError("The file MIME type does not match the selected format.")


def _validate_file_signature(extension, data):
    if extension == ".pdf" and not data.startswith(b"%PDF-"):
        raise DocumentUploadError("The file does not contain a valid PDF signature.")
    if extension in {".pptx", ".docx"} and not data.startswith(b"PK"):
        raise DocumentUploadError("The Office file does not contain a valid ZIP signature.")
