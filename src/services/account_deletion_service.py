import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select

from src.auth.password import verify_password
from src.config import BASE_DIR, UPLOAD_DIR
from src.database import get_db_session
from src.models import Document, User
from src.storage import delete_document_file


logger = logging.getLogger(__name__)
ACCOUNT_DELETION_CONFIRMATION = "DELETE MY ACCOUNT"


class AccountDeletionError(ValueError):
    pass


class AccountDeletionAuthenticationError(AccountDeletionError):
    pass


class AccountDeletionConfirmationError(AccountDeletionError):
    pass


@dataclass(frozen=True)
class AccountDeletionResult:
    deletion_id: str
    deleted_file_count: int
    file_cleanup_error_count: int


class AccountDeletionService:
    def delete_current_user(self, user_id, password, confirmation):
        if user_id is None:
            raise AccountDeletionAuthenticationError("Authentication is required.")
        if confirmation != ACCOUNT_DELETION_CONFIRMATION:
            raise AccountDeletionConfirmationError(
                f'Enter "{ACCOUNT_DELETION_CONFIRMATION}" to confirm account deletion.'
            )

        deletion_id = uuid4().hex
        quarantine_path = None
        file_paths = []

        try:
            with get_db_session() as session:
                user = session.scalar(select(User).where(User.id == int(user_id)))
                if user is None or not verify_password(password, user.password_hash):
                    raise AccountDeletionAuthenticationError(
                        "The password is incorrect or the account no longer exists."
                    )

                file_paths = list(
                    session.scalars(
                        select(Document.file_path).where(Document.user_id == int(user_id))
                    )
                )
                quarantine_path = self._quarantine_user_files(user_id, deletion_id)
                self._delete_user_records(session, user_id)
        except Exception:
            if quarantine_path is not None:
                self._restore_quarantined_files(user_id, quarantine_path, deletion_id)
            raise

        deleted_file_count, cleanup_errors = self._purge_user_files(
            user_id,
            deletion_id,
            quarantine_path,
            file_paths,
        )
        return AccountDeletionResult(
            deletion_id=deletion_id,
            deleted_file_count=deleted_file_count,
            file_cleanup_error_count=cleanup_errors,
        )

    @staticmethod
    def _delete_user_records(session, user_id):
        result = session.execute(delete(User).where(User.id == int(user_id)))
        if result.rowcount != 1:
            raise AccountDeletionError("The account could not be deleted.")

    @staticmethod
    def _quarantine_user_files(user_id, deletion_id):
        uploads_root = UPLOAD_DIR.resolve()
        user_directory = (UPLOAD_DIR / f"user_{int(user_id)}").resolve()
        if not user_directory.is_relative_to(uploads_root):
            raise AccountDeletionError("The user upload directory is invalid.")
        if not user_directory.exists():
            return None

        quarantine_root = (UPLOAD_DIR / ".deleting").resolve()
        quarantine_root.mkdir(parents=True, exist_ok=True)
        quarantine_path = (quarantine_root / deletion_id).resolve()
        if not quarantine_path.is_relative_to(quarantine_root):
            raise AccountDeletionError("The deletion quarantine path is invalid.")
        user_directory.replace(quarantine_path)
        return quarantine_path

    @staticmethod
    def _restore_quarantined_files(user_id, quarantine_path, deletion_id):
        user_directory = (UPLOAD_DIR / f"user_{int(user_id)}").resolve()
        try:
            if quarantine_path.exists() and not user_directory.exists():
                user_directory.parent.mkdir(parents=True, exist_ok=True)
                quarantine_path.replace(user_directory)
        except OSError:
            logger.exception(
                "Failed to restore quarantined account files.",
                extra={"deletion_id": deletion_id, "user_id": int(user_id)},
            )

    def _purge_user_files(
        self,
        user_id,
        deletion_id,
        quarantine_path,
        file_paths,
    ):
        deleted_file_count = 0
        cleanup_errors = 0
        user_directory = (UPLOAD_DIR / f"user_{int(user_id)}").resolve()

        if quarantine_path is not None:
            try:
                deleted_file_count += sum(1 for path in quarantine_path.rglob("*") if path.is_file())
                shutil.rmtree(quarantine_path)
            except OSError:
                cleanup_errors += 1
                logger.exception(
                    "Failed to purge quarantined account files.",
                    extra={"deletion_id": deletion_id, "user_id": int(user_id)},
                )

        for file_path in file_paths:
            resolved_path = self._resolve_document_path(file_path)
            if resolved_path.is_relative_to(user_directory):
                continue
            try:
                existed = resolved_path.exists()
                delete_document_file(file_path)
                if existed:
                    deleted_file_count += 1
            except (OSError, ValueError):
                cleanup_errors += 1
                logger.exception(
                    "Failed to delete an account document file.",
                    extra={"deletion_id": deletion_id, "user_id": int(user_id)},
                )

        return deleted_file_count, cleanup_errors

    @staticmethod
    def _resolve_document_path(file_path):
        path = Path(file_path)
        return path.resolve() if path.is_absolute() else (BASE_DIR / path).resolve()
