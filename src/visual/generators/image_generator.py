from src.visual.generators.base import BaseVisualGenerator


class ImageGenerator(BaseVisualGenerator):
    """Reserved provider-neutral interface for a future image model."""

    name = "image"

    def generate(self, spec):
        del spec
        raise NotImplementedError("Image generation is not enabled in Visual V1.")
