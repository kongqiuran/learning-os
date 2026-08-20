# 文件说明：资料上传、列表和删除服务。
# Path 来自 Python 标准库 pathlib，用来安全处理文件名/扩展名；select/delete 来自 SQLAlchemy，用来查询和删除数据库记录。
from pathlib import Path

from sqlalchemy import delete, select

from src.config import get_max_upload_size
from src.database import get_db_session
from src.models import Course, Document
from src.storage import (
    delete_document_derivatives,
    delete_document_file,
    save_document_bytes,
)
from src.logging_config import get_logger


# ALLOWED_FILE_TYPES 是上传白名单。
# key 是文件扩展名，value 是允许的 MIME 类型；MIME 是浏览器/系统告诉后端的文件媒体类型。
ALLOWED_FILE_TYPES = {
    ".pdf": {"application/pdf"},
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain", "text/x-markdown"},
}
DOCUMENT_TYPES = {"TEXTBOOK", "SLIDES", "EXAM", "HOMEWORK", "NOTES", "OTHER"}
logger = get_logger(__name__)


class DocumentUploadError(ValueError):
    pass


def save_uploaded_document(user_id, course_id, uploaded_file, document_type="OTHER"):
    # 上传阶段只做四件事：校验课程归属、校验文件、保存原文件、写 Document 记录。
    # 根据文档链路，DocumentAnalysis 不会在这里创建，AI 解析要等用户点击“整理”后由 Worker 执行。
    if user_id is None or course_id is None:
        raise DocumentUploadError("A user and course are required.")
    if not _course_belongs_to_user(course_id, user_id):
        raise DocumentUploadError("The course does not exist or access is denied.")

    original_filename = Path(getattr(uploaded_file, "name", "")).name
    extension = Path(original_filename).suffix.lower()
    mime_type = (getattr(uploaded_file, "type", "") or "").lower().strip()
    try:
        _validate_file_type(extension, mime_type)
        normalized_document_type = str(document_type).upper().strip()
        if normalized_document_type not in DOCUMENT_TYPES:
            raise DocumentUploadError("Invalid document type.")

        data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        file_size = len(data)
        if file_size == 0:
            raise DocumentUploadError("The uploaded file is empty.")
        if file_size > get_max_upload_size():
            raise DocumentUploadError("The uploaded file exceeds the size limit.")

        _validate_file_signature(extension, data)
        file_path, stored_filename = save_document_bytes(user_id, course_id, extension, data)
        # Document 是数据库模型，记录文件元数据和 processing_status。
        # processing_status="uploaded" 表示文件已入库但尚未解析。
        document = Document(
            user_id=int(user_id),
            course_id=int(course_id),
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            mime_type=mime_type,
            file_size=file_size,
            processing_status="uploaded",
            document_type=normalized_document_type,
        )
        with get_db_session() as session:
            session.add(document)
            session.flush()
    except Exception as exc:
        if "file_path" in locals():
            delete_document_file(file_path)
        logger.error(
            "Document upload failed.",
            extra={
                "event": "document.upload.failed",
                "user_id": user_id,
                "task_id": None,
                "document_id": None,
                "course_id": course_id,
                "exception": exc,
            },
        )
        raise

    logger.info(
        "Document upload completed.",
        extra={
            "event": "document.upload.success",
            "user_id": user_id,
            "document_id": document.id,
            "course_id": course_id,
        },
    )

    return document


def list_documents_for_course(user_id, course_id):
    if user_id is None or course_id is None:
        return []

    with get_db_session() as session:
        statement = (
            select(Document)
            .join(Course, Document.course_id == Course.id)
            .where(
                Document.user_id == int(user_id),
                Document.course_id == int(course_id),
                Course.user_id == int(user_id),
            )
            .order_by(Document.uploaded_at.desc(), Document.id.desc())
        )
        return list(session.scalars(statement))


def delete_document_for_user(document_id, user_id, course_id):
    # 删除资料时先删数据库记录，再删原文件和派生文件。
    # DocumentAnalysis 与 Document 有级联关系时，知识点也会随分析记录消失，因为知识点没有独立表。
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
        document_owner = document.user_id
        document_course = document.course_id
        stored_document_id = document.id
        session.execute(
            delete(Document).where(
                Document.id == int(document_id),
                Document.user_id == int(user_id),
                Document.course_id == int(course_id),
            )
        )

    delete_document_file(file_path)
    delete_document_derivatives(
        document_owner,
        document_course,
        stored_document_id,
    )
    return True


def _course_belongs_to_user(course_id, user_id):
    with get_db_session() as session:
        statement = select(Course.id).where(
            Course.id == int(course_id),
            Course.user_id == int(user_id),
        )
        return session.scalar(statement) is not None


def _validate_file_type(extension, mime_type):
    # 第一层校验：扩展名 + MIME 类型。
    # 这能挡住大多数错误上传；后面 _validate_file_signature 还会看文件头，避免只改后缀绕过。
    if extension not in ALLOWED_FILE_TYPES:
        raise DocumentUploadError("Supported file types are PDF, PPTX, TXT, and MD.")
    if mime_type not in ALLOWED_FILE_TYPES[extension]:
        raise DocumentUploadError("The file MIME type does not match the selected format.")


def _validate_file_signature(extension, data):
    # 第二层校验：文件头签名。
    # b"%PDF-" 和 b"PK" 是 bytes 字节串写法，来自 Python 语言本身；PDF 文件通常以 %PDF- 开头，PPTX 本质是 ZIP 包所以以 PK 开头。
    if extension == ".pdf" and not data.startswith(b"%PDF-"):
        raise DocumentUploadError("The file does not contain a valid PDF signature.")
    if extension == ".pptx" and not data.startswith(b"PK"):
        raise DocumentUploadError("The Office file does not contain a valid ZIP signature.")
