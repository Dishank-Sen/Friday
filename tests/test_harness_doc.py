from scripts.draw_harness import OUTPUT, render


def test_harness_diagram_is_generated() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render()
