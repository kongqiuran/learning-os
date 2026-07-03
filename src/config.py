import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
ENV_FILE = BASE_DIR / ".env"


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
