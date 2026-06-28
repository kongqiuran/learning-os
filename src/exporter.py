from datetime import datetime

from src.config import OUTPUT_DIR


def build_output_filename(course_name):
    safe_name = sanitize_filename(course_name.strip() or "course")
    date_text = datetime.now().strftime("%Y%m%d")
    return f"{safe_name}_review_pack_{date_text}.md"


def save_markdown(content, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_filename = sanitize_filename(filename)
    if not safe_filename.endswith(".md"):
        safe_filename = f"{safe_filename}.md"

    output_path = OUTPUT_DIR / safe_filename
    output_path.write_text(content, encoding="utf-8")
    return output_path


def sanitize_filename(filename):
    cleaned = filename.strip().replace("/", "-").replace("\\", "-")
    return cleaned or "review_pack.md"
