"""Canonical JSON serialization and hashing utilities.

This module owns every representation boundary for compiler artifacts:
structural stages produce immutable typed objects, and this module turns those
objects into dictionaries, canonical JSON bytes/text, and cryptographic hashes.
It does not perform graph traversal, dependency decisions, or classification.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from dependency_algebra.ir import (
    AnalysisResult,
    DependencyResult,
    Edge,
    ProjectedIR,
    ReachabilityResult,
    TraversalEdge,
    WorkloadReachability,
)


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


def edge_to_dict(edge: Edge) -> dict[str, str]:
    return {"edge_id": edge.edge_id, "component_id": edge.component_id}


def traversal_edge_to_dict(edge: TraversalEdge) -> dict[str, str]:
    return {"edge_id": edge.edge_id, "from": edge.source, "to": edge.target}


def workload_reachability_to_dict(result: WorkloadReachability) -> dict[str, Any]:
    return {
        "workload_id": result.workload_id,
        "roots": list(result.roots),
        "target": result.target,
        "reachable": result.reachable,
        "reached_by": list(result.reached_by),
        "visited_nodes": list(result.visited_nodes),
        "traversal_edges": [traversal_edge_to_dict(edge) for edge in result.traversal_edges],
        "diagnostics": [],
    }


def reachability_result_to_dict(result: ReachabilityResult, *, include_hash: bool = True) -> dict[str, Any]:
    doc = {
        "schema_version": result.schema_version,
        "topology_id": result.topology_id,
        "normalized_ir_hash": result.normalized_ir_hash,
        "results": [workload_reachability_to_dict(item) for item in result.results],
    }
    if include_hash:
        doc["reachability_result_hash"] = result.reachability_result_hash or reachability_result_hash(result)
    return doc


def reachability_result_hash(result: ReachabilityResult) -> str:
    return sha256_digest(reachability_result_to_dict(result, include_hash=False))


def projected_ir_identity_hash(normalized_ir_hash: str, removed: tuple[str, ...]) -> str:
    return sha256_digest({"normalized_ir_hash": normalized_ir_hash, "removed": list(removed)})


def projected_ir_to_dict(projection: ProjectedIR) -> dict[str, Any]:
    return {
        "removed": set(projection.removed),
        "adjacency": {key: [edge_to_dict(edge) for edge in edges] for key, edges in projection.adjacency.items()},
        "roots": list(projection.roots),
    }


def projected_reachability_identity_hash(visited_nodes: tuple[str, ...], target: str) -> str:
    return sha256_digest({"visited_nodes": list(visited_nodes), "target": target})


def dependency_result_to_dict(result: DependencyResult, *, include_hash: bool = True) -> dict[str, Any]:
    doc = {
        "schema_version": result.schema_version,
        "workload_id": result.workload_id,
        "normalized_ir_hash": result.normalized_ir_hash,
        "roots": list(result.roots),
        "target": result.target,
        "candidate_set": list(result.candidate_set),
        "projected_ir_hash": result.projected_ir_hash,
        "reachability_result_hash": result.reachability_result_hash,
        "dependency": result.dependency,
        "dependency_reason": result.dependency_reason,
        "reachable_after_projection": list(result.reachable_after_projection),
        "diagnostics": [dict(item) for item in result.diagnostics],
    }
    if include_hash:
        doc["dependency_result_hash"] = result.dependency_result_hash or dependency_result_hash(result)
    return doc


def dependency_result_hash(result: DependencyResult) -> str:
    return sha256_digest(dependency_result_to_dict(result, include_hash=False))


def analysis_result_to_dict(result: AnalysisResult, *, include_hash: bool = True) -> dict[str, Any]:
    doc = {
        "schema_version": result.schema_version,
        "topology_id": result.topology_id,
        "normalized_ir_hash": result.normalized_ir_hash,
        "classification": result.classification,
        "reachability": reachability_result_to_dict(result.reachability),
        "dependencies": [dependency_result_to_dict(dependency) for dependency in result.dependencies],
    }
    if include_hash:
        doc["dependency_result_hash"] = analysis_result_hash(result)
    return doc


def analysis_result_hash(result: AnalysisResult) -> str:
    return sha256_digest(analysis_result_to_dict(result, include_hash=False))


def normalized_ir_hash(ir_without_hash: Mapping[str, Any]) -> str:
    return sha256_digest(dict(ir_without_hash))


def hash_receipt_hash(receipt_without_hash: Mapping[str, Any]) -> str:
    return sha256_digest(dict(receipt_without_hash))
