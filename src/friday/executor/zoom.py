"""Pillow-backed zoomed screenshot views."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image


@dataclass(frozen=True, slots=True)
class ZoomView:
    """A zoomed PNG with a mapping back to real screen pixels."""

    image_png: bytes
    screen_size: tuple[int, int]
    crop: tuple[int, int, int, int]

    def to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Map a coordinate in this zoomed image to a real screen pixel."""
        width, height = self.screen_size
        left, top, right, bottom = self.crop
        crop_width = right - left
        crop_height = bottom - top
        zoom_width, zoom_height = self.image_size
        if not 0 <= x < zoom_width or not 0 <= y < zoom_height:
            raise ValueError("zoom coordinates are outside the image")
        screen_x = min(width - 1, left + round(x * crop_width / zoom_width))
        screen_y = min(height - 1, top + round(y * crop_height / zoom_height))
        return screen_x, screen_y

    @property
    def image_size(self) -> tuple[int, int]:
        with Image.open(BytesIO(self.image_png)) as image:
            return image.size


def zoom_image(png: bytes, factor: float, x: int, y: int) -> ZoomView:
    """Crop around a screen point, clamp at edges, and scale back to image size."""
    with Image.open(BytesIO(png)) as source:
        image = source.convert("RGB")
    width, height = image.size
    if not 0 <= x < width or not 0 <= y < height:
        raise ValueError(f"coordinates ({x}, {y}) are outside screenshot {width}x{height}")
    crop_width = max(1, round(width / factor))
    crop_height = max(1, round(height / factor))
    left = min(max(0, x - crop_width // 2), width - crop_width)
    top = min(max(0, y - crop_height // 2), height - crop_height)
    crop = (left, top, left + crop_width, top + crop_height)
    enlarged = image.crop(crop).resize((width, height), Image.Resampling.LANCZOS)
    output = BytesIO()
    enlarged.save(output, format="PNG")
    return ZoomView(output.getvalue(), (width, height), crop)
