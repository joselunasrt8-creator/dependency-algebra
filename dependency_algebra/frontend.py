"""Frontend parsing, validation, and canonical IR construction."""

from __future__ import annotations

import json
import re
from json import JSONDecodeError
from typing import Any

from dependency_algebra.diagnostics import CompilerDiagnosticException, diagnostic_document, make_diagnostic
from dependency_algebra.serialization import normalized_ir_hash

TOPOLOGY_SCHEMA_VERSION = "dependency-algebra.topology.v1"
IR_SCHEMA_VERSION = "dependency-algebra.ir.v1"
ID_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
CLASSIFICATIONS = {"VALID", "DEGRADED", "NULL"}


def parse_topology(source: str, source_id: str) -> dict[str, Any]:
    try:
        document = json.loads(source)
    except JSONDecodeError as exc:
        diagnostic = make_diagnostic(
            "PARSER.INVALID_JSON",
            "parse",
            "Source is not valid JSON.",
            "document",
            source_id,
            source_id,
            line=exc.lineno,
            column=exc.colno,
        )
        raise CompilerDiagnosticException(diagnostic_document([diagnostic])) from exc
    if not isinstance(document, dict):
        _raise_single("PARSER.INVALID_JSON", "parse", "Source JSON must be an object.", "document", source_id, source_id)
    return document


def validate_and_normalize(document: dict[str, Any], source_id: str) -> dict[str, Any]:
    diagnostics: list[dict[str, Any]] = []
    _validate_shape(document, source_id, diagnostics)
    if diagnostics:
        raise CompilerDiagnosticException(diagnostic_document(diagnostics))

    component_ids = [component["id"] for component in document["components"]]
    edge_ids = [edge["id"] for edge in document["edges"]]
    workload_ids = [workload["id"] for workload in document["workloads"]]
    component_set = set(component_ids)

    for duplicate in _duplicates(component_ids):
        diagnostics.append(make_diagnostic("NORMALIZE.DUPLICATE_COMPONENT_ID", "normalization", "Component identifier is declared more than once.", "component", duplicate, source_id, _first_index(document["components"], duplicate)))
    for duplicate in _duplicates(edge_ids):
        diagnostics.append(make_diagnostic("NORMALIZE.DUPLICATE_EDGE_ID", "normalization", "Edge identifier is declared more than once.", "edge", duplicate, source_id, _first_index(document["edges"], duplicate)))
    for duplicate in _duplicates(workload_ids):
        diagnostics.append(make_diagnostic("NORMALIZE.DUPLICATE_WORKLOAD_ID", "normalization", "Workload identifier is declared more than once.", "workload", duplicate, source_id, _first_index(document["workloads"], duplicate)))

    if not diagnostics:
        for index, edge in enumerate(document["edges"]):
            if edge["from"] not in component_set:
                diagnostics.append(make_diagnostic("NORMALIZE.UNRESOLVED_EDGE_FROM", "normalization", "Edge source endpoint does not resolve to a component.", "edge", edge["id"], source_id, index))
            if edge["to"] not in component_set:
                diagnostics.append(make_diagnostic("NORMALIZE.UNRESOLVED_EDGE_TO", "normalization", "Edge target endpoint does not resolve to a component.", "edge", edge["id"], source_id, index))
        for index, workload in enumerate(document["workloads"]):
            for root in workload["roots"]:
                if root not in component_set:
                    diagnostics.append(make_diagnostic("NORMALIZE.UNRESOLVED_WORKLOAD_ROOT", "normalization", "Workload root does not resolve to a component.", "root", root, source_id, index))
            if workload["target"] not in component_set:
                diagnostics.append(make_diagnostic("NORMALIZE.UNRESOLVED_WORKLOAD_TARGET", "normalization", "Workload target does not resolve to a component.", "target", workload["target"], source_id, index))
            if len(workload["candidate_set"]) == 0:
                diagnostics.append(make_diagnostic("NORMALIZE.EMPTY_CANDIDATE_SET", "normalization", "Workload candidate set must not be empty.", "candidate_set", workload["id"], source_id, index))
            for candidate in workload["candidate_set"]:
                if candidate not in component_set:
                    diagnostics.append(make_diagnostic("NORMALIZE.UNRESOLVED_CANDIDATE", "normalization", "Candidate does not resolve to a component.", "candidate", candidate, source_id, index))
    if diagnostics:
        raise CompilerDiagnosticException(diagnostic_document(diagnostics))
    return _normalize(document, source_id)


