from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SUPPORTED_PROMPTS = {
    "document_analyzer",
    "course_analyzer",
    "learning_package_generator",
}


def get_prompt(prompt_name):
    if prompt_name not in SUPPORTED_PROMPTS:
        raise ValueError(f"Unsupported prompt: {prompt_name}")
    return (PROMPT_DIR / f"{prompt_name}.txt").read_text(encoding="utf-8").strip()
