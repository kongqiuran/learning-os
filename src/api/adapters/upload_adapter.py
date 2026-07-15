from io import BytesIO
from pathlib import Path


FALLBACK_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class ServiceUploadFile(BytesIO):
    """Expose FastAPI upload bytes through the interface used by the existing service."""

    def __init__(self, filename, content_type, data):
        super().__init__(data)
        self.name = filename
        self.type = _normalize_content_type(filename, content_type)

    def getvalue(self):
        return super().getvalue()


def _normalize_content_type(filename, content_type):
    normalized = (content_type or "").lower().strip()
    if normalized and normalized != "application/octet-stream":
        return normalized
    return FALLBACK_CONTENT_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream")
