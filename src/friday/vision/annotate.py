from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw


def annotate_crosshair(png: bytes, x: int, y: int) -> bytes:
    with Image.open(BytesIO(png)) as source:
        image = source.convert("RGBA")
    if not 0 <= x < image.width or not 0 <= y < image.height:
        raise ValueError("crosshair coordinates are outside the image")
    draw = ImageDraw.Draw(image)
    radius = 12
    draw.line((max(0, x - radius), y, min(image.width - 1, x + radius), y), fill="red", width=2)
    draw.line((x, max(0, y - radius), x, min(image.height - 1, y + radius)), fill="red", width=2)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
