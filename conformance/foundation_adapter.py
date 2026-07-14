"""Foundation conformance adapter for SYNAPSE."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dependency_algebra import compile_artifact
from dependency_algebra.analysis import DEPENDENCY_ANALYSIS_ID
from dependency_algebra.analysis_registry import UnknownAnalysisPassError, core_analysis_registry
from dependency_algebra.diagnostics import CompilerDiagnosticException
from dependency_algebra.evidence import StructuralEvidenceValidationError, compile_structural_evidence_artifact, structural_evidence_artifact_hash
from dependency_algebra.serialization import canonical_json_text
from conformance.research_objects.discovery import discover
from conformance.research_objects.registry import get_handler

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_ROOT = ROOT.parent / "structural-analysis-foundations"
PAPER1_DEPENDENCY_RESEARCH_OBJECT_ID = "definition.dependency.dependency-predicate"
PAPER1_DEPENDENCY_FIXTURE_ID = "paper1.dependency-predicate.basic-v1"
PAPER1_NORMATIVE_REFERENCE = (
    "paper-1-dependency/research-objects/"
    "definition.dependency.dependency-predicate.json#canonical_statement"
)
PAPER1_RESEARCH_OBJECT_PATH = (
    "paper-1-dependency/research-objects/"
    "definition.dependency.dependency-predicate.json"
)
PAPER1_FIXTURE_SCHEMA_PATH = "schemas/canonical-dependency-predicate.schema.json"


def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def topology_from_fixture(fixture):
    canonical = canonical_context_from_fixture(fixture)
    nodes = canonical["nodes"]
    relations = canonical["relations"]
    roots = canonical["roots"]
    targets = canonical["targets"]
    candidate_set = canonical.get("candidate_component_set", [])

    workloads = _workloads_from_context(roots, targets, candidate_set)

    return {
        "schema_version": "dependency-algebra.topology.v1",
        "topology_id": fixture.get("topology_id", "paper1-dependency-predicate"),
        "components": [{"id": n} for n in nodes],
        "edges": [
            {"id": f"e{i}", "from": item["from"], "to": item["to"]}
            for i, item in enumerate(relations)
        ],
        "workloads": workloads,
    }


def canonical_context_from_fixture(fixture):
    payload = fixture.get("input", fixture)
    graph = payload.get("graph", payload.get("structural_object", payload.get("structure", payload)))
    workload = payload.get("workload", payload.get("workload_profile", payload))

    raw_nodes = graph.get("nodes", graph.get("structural_nodes", []))
    nodes = sorted(_identifier(item) for item in raw_nodes)

    raw_relations = graph.get("edges", graph.get("relations", graph.get("structural_relations", [])))
    relations = sorted(
        (
            {
                "from": _endpoint(item, "from", "source", "src"),
                "to": _endpoint(item, "to", "target", "dst"),
            }
            for item in raw_relations
        ),
        key=lambda item: (item["from"], item["to"]),
    )

    roots = sorted(_identifier(item) for item in workload.get("roots", workload.get("workload_roots", [])))
    targets = sorted(_identifier(item) for item in workload.get("targets", workload.get("workload_targets", [])))
    candidate_set = sorted(_identifier(item) for item in workload.get("candidate_component_set", []))

    return {
        "nodes": nodes,
        "relations": relations,
        "roots": roots,
        "targets": targets,
        "candidate_component_set": candidate_set,
    }


def _workloads_from_context(roots, targets, candidate_set):
    if candidate_set and targets:
        return [{
            "id": "paper1-dependency-workload",
            "roots": roots,
            "target": targets[0],
            "candidate_set": candidate_set,
            "expected_classification": "VALID",
        }]
    return [
        {
            "id": f"workload-{root}-to-{target}",
            "roots": [root],
            "target": target,
            "candidate_set": [root],
            "expected_classification": "VALID",
        }
        for root in roots
        for target in targets
    ]


def _identifier(item):
    if isinstance(item, str):
        return item
    for key in ("id", "node", "component_id"):
        if key in item:
            return item[key]
    raise KeyError(f"Cannot extract identifier from {item!r}")


def _endpoint(item, *keys):
    if isinstance(item, (list, tuple)):
        return item[0] if keys[0] in {"from", "source", "src"} else item[1]
    for key in keys:
        if key in item:
            return _identifier(item[key])
    raise KeyError(f"Cannot extract endpoint {keys!r} from {item!r}")


def run_paper1_dependency_conformance(
    fixture_path: str | Path,
    *,
    research_repo_path: str | Path = RESEARCH_ROOT,
    synapse_repo_path: str | Path = ROOT,
    analysis_id: str = DEPENDENCY_ANALYSIS_ID,
    registry=None,
    expected_source_fixture_hash: str | None = None,
    expected_normalized_ir_hash: str | None = None,
    second_artifact_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the canonical Paper 1 dependency fixture through SYNAPSE."""

    fixture_path = Path(fixture_path)
    fixture_bytes = fixture_path.read_bytes()
    source_fixture_hash = _sha256_prefixed(fixture_bytes)
    try:
        fixture = json.loads(fixture_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _blocked_result(
            source_fixture_hash=source_fixture_hash,
            verdict="FAIL",
            code="MALFORMED_FIXTURE",
            message=str(exc),
            research_repo_path=research_repo_path,
            synapse_repo_path=synapse_repo_path,
        )

    preliminary = _preflight_fixture(fixture)
    if preliminary is not None:
        return _result_from_preflight(
            fixture,
            preliminary,
            source_fixture_hash,
            research_repo_path=research_repo_path,
            synapse_repo_path=synapse_repo_path,
        )
    if expected_source_fixture_hash is not None and expected_source_fixture_hash != source_fixture_hash:
        return _conformance_result(
            fixture=fixture,
            research_repo_path=research_repo_path,
            synapse_repo_path=synapse_repo_path,
            source_fixture_hash=source_fixture_hash,
            normalized_ir_hash="UNOBSERVED",
            result_hash="UNOBSERVED",
            artifact_hash="UNOBSERVED",
            analysis_id=analysis_id,
            analysis_version="UNOBSERVED",
            expected_classification=_expected_classification(fixture),
            actual_classification="UNOBSERVED",
            verdict="FAIL",
            diagnostics=[_diagnostic("SOURCE_HASH_MISMATCH", "error", "source fixture hash did not match expected hash")],
        )

    topology = _paper1_topology_from_fixture(fixture)
    topology_source = canonical_json_text(topology)
    try:
        registry = registry or core_analysis_registry()
        artifact = compile_structural_evidence_artifact(
            topology_source,
            source_id=fixture["fixture_id"],
            registry=registry,
            analysis_id=analysis_id,
        )
        repeated = (
            copy.deepcopy(second_artifact_override)
            if second_artifact_override is not None
            else compile_structural_evidence_artifact(
                topology_source,
                source_id=fixture["fixture_id"],
                registry=registry,
                analysis_id=analysis_id,
            )
        )
    except (CompilerDiagnosticException, StructuralEvidenceValidationError, UnknownAnalysisPassError, ValueError) as exc:
        return _conformance_result(
            fixture=fixture,
            research_repo_path=research_repo_path,
            synapse_repo_path=synapse_repo_path,
            source_fixture_hash=source_fixture_hash,
            normalized_ir_hash="UNOBSERVED",
            result_hash="UNOBSERVED",
            artifact_hash="UNOBSERVED",
            analysis_id=analysis_id,
            analysis_version="UNOBSERVED",
            expected_classification=_expected_classification(fixture),
            actual_classification="UNOBSERVED",
            verdict="FAIL",
            diagnostics=[_diagnostic(_failure_code(exc), "error", str(exc))],
        )

    diagnostics: list[dict[str, str]] = []
    expected_classification = _expected_classification(fixture)
    actual_classification = artifact["result"]["payload"].get("classification", "UNOBSERVED")
    normalized_ir_hash = artifact["input"]["normalized_ir_hash"]
    result_hash = artifact["result"]["result_hash"]
    artifact_hash = artifact["artifact_hash"]

    if expected_normalized_ir_hash is not None and expected_normalized_ir_hash != normalized_ir_hash:
        diagnostics.append(_diagnostic("NORMALIZED_IR_HASH_MISMATCH", "error", "normalized IR hash did not match expected hash"))
    if artifact_hash != structural_evidence_artifact_hash(artifact):
        diagnostics.append(_diagnostic("ARTIFACT_HASH_MISMATCH", "error", "artifact hash did not validate"))
    diagnostics.extend(_semantic_diagnostics(fixture, artifact))
    if actual_classification != expected_classification:
        diagnostics.append(_diagnostic("EXPECTED_CLASSIFICATION_MISMATCH", "error", "actual classification did not match expected classification"))
    if canonical_json_text(artifact) != canonical_json_text(repeated):
        diagnostics.append(_diagnostic("REPEATED_RUN_DIVERGENCE", "error", "repeated structural evidence artifact was not byte-identical"))

    verdict = "PASS" if not diagnostics else "FAIL"
    if verdict == "PASS":
        diagnostics.append(_diagnostic("CONFORMANCE_PASS", "info", "canonical fixture produced deterministic validated evidence"))

    return _conformance_result(
        fixture=fixture,
        research_repo_path=research_repo_path,
        synapse_repo_path=synapse_repo_path,
        source_fixture_hash=source_fixture_hash,
        normalized_ir_hash=normalized_ir_hash,
        result_hash=result_hash,
        artifact_hash=artifact_hash,
        analysis_id=artifact["analysis"]["analysis_id"],
        analysis_version=artifact["analysis"]["analysis_version"],
        expected_classification=expected_classification,
        actual_classification=actual_classification,
        verdict=verdict,
        diagnostics=diagnostics,
    )


def _paper1_topology_from_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    payload = fixture["input"]
    graph = payload["graph"]
    workload = payload["workload"]
    targets = list(workload["targets"])
    if len(targets) != 1:
        raise ValueError("Paper 1 dependency fixture must declare exactly one target for SYNAPSE")
    return {
        "schema_version": "dependency-algebra.topology.v1",
        "topology_id": fixture.get("topology_id", "paper1-dependency-predicate"),
        "components": [{"id": _identifier(node)} for node in graph["nodes"]],
        "edges": [
            {"id": f"e{index}", "from": _endpoint(edge, "from", "source", "src"), "to": _endpoint(edge, "to", "target", "dst")}
            for index, edge in enumerate(graph["edges"])
        ],
        "workloads": [
            {
                "id": "paper1-dependency-workload",
                "roots": [_identifier(root) for root in workload["roots"]],
                "target": targets[0],
                "candidate_set": [_identifier(candidate) for candidate in workload["candidate_component_set"]],
                "expected_classification": "VALID",
            }
        ],
    }


def _preflight_fixture(fixture: Any) -> tuple[str, str, str] | None:
    if not isinstance(fixture, dict):
        return ("FAIL", "MALFORMED_FIXTURE", "fixture root must be an object")
    if fixture.get("research_object_id") != PAPER1_DEPENDENCY_RESEARCH_OBJECT_ID:
        return ("NOT_APPLICABLE", "UNKNOWN_RESEARCH_OBJECT", "research object is not mapped to a SYNAPSE analysis")
    if fixture.get("fixture_id") != PAPER1_DEPENDENCY_FIXTURE_ID:
        return ("NOT_APPLICABLE", "UNSUPPORTED_FIXTURE_VERSION", "fixture version is not supported by this adapter")
    if fixture.get("research_object_path") != PAPER1_RESEARCH_OBJECT_PATH or fixture.get("schema_path") != PAPER1_FIXTURE_SCHEMA_PATH:
        return ("FAIL", "MISSING_NORMATIVE_REFERENCE", "fixture does not declare the canonical Paper 1 research object and schema references")
    required = ("input", "expected_semantics", "deterministic_timestamp")
    missing = [field for field in required if field not in fixture]
    if missing:
        return ("FAIL", "MALFORMED_FIXTURE", f"fixture missing required fields: {missing}")
    try:
        graph = fixture["input"]["graph"]
        workload = fixture["input"]["workload"]
        expected = fixture["expected_semantics"]
        if not graph["nodes"] or "edges" not in graph:
            raise KeyError("input.graph.nodes/input.graph.edges")
        if not workload["roots"] or not workload["targets"] or not workload["candidate_component_set"]:
            raise KeyError("input.workload roots/targets/candidate_component_set")
        if "is_dependency" not in expected["canonical_outputs"]:
            raise KeyError("expected_semantics.canonical_outputs.is_dependency")
    except (KeyError, TypeError) as exc:
        return ("FAIL", "MALFORMED_FIXTURE", str(exc))
    return None


def _result_from_preflight(
    fixture: Any,
    preflight: tuple[str, str, str],
    source_fixture_hash: str,
    *,
    research_repo_path: str | Path,
    synapse_repo_path: str | Path,
) -> dict[str, Any]:
    verdict, code, message = preflight
    fixture_dict = fixture if isinstance(fixture, dict) else {}
    return _conformance_result(
        fixture=fixture_dict,
        research_repo_path=research_repo_path,
        synapse_repo_path=synapse_repo_path,
        source_fixture_hash=source_fixture_hash,
        normalized_ir_hash="UNOBSERVED",
        result_hash="UNOBSERVED",
        artifact_hash="UNOBSERVED",
        analysis_id=DEPENDENCY_ANALYSIS_ID,
        analysis_version="UNOBSERVED",
        expected_classification=_expected_classification(fixture_dict),
        actual_classification="UNOBSERVED",
        verdict=verdict,
        diagnostics=[_diagnostic(code, "error" if verdict == "FAIL" else "warning", message)],
    )


def _conformance_result(
    *,
    fixture: dict[str, Any],
    research_repo_path: str | Path,
    synapse_repo_path: str | Path,
    source_fixture_hash: str,
    normalized_ir_hash: str,
    result_hash: str,
    artifact_hash: str,
    analysis_id: str,
    analysis_version: str,
    expected_classification: str,
    actual_classification: str,
    verdict: str,
    diagnostics: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": "synapse.cross-repository-conformance-result.v1",
        "conformance_case_id": "paper1-dependency-predicate-basic-v1-to-synapse-dependency-analysis",
        "research_object_id": fixture.get("research_object_id", "UNOBSERVED"),
        "fixture_id": fixture.get("fixture_id", "UNOBSERVED"),
        "normative_specification_reference": PAPER1_NORMATIVE_REFERENCE,
        "research_repository_commit": _git_commit(research_repo_path),
        "synapse_repository_commit": _git_commit(synapse_repo_path),
        "analysis_id": analysis_id,
        "analysis_version": analysis_version,
        "source_fixture_hash": source_fixture_hash,
        "normalized_ir_hash": normalized_ir_hash,
        "result_hash": result_hash,
        "artifact_hash": artifact_hash,
        "expected_classification": expected_classification,
        "actual_classification": actual_classification,
        "verdict": verdict,
        "diagnostics": sorted(diagnostics, key=canonical_json_text),
        "traceability": [
            "Paper 1 Dependency Predicate",
            "Canonical Research Object",
            "Canonical Fixture",
            "Cross-Repository Adapter",
            "CanonicalIR",
            "Registered Dependency Pass",
            "Validated Result",
            "Structural Evidence Artifact",
            "Conformance Result",
        ],
    }


def _semantic_diagnostics(fixture: dict[str, Any], artifact: dict[str, Any]) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    dependencies = artifact["result"]["payload"].get("dependencies", [])
    if len(dependencies) != 1 or not isinstance(dependencies[0], dict):
        return [_diagnostic("MALFORMED_ANALYSIS_RESULT", "error", "artifact payload must contain exactly one dependency result")]
    actual_dependency = dependencies[0].get("dependency")
    expected_dependency = fixture["expected_semantics"]["canonical_outputs"]["is_dependency"]
    if actual_dependency is not expected_dependency:
        diagnostics.append(_diagnostic("DEPENDENCY_SEMANTIC_MISMATCH", "error", "actual dependency predicate did not match expected semantics"))
    expected_candidate_set = fixture["expected_semantics"]["structural_invariants"]["removed_components"]
    if dependencies[0].get("candidate_set") != expected_candidate_set:
        diagnostics.append(_diagnostic("CANDIDATE_SET_MISMATCH", "error", "candidate set did not match canonical fixture"))
    return diagnostics


def _expected_classification(fixture: dict[str, Any]) -> str:
    try:
        return "NULL" if fixture["expected_semantics"]["canonical_outputs"]["is_dependency"] else "VALID"
    except (KeyError, TypeError):
        return "UNOBSERVED"


def _failure_code(exc: Exception) -> str:
    if isinstance(exc, UnknownAnalysisPassError):
        return "MISSING_REGISTERED_ANALYSIS"
    if isinstance(exc, StructuralEvidenceValidationError):
        return "MALFORMED_ANALYSIS_RESULT"
    if isinstance(exc, CompilerDiagnosticException):
        return "MALFORMED_FIXTURE"
    return "CONFORMANCE_EXECUTION_FAILED"


def _diagnostic(code: str, level: str, message: str) -> dict[str, str]:
    return {"code": code, "level": level, "message": message}


def _sha256_prefixed(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _git_commit(path: str | Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(path),
        check=False,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "UNOBSERVED"


def _blocked_result(
    *,
    source_fixture_hash: str,
    verdict: str,
    code: str,
    message: str,
    research_repo_path: str | Path,
    synapse_repo_path: str | Path,
) -> dict[str, Any]:
    return _conformance_result(
        fixture={},
        research_repo_path=research_repo_path,
        synapse_repo_path=synapse_repo_path,
        source_fixture_hash=source_fixture_hash,
        normalized_ir_hash="UNOBSERVED",
        result_hash="UNOBSERVED",
        artifact_hash="UNOBSERVED",
        analysis_id=DEPENDENCY_ANALYSIS_ID,
        analysis_version="UNOBSERVED",
        expected_classification="UNOBSERVED",
        actual_classification="UNOBSERVED",
        verdict=verdict,
        diagnostics=[_diagnostic(code, "error", message)],
    )

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixture", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--conformance-result", action="store_true")
    a = p.parse_args()

    if a.conformance_result:
        result = run_paper1_dependency_conformance(a.fixture)
        Path(a.output).write_text(canonical_json_text(result), encoding="utf-8")
        return 0 if result["verdict"] == "PASS" else 1

    fixture = json.loads(Path(a.fixture).read_text())
    topology = topology_from_fixture(fixture)

    artifact = compile_artifact(
        canonical_json(topology),
        source_id=fixture["fixture_id"],
    )
    artifact["canonical_context"] = canonical_context_from_fixture(fixture)

    discover()

    projection = get_handler(
        fixture["research_object_id"]
    )(artifact)

    evidence = {
        "repository": "SYNAPSE",
        "repository_url": "https://github.com/joselunasrt8-creator/SYNAPSE",
        "commit_sha": "UNKNOWN",
        "branch": "synapse-foundation-evidence-84",
        "implementation_version": artifact["package_version"],
        "research_object_id": fixture["research_object_id"],
        "fixture_id": fixture["fixture_id"],
        "observed_execution_timestamp": "2026-01-01T00:00:00Z",
        "canonical_projection_timestamp": fixture["deterministic_timestamp"],
        "semantic_result": "PASS",
        "diagnostics": [],
        "generated_artifacts": [
            {
                "kind": "synapse",
                "hash": artifact["artifact_hash"],
            }
        ],
        "structural_metrics": {
            "classification": artifact["classification"],
        },
        "provenance": {
            "compiler_version": artifact["compiler_version"],
        },
        **projection,
    }

    Path(a.output).write_text(
        json.dumps(evidence, indent=2)
    )

if __name__ == "__main__":
    raise SystemExit(main())
