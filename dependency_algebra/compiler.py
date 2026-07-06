"""Canonical compiler facade."""

from __future__ import annotations

from typing import Any

from dependency_algebra.diagnostics import CompilerDiagnosticException
from dependency_algebra.engine import analyze
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.serialization import hash_receipt_hash, sha256_bytes

COMPILER_VERSION = "dependency-algebra.compiler.v1"


def compile(source: str | bytes, *, source_id: str = "stdin", max_depth: int | None = None) -> dict[str, Any]:
    """Compile raw JSON into a canonical hash receipt."""

    if isinstance(source, bytes):
        source_text = source.decode("utf-8")
        source_bytes = source
    else:
        source_text = source
        source_bytes = source.encode("utf-8")
    topology = parse_topology(source_text, source_id)
    ir = validate_and_normalize(topology, source_id)
    dependency = analyze(ir, max_depth=max_depth)
    receipt = {
        "schema_version": "dependency-algebra.hash-receipt.v1",
        "compiler_version": COMPILER_VERSION,
        "input_hash": sha256_bytes(source_bytes),
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "dependency_result_hash": dependency["dependency_result_hash"],
        "classification": dependency["classification"],
    }
    # Hash boundary: canonical hash receipt payload, excluding
    # hash_receipt_hash because it is added only after hashing.
    receipt["hash_receipt_hash"] = hash_receipt_hash(receipt)
    return receipt

__all__ = ["COMPILER_VERSION", "CompilerDiagnosticException", "compile"]
