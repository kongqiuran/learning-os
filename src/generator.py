from openai import OpenAI

from src.chunker import combine_documents
from src.config import MAX_CHARS_PER_REQUEST, MODEL_NAME, OPENAI_API_KEY
from src.prompts import REVIEW_PACK_SYSTEM_PROMPT, REVIEW_PACK_USER_PROMPT


def generate_review_pack(course_name, documents):
    if not OPENAI_API_KEY:
        return build_missing_api_key_message(course_name, documents)

    content = combine_documents(documents, max_chars=MAX_CHARS_PER_REQUEST)
    if not content:
        raise ValueError("No course text is available for generation.")

    prompt = REVIEW_PACK_USER_PROMPT.format(
        course_name=course_name,
        content=content,
    )

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": REVIEW_PACK_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    result = response.choices[0].message.content or ""
    return result.strip()


def build_missing_api_key_message(course_name, documents):
    filenames = "\n".join(f"- {document['filename']}" for document in documents)

    return f"""# {course_name} review pack

OpenAI API key is not configured yet, so the app did not call the model.

Create a `.env` file from `.env.example`, then fill in:

```env
OPENAI_API_KEY=your_api_key_here
MODEL_NAME=gpt-4o-mini
```

Then restart the app:

```bash
streamlit run app.py
```

Files already read:

{filenames}
"""
