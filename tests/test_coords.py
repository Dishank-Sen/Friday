import pytest

from friday.vision.coords import PointResponse, normalized_to_pixels, to_pixel


def test_to_pixel_edges_and_clamp() -> None:
    assert to_pixel(0, 101) == 0
    assert to_pixel(1000, 101) == 100
    assert to_pixel(999, 101) == 100


def test_to_pixel_supports_non_default_grid() -> None:
    assert to_pixel(50, 200, grid=100) == 100


@pytest.mark.parametrize("value", [-1, 1001])
def test_to_pixel_rejects_out_of_range_values(value: int) -> None:
    with pytest.raises(ValueError, match="normalized coordinate"):
        to_pixel(value, 100)


def test_normalized_to_pixels_converts_both_axes() -> None:
    assert normalized_to_pixels(PointResponse(x=500, y=1000), 200, 300) == (100, 299)
