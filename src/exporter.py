from datetime import datetime

from src.config import OUTPUT_DIR


def build_output_filename(course_name):
    safe_name = course_name.strip().replace("/", "-").replace("\\", "-")
    date_text = datetime.now().strftime("%Y%m%d")
    return f"{safe_name}期末复习包_{date_text}.md"


def save_markdown(content, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(content, encoding="utf-8")
    return output_path

