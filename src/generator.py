from openai import OpenAI

from src.chunker import combine_documents
from src.config import MAX_CHARS_PER_REQUEST, MODEL_NAME, OPENAI_API_KEY
from src.prompts import REVIEW_PACK_SYSTEM_PROMPT, REVIEW_PACK_USER_PROMPT


def generate_review_pack(course_name, documents):
    if not OPENAI_API_KEY:
        return build_missing_api_key_message(course_name, documents)

    content = combine_documents(documents, max_chars=MAX_CHARS_PER_REQUEST)
    prompt = REVIEW_PACK_USER_PROMPT.format(course_name=course_name, content=content)

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": REVIEW_PACK_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def build_missing_api_key_message(course_name, documents):
    filenames = "\n".join(f"- {document['filename']}" for document in documents)
    return f"""# 《{course_name}》期末复习包

当前还没有配置 OpenAI API Key，所以没有真正调用 AI。

请复制 `.env.example` 为 `.env`，填入：

```env
OPENAI_API_KEY=你的 API Key
MODEL_NAME=gpt-4o-mini
```

然后重新运行：

```bash
streamlit run app.py
```

已读取到的资料：

{filenames}
"""

