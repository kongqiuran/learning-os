from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_database_url
from src.database.base import Base


def _ensure_sqlite_directory(database_url):
    prefix = "sqlite:///"
    if not database_url.startswith(prefix) or database_url == "sqlite:///:memory:":
        return

    database_path = Path(database_url.removeprefix(prefix))
    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)


DATABASE_URL = get_database_url()
_ensure_sqlite_directory(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_database_tables():
    import src.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _upgrade_sqlite_document_columns()


def _upgrade_sqlite_document_columns():
    if not DATABASE_URL.startswith("sqlite"):
        return

    existing_columns = {column["name"] for column in inspect(engine).get_columns("documents")}
    required_columns = {
        "stored_filename": "VARCHAR(255) NOT NULL DEFAULT ''",
        "mime_type": "VARCHAR(255) NOT NULL DEFAULT 'application/octet-stream'",
        "file_size": "INTEGER NOT NULL DEFAULT 0",
        "document_type": "VARCHAR(20) NOT NULL DEFAULT 'OTHER'",
    }

    with engine.begin() as connection:
        for column_name, column_definition in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE documents ADD COLUMN {column_name} {column_definition}")
                )


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
