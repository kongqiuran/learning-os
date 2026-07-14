import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
UPLOAD_DIR = DATA_DIR / "uploads"
ENV_FILE = BASE_DIR / ".env"
DEFAULT_DATABASE_PATH = DATA_DIR / "database" / "learning_os.db"


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str


def get_llm_config():
    load_dotenv(ENV_FILE, override=True)
    return LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "deepseek").strip(),
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip(),
        model=os.getenv("LLM_MODEL", "deepseek-v4-flash").strip(),
    )


def get_max_chars_per_request():
    load_dotenv(ENV_FILE, override=True)
    try:
        return int(os.getenv("MAX_CHARS_PER_REQUEST", "60000"))
    except ValueError:
        return 60000


def get_database_url():
    load_dotenv(ENV_FILE, override=True)
    configured_url = os.getenv("DATABASE_URL", "").strip()
    if not configured_url:
        return f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

    sqlite_prefix = "sqlite:///"
    if not configured_url.startswith(sqlite_prefix):
        return configured_url

    database_path = configured_url.removeprefix(sqlite_prefix)
    if database_path == ":memory:" or Path(database_path).is_absolute():
        return configured_url

    return f"sqlite:///{(BASE_DIR / database_path).resolve().as_posix()}"


def get_max_upload_size():
    load_dotenv(ENV_FILE, override=True)
    try:
        size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    except ValueError:
        size_mb = 50
    return max(1, size_mb) * 1024 * 1024
