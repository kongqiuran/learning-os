# 文件说明：上传文件适配器。BytesIO 来自 Python 标准库 io，用内存字节模拟文件对象；Path 来自 pathlib，用来按后缀补 MIME 类型。
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
    # 这个类继承 BytesIO，意思是“这个对象本身就是一段可读的内存字节流”。
    # document_service 既可能接收 Streamlit 文件，也可能接收 FastAPI 文件；适配器让两边都暴露 name/type/getvalue 这些同名接口。

    def __init__(self, filename, content_type, data):
        # super().__init__(data) 调用 BytesIO 的初始化逻辑，把上传字节 data 放进内存文件。
        super().__init__(data)
        self.name = filename
        self.type = _normalize_content_type(filename, content_type)

    def getvalue(self):
        return super().getvalue()


def _normalize_content_type(filename, content_type):
    # 有些浏览器或代理会把未知文件标成 application/octet-stream。
    # octet-stream 是通用二进制类型；这里根据扩展名兜底推断真实 MIME，避免合法文件被误拒。
    normalized = (content_type or "").lower().strip()
    if normalized and normalized != "application/octet-stream":
        return normalized
    return FALLBACK_CONTENT_TYPES.get(Path(filename).suffix.lower(), "application/octet-stream")
