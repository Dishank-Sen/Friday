from __future__ import annotations

from pathlib import Path

from scripts.gen_harness_contract import OUTPUT, render


def test_harness_contract_generated_file_is_up_to_date() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render()


def test_contract_table_is_embedded_in_harness_docs() -> None:
    source = render().splitlines()
    docs = Path("docs/harness.md").read_text(encoding="utf-8")
    # the header and every data row rendered from the contract appear verbatim
    assert source[0] in docs
    assert source[2] in docs
    assert source[3] in docs
    assert source[4] in docs