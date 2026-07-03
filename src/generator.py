from openai import OpenAI

from src.chunker import combine_documents
from src.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAX_CHARS_PER_REQUEST
from src.prompts import REVIEW_PACK_SYSTEM_PROMPT, REVIEW_PACK_USER_PROMPT


def generate_review_pack(course_name, documents):
    if not LLM_API_KEY:
        return build_missing_api_key_message(course_name, documents)

    content = combine_documents(documents, max_chars=MAX_CHARS_PER_REQUEST)
    if not content:
        raise ValueError("No course text is available for generation.")

    prompt = REVIEW_PACK_USER_PROMPT.format(
        course_name=course_name,
        content=content,
    )

    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    response = client.chat.completions.create(
        model=LLM_MODEL,
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

还没有配置模型 API Key，请先查看 README 的配置教程。

你已经成功上传并读取了资料，下一步只需要配置 `.env` 文件：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

已读取到的资料：

{filenames}
"""
