"""Best-effort redaction of high-confidence secrets in exported text."""

from __future__ import annotations

import re
from typing import Any

_REDACTED = "[REDACTED]"

_PATTERNS = [
    (
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[REDACTED PEM]",
    ),
    (re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}\b"), _REDACTED),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), _REDACTED),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), _REDACTED),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), _REDACTED),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), _REDACTED),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), _REDACTED),
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        _REDACTED,
    ),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{20,}=*"), "Bearer [REDACTED]"),
]


def redact(text: str) -> str:
    """Replace high-confidence secret patterns in a string."""
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_obj(value: Any) -> Any:
    """Recursively sanitize string values in JSON-like data."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {key: sanitize_obj(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_obj(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_obj(item) for item in value)
    return value
