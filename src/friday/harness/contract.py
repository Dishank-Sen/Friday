"""The single authoritative table of node read/write contracts.

``docs/harness.md`` renders its State table from this module, and every
implemented node's write- and read-contract test checks against it, so tests,
code, and docs cannot drift apart. Reads include the fields a node reads (via
``state.get``) and writes include the fields a node may return in its update.
"""

from __future__ import annotations


class NodeContract:
    """The documented read/write set for one harness node."""

    __slots__ = ("reads", "writes")

    def __init__(self, reads: frozenset[str], writes: frozenset[str]) -> None:
        self.reads = reads
        self.writes = writes


BUILD_CONTEXT = NodeContract(
    reads=frozenset(
        {
            "goal",
            "focused_app",
            "guard_verdict",
            "hint",
            "history",
            "last_result",
            "max_steps",
            "pending_action",
            "retries",
            "screen_size",
            "screenshot_path",
            "step",
            "windows",
        }
    ),
    writes=frozenset({"prompt", "hint"}),
)

GUARD = NodeContract(
    reads=frozenset(
        {
            "focused_app",
            "history",
            "max_steps",
            "pending_action",
            "retries",
            "screen_size",
            "status",
            "step",
        }
    ),
    writes=frozenset({"guard_verdict", "hint"}),
)

OBSERVE = NodeContract(
    reads=frozenset(),
    writes=frozenset(
        {"screenshot_path", "screen_size", "windows", "focused_app", "status", "final_report"}
    ),
)

# Implemented nodes, in graph order. Add decide/settle/verify/finish as they land.
NODES: dict[str, NodeContract] = {
    "observe": OBSERVE,
    "build_context": BUILD_CONTEXT,
    "guard": GUARD,
}


def _as_table_markdown() -> str:
    """Render the read/write contract as the markdown table used by docs."""
    lines = ["| Node | Reads | Writes |", "| --- | --- | --- |"]
    for name in ("observe", "build_context", "guard"):
        contract = NODES[name]
        reads = ", ".join(sorted(contract.reads)) or "—"
        writes = ", ".join(sorted(contract.writes)) or "—"
        lines.append(f"| {name} | {reads} | {writes} |")
    return "\n".join(lines)