def _validate_shape(document: dict[str, Any], source_id: str, diagnostics: list[dict[str, Any]]) -> None:
    if document.get("schema_version") != TOPOLOGY_SCHEMA_VERSION:
        diagnostics.append(make_diagnostic("AST.UNSUPPORTED_SCHEMA_VERSION", "ast_construction", "Topology schema version is not supported.", "schema_version", str(document.get("schema_version")), source_id))
    for field in ("topology_id", "components", "edges", "workloads"):
        if field not in document:
            diagnostics.append(make_diagnostic("AST.MISSING_REQUIRED_FIELD", "ast_construction", "Required topology field is missing.", "document", field, source_id))
    if diagnostics:
        return
    if not isinstance(document["components"], list) or not isinstance(document["edges"], list) or not isinstance(document["workloads"], list):
        diagnostics.append(make_diagnostic("AST.INVALID_FIELD_TYPE", "ast_construction", "Topology collections must be arrays.", "document", document.get("topology_id", source_id), source_id))
        return
    if not document["components"] or not document["workloads"]:
        diagnostics.append(make_diagnostic("AST.EMPTY_REQUIRED_COLLECTION", "ast_construction", "Components and workloads must not be empty.", "document", document.get("topology_id", source_id), source_id))
        return
    for kind, items in (("component", document["components"]), ("edge", document["edges"]), ("workload", document["workloads"])):
        for index, item in enumerate(items):
            if not isinstance(item, dict) or "id" not in item or not isinstance(item["id"], str) or not ID_RE.match(item["id"]):
                diagnostics.append(make_diagnostic(f"AST.INVALID_{kind.upper()}", "ast_construction", f"Invalid {kind} declaration.", kind, str(index), source_id, index))
                continue
            required = {"component": ["id"], "edge": ["id", "from", "to"], "workload": ["id", "roots", "target", "candidate_set", "expected_classification"]}[kind]
            for field in required:
                if field not in item:
                    diagnostics.append(make_diagnostic("AST.MISSING_REQUIRED_FIELD", "ast_construction", "Required field is missing.", kind, item["id"], source_id, index))
            if kind == "workload":
                if not item.get("roots"):
                    diagnostics.append(make_diagnostic("AST.EMPTY_WORKLOAD_ROOTS", "ast_construction", "Workload roots must not be empty.", "root", item["id"], source_id, index))
                if not item.get("candidate_set"):
                    diagnostics.append(make_diagnostic("AST.EMPTY_CANDIDATE_SET", "ast_construction", "Workload candidate set must not be empty.", "candidate_set", item["id"], source_id, index))
                if item.get("expected_classification") not in CLASSIFICATIONS:
                    diagnostics.append(make_diagnostic("AST.INVALID_CLASSIFICATION", "ast_construction", "Workload classification is not supported.", "workload", item["id"], source_id, index))


def _normalize(document: dict[str, Any], source_id: str) -> dict[str, Any]:
    components = sorted(({"id": c["id"], **({"type": c["type"]} if "type" in c else {}), **({"metadata": c.get("metadata", c.get("labels", {}))} if c.get("metadata", c.get("labels", {})) else {}), "source": {"source_id": source_id}} for c in document["components"]), key=lambda c: c["id"])
    edges = sorted(({"id": e["id"], "from": e["from"], "to": e["to"], **({"metadata": e.get("metadata", e.get("labels", {}))} if e.get("metadata", e.get("labels", {})) else {}), "source": {"source_id": source_id}} for e in document["edges"]), key=lambda e: e["id"])
    component_ids = [c["id"] for c in components]
    adjacency: dict[str, list[dict[str, str]]] = {cid: [] for cid in component_ids}
    reverse: dict[str, list[dict[str, str]]] = {cid: [] for cid in component_ids}
    for edge in edges:
        adjacency[edge["from"]].append({"edge_id": edge["id"], "component_id": edge["to"]})
        reverse[edge["to"]].append({"edge_id": edge["id"], "component_id": edge["from"]})
    for value in list(adjacency.values()) + list(reverse.values()):
        value.sort(key=lambda item: item["edge_id"])
    workloads = sorted(({"id": w["id"], "roots": sorted(set(w["roots"])), "target": w["target"], "candidate_set": sorted(set(w["candidate_set"])), "expected_classification": w["expected_classification"], "source": {"source_id": source_id}} for w in document["workloads"]), key=lambda w: w["id"])
    ir = {"schema_version": IR_SCHEMA_VERSION, "topology_id": document["topology_id"], "components": components, "edges": edges, "adjacency": adjacency, "reverse_adjacency": reverse, "workloads": workloads}
    # Hash boundary: canonical normalized IR structural payload, excluding
    # normalized_ir_hash because it is added only after hashing.
    ir["normalized_ir_hash"] = normalized_ir_hash(ir)
    return ir


def _duplicates(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


def _first_index(items: list[dict[str, Any]], identifier: str) -> int:
    return next(index for index, item in enumerate(items) if item.get("id") == identifier)


def _raise_single(code: str, phase: str, message: str, kind: str, subject_id: str, source_id: str) -> None:
    raise CompilerDiagnosticException(diagnostic_document([make_diagnostic(code, phase, message, kind, subject_id, source_id)]))
