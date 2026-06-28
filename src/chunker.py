def chunk_text(text, max_chars=12000, overlap=500):
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def combine_documents(documents, max_chars):
    parts = []
    used_chars = 0

    for document in documents:
        filename = document["filename"]
        text = document["text"]
        block = f"\n\n# 来源文件：{filename}\n\n{text}"

        remaining = max_chars - used_chars
        if remaining <= 0:
            break

        if len(block) > remaining:
            block = block[:remaining]

        parts.append(block)
        used_chars += len(block)

    return "\n".join(parts).strip()

