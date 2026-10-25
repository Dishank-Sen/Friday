"""Task 6511 — secret handling primitives (Layer 1).

Nothing here performs terminal I/O, touches the desktop, or reaches a network.
Those belong to the runner (terminal channel) and the executor/typing path
(Layer 2). This package only provides the value wrapper, the vault, and the
redaction surface that every later candidate body for a secret passes through.
"""

from __future__ import annotations

from friday.secrets.redact import LoggingFilter, redact
from friday.secrets.value import SecretValue, unwrap
from friday.secrets.vault import MemorySecretVault, SecretVault

__all__ = [
    "LoggingFilter",
    "MemorySecretVault",
    "SecretValue",
    "SecretVault",
    "redact",
    "unwrap",
]
