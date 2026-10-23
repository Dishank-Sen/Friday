from io import BytesIO

from PIL import Image

from friday.vision.annotate import annotate_crosshair


def test_annotate_crosshair_returns_png() -> None:
    source = Image.new("RGB", (20, 20), "white")
    input_bytes = BytesIO()
    source.save(input_bytes, format="PNG")

    result = annotate_crosshair(input_bytes.getvalue(), 10, 10)

    assert result.startswith(b"\x89PNG\r\n\x1a\n")
