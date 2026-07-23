from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VisionAnalysis:
    content: dict[str, Any]
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class VisionProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self):
        raise NotImplementedError

    @abstractmethod
    def is_available(self):
        raise NotImplementedError

    @abstractmethod
    def analyze_page(self, image_path: Path, page_text: str, metadata: dict):
        raise NotImplementedError
