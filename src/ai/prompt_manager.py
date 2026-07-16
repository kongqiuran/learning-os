from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
SUPPORTED_PROMPTS = {
    "document_analyzer",
    "course_analyzer",
    "learning_package_generator",
}

STRUCTURED_OUTPUT_RULES = """

IMPORTANT OUTPUT FORMAT:

You MUST return ONLY valid JSON.

Rules:
- Do not use markdown code blocks
- Do not add explanations
- Do not add comments
- Use double quotes for every JSON key and string value
- Escape double quotes and control characters inside strings
- Do not include trailing commas
- Complete every object and array before ending the response
- JSON must be directly parseable by Python json.loads()
""".strip()


def get_prompt(prompt_name):
    if prompt_name not in SUPPORTED_PROMPTS:
        raise ValueError(f"Unsupported prompt: {prompt_name}")
    prompt = (PROMPT_DIR / f"{prompt_name}.txt").read_text(encoding="utf-8").strip()
    return f"{prompt}\n\n{STRUCTURED_OUTPUT_RULES}"
