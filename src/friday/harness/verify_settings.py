"""Configuration for the verify node's screenshot diff and scorekeeping."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DiffSettings:
    """Tuning for the screenshot diff used by verify.

    These defaults are a starting point and must be tuned against the real
    container (the panel clock and cursor blink change by themselves and will
    otherwise report as a change). ``ignore_regions`` are (x, y, w, h)
    rectangles in screenshot pixels; each region's pixels are excluded from the
    difference before computing the changed ratio.
    """

    tolerance: int = 25
    min_changed_ratio: float = 0.01
    ignore_regions: tuple[tuple[int, int, int, int], ...] = ()

    # Max history entries verify keeps before summarizing oldest ones.
    max_history: int = 20

    # Type/key/hold_key actions are recorded by payload length, never by text.
    max_action_summary: int = 120

    # A note, not a default the code reads: retune tolerance/min_changed_ratio
    # on the real container after recording its live panel clock/cursor blink.


@dataclass(frozen=True, slots=True)
class VerifySettings:
    """Bounds and thresholds for the verify node's bookkeeping."""

    diff: DiffSettings = field(default_factory=DiffSettings)
    stuck_warning_level: int = 2
    max_stuck: int = 3