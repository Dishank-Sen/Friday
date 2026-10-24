from scripts.gen_keybinding_doc import OUTPUT, render


def test_keybinding_document_is_generated() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render()
