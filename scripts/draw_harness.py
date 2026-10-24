"""Generate the Mermaid diagram for the harness topology."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "harness.mmd"

if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from friday.harness.graph import build_graph  # noqa: E402


def render() -> str:
    """Render Mermaid from the compiled default harness graph."""
    return build_graph().get_graph().draw_mermaid()


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
