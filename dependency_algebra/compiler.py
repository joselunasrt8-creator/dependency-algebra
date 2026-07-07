"""Canonical compiler facade."""

from __future__ import annotations

from typing import Any

from dependency_algebra.diagnostics import CompilerDiagnosticException
from dependency_algebra.engine import analyze
from dependency_algebra.frontend import TOPOLOGY_SCHEMA_VERSION, parse_topology, validate_and_normalize
from dependency_algebra.serialization import hash_receipt_hash, sha256_bytes, sha256_digest
from dependency_algebra.version import __version__

COMPILER_VERSION = "dependency-algebra.compiler.v1"
ARTIFACT_SCHEMA_VERSION = "dependency-algebra.artifact.v1"


def compile(source: str | bytes, *, source_id: str = "stdin", max_depth: int | None = None) -> dict[str, Any]:
    """Compile raw JSON into a canonical hash receipt."""

    source_text, source_bytes = _source_text_and_bytes(source)
    topology = parse_topology(source_text, source_id)
    ir = validate_and_normalize(topology, source_id)
    dependency = analyze(ir, max_depth=max_depth)
    receipt = {
        "schema_version": "dependency-algebra.hash-receipt.v1",
        "compiler_version": COMPILER_VERSION,
        "package_version": __version__,
        "input_hash": sha256_bytes(source_bytes),
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "dependency_result_hash": dependency["dependency_result_hash"],
        "classification": dependency["classification"],
    }
    # Hash boundary: canonical hash receipt payload, excluding
    # hash_receipt_hash because it is added only after hashing.
    receipt["hash_receipt_hash"] = hash_receipt_hash(receipt)
    return receipt


def compile_artifact(source: str | bytes, *, source_id: str = "stdin", max_depth: int | None = None) -> dict[str, Any]:
    """Compile raw topology JSON into the canonical structural evidence artifact."""

    source_text, source_bytes = _source_text_and_bytes(source)
    topology = parse_topology(source_text, source_id)
    ir = validate_and_normalize(topology, source_id)
    analysis = analyze(ir, max_depth=max_depth)
    dependencies = analysis["dependencies"]
    artifact = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "source_topology_schema_version": TOPOLOGY_SCHEMA_VERSION,
        "compiler_version": COMPILER_VERSION,
        "package_version": __version__,
        "input_hash": sha256_bytes(source_bytes),
        "normalized_ir_hash": ir["normalized_ir_hash"],
        "classification": analysis["classification"],
        "reachability_graph": analysis["reachability"],
        "dependency_lattice": dependencies,
        "failure_surface": [item for item in dependencies if item["dependency"]],
        "redundancy_map": {
            item["workload_id"]: {
                "candidate_set": item["candidate_set"],
                "dependency": item["dependency"],
                "dependency_reason": item["dependency_reason"],
            }
            for item in dependencies
        },
        "k_of_n_resilience_profile": {
            item["workload_id"]: {
                "candidate_count": len(item["candidate_set"]),
                "reachable_after_projection_count": len(item["reachable_after_projection"]),
            }
            for item in dependencies
        },
        "annihilation_conditions": [
            {
                "workload_id": item["workload_id"],
                "candidate_set": item["candidate_set"],
                "target": item["target"],
            }
            for item in dependencies
            if item["dependency"]
        ],
        "diagnostics": [],
        "warnings": [],
        "errors": [],
        "provenance": {
            "source_id": source_id,
            "pipeline": ["parse_topology", "validate_and_normalize", "analyze", "emit_artifact"],
            "analysis_result_hash": analysis["dependency_result_hash"],
        },
    }
    # Hash boundary: canonical structural artifact payload, excluding
    # artifact_hash because it is added only after hashing.
    artifact["artifact_hash"] = sha256_digest(artifact)
    return artifact


def _source_text_and_bytes(source: str | bytes) -> tuple[str, bytes]:
    if isinstance(source, bytes):
        return source.decode("utf-8"), source
    return source, source.encode("utf-8")
