"""Generate the Mermaid diagram for the harness topology."""

from __future__ import annotations

from pathlib import Path

from friday.harness.graph import build_graph

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "harness.mmd"


def render() -> str:
    """Render Mermaid from the compiled default harness graph."""
    return build_graph().get_graph().draw_mermaid()


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
