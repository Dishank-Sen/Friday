from friday.llm.messages import png_data_url


def test_png_data_url_has_exact_prefix() -> None:
    assert png_data_url(b"png").startswith("data:image/png;base64,")
