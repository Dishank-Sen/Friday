"""Task 6511 Layer 1: secret value wrapping, redaction, and the in-memory vault.

The one rule this whole module exists to hold: a secret value is never
recoverable except through ``unwrap`` (the single deliberate typing gate), and
it never appears in repr, str, model_dump, json, pickle, or logged output.
"""

from __future__ import annotations

import json
import logging
import pickle

import pytest
from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticSerializationError

from friday.secrets import (
    LoggingFilter,
    MemorySecretVault,
    SecretValue,
    SecretVault,
    redact,
    unwrap,
)


def test_value_is_never_in_repr_or_str() -> None:
    secret = SecretValue("hunter2")

    assert "hunter2" not in str(secret)
    assert "hunter2" not in repr(secret)
    assert "hunter2" not in str(secret)
    assert str(secret) != "hunter2"


def test_fstring_and_format_render_redacted() -> None:
    secret = SecretValue("hunter2")

    assert f"{secret}" == str(secret)
    assert f"{secret}" != "hunter2"
    assert format(secret, "") != "hunter2"


def test_unwrap_is_the_only_way_to_reach_the_value() -> None:
    secret = SecretValue("hunter2")

    assert unwrap(secret) == "hunter2"


def test_json_dumps_refuses_the_wrapper() -> None:
    secret = SecretValue("hunter2")

    with pytest.raises(TypeError):
        json.dumps(secret)


def test_pickle_refuses_the_wrapper_eagerly() -> None:
    secret = SecretValue("hunter2")

    with pytest.raises(TypeError):
        pickle.dumps(secret)


def test_bytes_of_the_wrapper_is_not_the_value() -> None:
    secret = SecretValue("hunter2")

    with pytest.raises(TypeError):
        bytes(secret)


def test_pydantic_json_dump_of_a_secret_field_refuses() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        token: SecretValue

    model = Model(token=SecretValue("hunter2"))

    with pytest.raises(PydanticSerializationError):
        model.model_dump_json()
    with pytest.raises(PydanticSerializationError):
        model.model_dump(mode="json")


def test_pydantic_python_dump_never_exposes_the_value() -> None:
    class Model(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        token: SecretValue

    model = Model(token=SecretValue("hunter2"))

    dumped = model.model_dump()
    assert isinstance(dumped["token"], SecretValue)
    assert "hunter2" not in repr(dumped["token"])


# --- redact() -----------------------------------------------------------------


def test_redact_swaps_every_value_occurrence_for_the_marker() -> None:
    secret = SecretValue("hunter2")

    out = redact("login with hunter2 then hunter2 again", secret)

    assert out == "login with <secret> then <secret> again"
    assert "hunter2" not in out


def test_redact_with_no_secrets_is_identity() -> None:
    assert redact("plain text") == "plain text"


def test_redact_does_not_touch_unrelated_text() -> None:
    secret = SecretValue("hunter2")

    assert redact("nothing sensitive here", secret) == "nothing sensitive here"


# --- LoggingFilter -------------------------------------------------------------


def _capture_logger() -> tuple[logging.Logger, list[logging.LogRecord]]:
    logger = logging.getLogger("test.friday.secrets")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger.addHandler(_Capture())
    return logger, records


def test_logging_filter_redacts_the_value_in_emitted_records() -> None:
    secret = SecretValue("hunter2")
    logger, records = _capture_logger()
    logger.addFilter(LoggingFilter(lambda: [secret]))

    logger.info("deploying with token hunter2 attached")

    assert len(records) == 1
    message = records[0].getMessage()
    assert message == "deploying with token <secret> attached"
    assert "hunter2" not in message


def test_logging_filter_leaves_unrelated_messages_alone() -> None:
    secret = SecretValue("hunter2")
    logger, records = _capture_logger()
    logger.addFilter(LoggingFilter(lambda: [secret]))

    logger.info("plain message")

    assert records[0].getMessage() == "plain message"


# --- SecretVault ---------------------------------------------------------------


def test_memory_vault_is_a_secret_vault() -> None:
    vault: SecretVault = MemorySecretVault()
    for member in ("names", "store", "contains", "get", "drop"):
        assert callable(getattr(vault, member))


def test_memory_vault_round_trip_via_wrapped_values() -> None:
    vault = MemorySecretVault()
    vault.store("db_password", SecretValue("hunter2"))

    assert vault.names() == frozenset({"db_password"})
    assert vault.contains("db_password")
    assert vault.contains("missing") is False

    stored = vault.get("db_password")
    assert isinstance(stored, SecretValue)
    assert unwrap(stored) == "hunter2"
    assert "hunter2" not in str(stored)


def test_memory_vault_drop_removes_the_entry() -> None:
    vault = MemorySecretVault()
    vault.store("db_password", SecretValue("hunter2"))

    vault.drop("db_password")

    assert vault.names() == frozenset()
    assert vault.contains("db_password") is False
    assert vault.get("db_password") is None


def test_memory_vault_get_for_unknown_name_is_none() -> None:
    vault = MemorySecretVault()

    assert vault.get("nope") is None
