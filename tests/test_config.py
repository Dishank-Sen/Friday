import pytest

from friday.config import FridayConfig


def test_default_config_has_fixed_resolution() -> None:
    config = FridayConfig()

    assert (config.width, config.height) == (1280, 720)
    assert config.viewer_port is None
    assert config.api_port is None


@pytest.mark.parametrize("kwargs", [{"width": 0}, {"height": -1}, {"api_port": 70000}])
def test_config_rejects_invalid_values(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        FridayConfig(**kwargs)
