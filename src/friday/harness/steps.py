"""run_steps: the single executor-boundary for one or more validated steps."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, field_serializer

from friday.actions.models import Action, ActionResult
from friday.desktop.errors import (
    DesktopConnectionError,
    DesktopRequestError,
    DesktopTimeoutError,
)
from friday.operations.registry import SystemOperation

# The fixed, small set of error types callers and the node can rely on. The
# layer's richer errors are collapsed into these by ``run_steps``.
ERROR_TYPES = frozenset(
    {
        "timeout",
        "rejected_by_server",
        "command_failed",
        "bounds",
        "not_available",
        "connection",
        "internal_error",
        "unknown",
    }
)

# Actions that carry user-supplied input. Their results are never surfaced in
# ``detail`` so typed text, clipboard content, and file contents cannot leak.
_SENSITIVE_OPERATIONS: frozenset[str] = frozenset({"type", "key", "hold_key"})

_TIMEOUT_MESSAGE = "outcome unknown: the action may have run; check the screen before repeating"
_CONNECTION_MESSAGE = "outcome unknown: the control server could not be reached"


class ConfigurationError(ValueError):
    """run_steps was asked to do something the settings forbid."""


class StepSpec(BaseModel):
    """One validated step to run: an input action or a system operation."""

    model_config = ConfigDict(extra="forbid")

    payload: Action | SystemOperation
    expected_result: str | None = None


class StepOutcome(BaseModel):
    """The record run_steps produces for one executed action.

    Serializes to the ``last_result`` shape; ``image_png`` carries the transient
    bytes the node saves through the trace writer and is excluded from every
    serialization, so image bytes never reach state.
    """

    model_config = ConfigDict(extra="forbid")

    ok: bool
    operation: str
    detail: str | None = None
    error: dict[str, str] | None = None
    duration_ms: int = 0
    point: list[int, int] | None = None
    image_path: str | None = None
    expected_result: str | None = None
    image_png: bytes | None = None

    @field_serializer("image_png", when_used="json")
    def _no_image_bytes(self, value: bytes | None) -> None:
        return None


@dataclass(frozen=True, slots=True)
class ExecutorSettings:
    """Bounds for one run_steps call."""

    max_steps_per_call: int = 1
    max_detail: int = 400


def _sensitive(operation: str) -> bool:
    return operation in _SENSITIVE_OPERATIONS


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _classify_error(error: BaseException) -> tuple[str, str]:
    """Map a layer error to the fixed error table; keys never include a traceback."""
    if isinstance(error, DesktopTimeoutError):
        return "timeout", _TIMEOUT_MESSAGE
    if isinstance(error, DesktopConnectionError):
        return "connection", _CONNECTION_MESSAGE
    if isinstance(error, DesktopRequestError):
        kind = "rejected_by_server" if error.status_code < 500 else "command_failed"
        return kind, str(error)
    return "unknown", str(error)


def _clock_now() -> float:
    return time.monotonic()


def _name_of(payload: Action | SystemOperation) -> str:
    """The operation/action name of a step payload, for recording and detail rules."""
    name = getattr(payload, "operation", None) or getattr(payload, "action", None)
    return str(name or "")


def _record(
    payload: Action | SystemOperation,
    outcome: ActionResult | dict,
    *,
    started: float,
    clock: Callable[[], float],
    max_detail: int,
) -> StepOutcome:
    operation = _name_of(payload)
    detail: str | None = None
    ok: bool
    point = None
    image_png: bytes | None = None
    if isinstance(outcome, dict):
        ok = bool(outcome.get("ok", True))
        if not _sensitive(operation):
            detail = _operation_detail(outcome, max_detail)
    else:
        ok = outcome.ok
        if outcome.detail is not None and not _sensitive(operation):
            detail = _truncate(outcome.detail, max_detail)
        if outcome.point is not None:
            point = [int(outcome.point[0]), int(outcome.point[1])]
        image_png = outcome.image_png
    return StepOutcome(
        ok=ok,
        operation=operation,
        detail=detail,
        duration_ms=int(round((clock() - started) * 1000)),
        point=point,
        image_png=image_png,
    )


def _operation_detail(result: dict, max_detail: int) -> str | None:
    """Bounded detail text from an operation result.

    Operations return loose dicts (``output``/``text``/``content``/``entries``/
    ``pid``/``ok``). The text-carrying fields are preserved so read-type
    operations feed their result forward into the next prompt; pure status
    (``{ok: True}``) has no detail. The full dict is JSON-serialized, bounded,
    and returned as the single detail string.
    """
    text = json.dumps(result, sort_keys=True, ensure_ascii=False)
    return _truncate(text, max_detail)


def _failed_record(
    payload: Action | SystemOperation,
    error: dict[str, str],
    *,
    started: float,
    clock: Callable[[], float],
) -> StepOutcome:
    return StepOutcome(
        ok=False,
        operation=_name_of(payload),
        error=error,
        duration_ms=int(round((clock() - started) * 1000)),
    )


def run_steps(
    executor: object,
    steps: Sequence[StepSpec],
    *,
    settings: ExecutorSettings | None = None,
    clock: Callable[[], float] | None = None,
) -> list[StepOutcome]:
    """Run validated steps through the Executor, stopping at the first failure.

    The only function in the harness that talks to the ``Executor``. A sequence
    longer than ``settings.max_steps_per_call`` (default 1) raises
    ``ConfigurationError`` so batching stays off until the seam is deliberately
    widened. Each step runs once; failures are recorded in the returned outcomes
    and do not raise (except ``KeyboardInterrupt``/``SystemExit``, which
    propagate unchanged).
    """
    settings = settings or ExecutorSettings()
    if len(steps) > settings.max_steps_per_call:
        raise ConfigurationError(
            "batching is not enabled: pass at most max_steps_per_call steps per call"
        )
    clock = clock or _clock_now
    results: list[StepOutcome] = []
    for step in steps:
        started = clock()
        try:
            outcome = executor.execute(step.payload)  # type: ignore[attr-defined]
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as error:
            error_type, message = _classify_error(error)
            message = message[: settings.max_detail]
            results.append(
                _failed_record(
                    step.payload,
                    {"type": error_type, "message": message},
                    started=started,
                    clock=clock,
                )
            )
            break
        record = _record(
            step.payload,
            outcome,
            started=started,
            clock=clock,
            max_detail=settings.max_detail,
        )
        record.expected_result = step.expected_result
        results.append(record)
        ok = outcome.ok if not isinstance(outcome, dict) else outcome.get("ok", True)
        if not ok:
            break
    return results