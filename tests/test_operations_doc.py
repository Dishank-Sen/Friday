from scripts.gen_operations_doc import OUTPUT, render


def test_operations_document_is_generated() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render()
