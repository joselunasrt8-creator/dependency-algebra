"""Canonical JSON serialization and hashing utilities.

This module is intentionally isolated: compiler stages ask it for canonical
bytes or hashes, but it does not know graph semantics, validation rules, or CLI
concerns.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_bytes(document: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes with no trailing newline."""

    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_json_text(document: Any) -> str:
    """Return deterministic JSON text with no trailing newline."""

    return canonical_json_bytes(document).decode("utf-8")


def sha256_digest(document: Any) -> str:
    """Return the canonical sha256 digest for a JSON-serializable document."""

    return "sha256:" + hashlib.sha256(canonical_json_bytes(document)).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    """Return the sha256 digest for exact input bytes."""

    return "sha256:" + hashlib.sha256(payload).hexdigest()
