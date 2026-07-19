import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=False)


def _resolve_data_dir():
    configured_path = os.getenv("LEARNING_OS_DATA_DIR", "").strip()
    if not configured_path:
        return BASE_DIR / "data"
    path = Path(configured_path)
    return path if path.is_absolute() else (BASE_DIR / path).resolve()


DATA_DIR = _resolve_data_dir()
OUTPUT_DIR = DATA_DIR / "outputs"
UPLOAD_DIR = DATA_DIR / "uploads"
DEFAULT_DATABASE_PATH = DATA_DIR / "database" / "learning_os.db"
DEFAULT_PRIVACY_POLICY_VERSION = "2026.07.01-v1"
CURRENT_PRIVACY_POLICY_VERSION = (
    os.getenv("PRIVACY_POLICY_VERSION", DEFAULT_PRIVACY_POLICY_VERSION).strip()
    or DEFAULT_PRIVACY_POLICY_VERSION
)


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float
    max_attempts: int


def get_llm_config():
    load_dotenv(ENV_FILE, override=False)
    return LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "deepseek").strip(),
        api_key=os.getenv("LLM_API_KEY", "").strip(),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com").strip(),
        model=os.getenv("LLM_MODEL", "deepseek-v4-flash").strip(),
        timeout_seconds=_get_float_setting("LLM_TIMEOUT_SECONDS", 120.0, 30.0, 300.0),
        max_attempts=_get_int_setting("LLM_MAX_ATTEMPTS", 3, 1, 4),
    )


def _get_float_setting(name, default, minimum, maximum):
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def _get_int_setting(name, default, minimum, maximum):
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def get_max_chars_per_request():
    load_dotenv(ENV_FILE, override=False)
    try:
        return int(os.getenv("MAX_CHARS_PER_REQUEST", "60000"))
    except ValueError:
        return 60000


def get_assistant_max_context_chars():
    load_dotenv(ENV_FILE, override=False)
    try:
        configured_limit = int(os.getenv("ASSISTANT_MAX_CONTEXT_CHARS", "16000"))
    except ValueError:
        configured_limit = 16000
    return max(4000, min(configured_limit, 30000))


def get_database_url():
    load_dotenv(ENV_FILE, override=False)
    configured_url = os.getenv("DATABASE_URL", "").strip()
    if not configured_url:
        database_url = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
        _ensure_safe_test_database(database_url)
        return database_url

    sqlite_prefix = "sqlite:///"
    if not configured_url.startswith(sqlite_prefix):
        _ensure_safe_test_database(configured_url)
        return configured_url

    database_path = configured_url.removeprefix(sqlite_prefix)
    if database_path == ":memory:" or Path(database_path).is_absolute():
        _ensure_safe_test_database(configured_url)
        return configured_url

    database_url = f"sqlite:///{(BASE_DIR / database_path).resolve().as_posix()}"
    _ensure_safe_test_database(database_url)
    return database_url


def get_max_upload_size():
    load_dotenv(ENV_FILE, override=False)
    try:
        size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    except ValueError:
        size_mb = 50
    return max(1, size_mb) * 1024 * 1024


def _ensure_safe_test_database(database_url):
    if os.getenv("LEARNING_OS_TESTING", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    if not database_url.startswith("sqlite:///") or database_url == "sqlite:///:memory:":
        return
    configured_path = Path(database_url.removeprefix("sqlite:///"))
    resolved_path = configured_path if configured_path.is_absolute() else (BASE_DIR / configured_path).resolve()
    production_path = (BASE_DIR / "data" / "database" / "learning_os.db").resolve()
    if resolved_path.resolve() == production_path:
        raise RuntimeError("Tests cannot use the production Learning OS database.")
