from abc import ABC, abstractmethod


class BaseVisualGenerator(ABC):
    name: str

    @abstractmethod
    def generate(self, spec):
        raise NotImplementedError
