"""Generate the node read/write contract table used by docs/harness.md.

The contract table lives once in ``friday.harness.contract``; the harness doc
embeds the rendered rows so the tests that check node reads/writes against the
contract and the doc cannot disagree.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "harness_contract.md"

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from friday.harness.contract import _as_table_markdown  # noqa: E402


def render() -> str:
    """Render the read/write contract as markdown for embedding in the doc."""
    return _as_table_markdown()


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")