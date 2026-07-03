from openai import OpenAI

from src.chunker import combine_documents
from src.config import ENV_FILE, get_llm_config, get_max_chars_per_request
from src.prompts import REVIEW_PACK_SYSTEM_PROMPT, REVIEW_PACK_USER_PROMPT


PLACEHOLDER_KEYS = {"", "your_api_key_here", "your_deepseek_api_key_here"}


def generate_review_pack(course_name, documents):
    llm_config = get_llm_config()
    if llm_config.api_key in PLACEHOLDER_KEYS:
        return build_missing_api_key_message(course_name, documents)

    content = combine_documents(
        documents,
        max_chars=get_max_chars_per_request(),
    )
    if not content:
        raise ValueError("No course text is available for generation.")

    prompt = REVIEW_PACK_USER_PROMPT.format(
        course_name=course_name,
        content=content,
    )

    client = OpenAI(api_key=llm_config.api_key, base_url=llm_config.base_url)
    response = client.chat.completions.create(
        model=llm_config.model,
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

程序正在读取这个配置文件：

```text
{ENV_FILE}
```

请确认这个文件存在，并且里面的 `LLM_API_KEY` 已经换成你自己的 Key：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-flash
```

如果你刚刚修改过 `.env`，请关闭 `start.bat` 窗口后重新启动。

已读取到的资料：

{filenames}
"""
