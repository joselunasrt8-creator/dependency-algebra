import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from dependency_algebra.analysis import DependencyAnalysisPass
from dependency_algebra.analysis_registry import UnknownAnalysisPassError, core_analysis_registry
from dependency_algebra.diagnostics import CompilerDiagnosticException
from dependency_algebra.engine import _analyze_artifact_legacy
from dependency_algebra.evidence import StructuralEvidenceValidationError, compile_structural_evidence_artifact, validate_analysis_result
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import CanonicalIR
from dependency_algebra.serialization import analysis_result_hash, analysis_result_to_dict, canonical_json_text, sha256_bytes

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "representation_invariance"
GROUPS_PATH = FIXTURE_ROOT / "groups.json"
NEGATIVE_GROUPS_PATH = FIXTURE_ROOT / "negative_groups.json"
STAGES = ("PARSE", "VALIDATION", "NORMALIZATION", "CANONICAL_IR", "REGISTRY", "ANALYSIS", "RESULT_VALIDATION", "SERIALIZATION", "ARTIFACT")
SEMANTIC_ARTIFACT_FIELDS = ("analysis", "input_normalized_ir_hash", "result_hash", "result_payload", "diagnostics")
PROVENANCE_ARTIFACT_FIELDS = ("source_topology_hash", "artifact_hash", "serialization")


class DivergenceAssertion(AssertionError):
    def __init__(self, report: dict[str, Any]):
        self.report = report
        super().__init__(canonical_json_text(report))


def load_groups() -> list[dict[str, Any]]:
    data = json.loads(GROUPS_PATH.read_text(encoding="utf-8"))
    return sorted(data["groups"], key=lambda g: g["group_id"])


def run_pipeline(path: str, group: dict[str, Any], *, analysis_id: str | None = None, configuration: dict[str, Any] | None = None, expected_ir_hash: str | None = None, expected_result_hash: str | None = None) -> dict[str, Any]:
    fixture_path = FIXTURE_ROOT / path
    source = fixture_path.read_text(encoding="utf-8")
    source_bytes = source.encode("utf-8")
    source_id = group["semantic_identity"]
    snapshots: dict[str, Any] = {}

    try:
        topology = parse_topology(source, source_id)
    except CompilerDiagnosticException as exc:
        return _terminated(path, "PARSE", snapshots, exc.diagnostic)
    snapshots["PARSE"] = {"document_type": type(topology).__name__}

    try:
        ir_dict = validate_and_normalize(topology, source_id)
    except CompilerDiagnosticException as exc:
        return _terminated(path, "VALIDATION", snapshots, exc.diagnostic)
    snapshots["VALIDATION"] = "VALID"
    snapshots["NORMALIZATION"] = {"normalized_ir_hash": ir_dict["normalized_ir_hash"], "serialization": canonical_json_text(ir_dict)}
    if expected_ir_hash and ir_dict["normalized_ir_hash"] != expected_ir_hash:
        return _terminated(path, "NORMALIZATION", snapshots, {"expected": expected_ir_hash, "actual": ir_dict["normalized_ir_hash"], "field": "normalized_ir_hash"})

    ir = CanonicalIR.from_dict(ir_dict)
    snapshots["CANONICAL_IR"] = {
        "normalized_ir_hash": ir.normalized_ir_hash,
        "components": list(ir.components),
        "adjacency": {key: [edge.to_dict() for edge in edges] for key, edges in ir.adjacency.items()},
        "workloads": [dataclasses.asdict(workload) for workload in ir.workloads],
    }

    try:
        analysis_pass = core_analysis_registry().get(analysis_id or group["analysis_id"])
    except UnknownAnalysisPassError as exc:
        return _terminated(path, "REGISTRY", snapshots, str(exc))
    try:
        configured_pass = analysis_pass.with_configuration(**(configuration if configuration is not None else group.get("configuration", {})))
    except (TypeError, ValueError) as exc:
        return _terminated(path, "REGISTRY", snapshots, str(exc))
    snapshots["REGISTRY"] = {
        "analysis_id": configured_pass.analysis_id,
        "analysis_version": configured_pass.analysis_version,
        "accepted_input": configured_pass.accepted_input,
        "deterministic_configuration": dict(configured_pass.deterministic_configuration),
        "specification_references": list(configured_pass.specification_references),
        "output_contract_identity": configured_pass.output_contract_identity,
    }

    result = configured_pass.execute(ir)
    result_payload = analysis_result_to_dict(result)
    snapshots["ANALYSIS"] = {
        "classification": result.classification,
        "dependencies": result_payload["dependencies"],
        "reachability": result_payload["reachability"],
        "result_hash": analysis_result_hash(result),
    }

    try:
        validation = validate_analysis_result(configured_pass.metadata, ir, result, result_hash=expected_result_hash or analysis_result_hash(result))
    except StructuralEvidenceValidationError as exc:
        return _terminated(path, "RESULT_VALIDATION", snapshots, str(exc))
    snapshots["RESULT_VALIDATION"] = validation
    snapshots["SERIALIZATION"] = {"analysis_result": canonical_json_text(result_payload), "legacy_analysis_result": canonical_json_text(analysis_result_to_dict(_analyze_artifact_legacy(ir)))}

    artifact = compile_structural_evidence_artifact(source_bytes, source_id=source_id, analysis_id=analysis_id or group["analysis_id"], max_depth=(configuration or group.get("configuration", {})).get("max_depth"))
    snapshots["ARTIFACT"] = {
        "semantic": {
            "analysis": artifact["analysis"],
            "input_normalized_ir_hash": artifact["input"]["normalized_ir_hash"],
            "result_hash": artifact["result"]["result_hash"],
            "result_payload": artifact["result"]["payload"],
            "diagnostics": artifact["diagnostics"],
        },
        "provenance": {
            "source_topology_hash": artifact["input"]["source_topology_hash"],
            "artifact_hash": artifact["artifact_hash"],
            "serialization": canonical_json_text(artifact),
        },
        "expected_source_topology_hash": sha256_bytes(source_bytes),
    }
    return {"fixture": path, "terminated_stage": "ARTIFACT", "snapshots": snapshots}


def _terminated(path: str, stage: str, snapshots: dict[str, Any], detail: Any) -> dict[str, Any]:
    snapshots[stage] = {"terminated": True, "detail": detail}
    return {"fixture": path, "terminated_stage": stage, "snapshots": snapshots}


def assert_no_semantic_divergence(group: dict[str, Any], baseline_path: str, variant_path: str, baseline: dict[str, Any], variant: dict[str, Any]) -> None:
    report = first_semantic_divergence(group, baseline_path, variant_path, baseline, variant)
    if report is not None:
        raise DivergenceAssertion(report)


def first_semantic_divergence(group: dict[str, Any], baseline_path: str, variant_path: str, baseline: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any] | None:
    baseline_snapshots = baseline["snapshots"]
    variant_snapshots = variant["snapshots"]
    for stage in STAGES:
        expected = baseline_snapshots.get(stage)
        actual = variant_snapshots.get(stage)
        if stage == "ARTIFACT" and expected is not None and actual is not None:
            expected = expected["semantic"]
            actual = actual["semantic"]
        if baseline["terminated_stage"] == stage or variant["terminated_stage"] == stage:
            if baseline["terminated_stage"] != variant["terminated_stage"] or expected != actual:
                return _divergence_report(group, baseline_path, variant_path, stage, expected, actual)
            return None
        if expected != actual:
            return _divergence_report(group, baseline_path, variant_path, stage, expected, actual)
    return None


def _divergence_report(group: dict[str, Any], baseline_path: str, variant_path: str, stage: str, expected: Any, actual: Any) -> dict[str, Any]:
    return {
        "group_id": group["group_id"],
        "baseline": baseline_path,
        "variant": variant_path,
        "earliest_stage": stage,
        "expected": expected,
        "actual": actual,
        "fixture_path": str(GROUPS_PATH.relative_to(ROOT)),
    }


@pytest.mark.parametrize("group", load_groups())
def test_valid_equivalence_groups_are_semantically_invariant_and_repeat_byte_identically(group: dict[str, Any]) -> None:
    paths = sorted(group["representations"])
    baseline_path = group["baseline"]
    baseline = run_pipeline(baseline_path, group)
    repeated = run_pipeline(baseline_path, group)
    assert canonical_json_text(baseline) == canonical_json_text(repeated)
    assert baseline["snapshots"]["CANONICAL_IR"]["normalized_ir_hash"] == group["expected"]["normalized_ir_hash"]
    assert baseline["snapshots"]["ANALYSIS"]["result_hash"] == group["expected"]["result_hash"]
    assert baseline["snapshots"]["ANALYSIS"]["classification"] == group["expected"]["classification"]
    assert baseline["snapshots"]["SERIALIZATION"]["analysis_result"] == baseline["snapshots"]["SERIALIZATION"]["legacy_analysis_result"]
    assert baseline["snapshots"]["ARTIFACT"]["expected_source_topology_hash"] == baseline["snapshots"]["ARTIFACT"]["provenance"]["source_topology_hash"]

    for variant_path in paths:
        variant_first = run_pipeline(variant_path, group)
        variant_second = run_pipeline(variant_path, group)
        assert canonical_json_text(variant_first) == canonical_json_text(variant_second)
        assert_no_semantic_divergence(group, baseline_path, variant_path, baseline, variant_first)
        assert variant_first["snapshots"]["SERIALIZATION"]["analysis_result"] == variant_first["snapshots"]["SERIALIZATION"]["legacy_analysis_result"]
        assert variant_first["snapshots"]["ARTIFACT"]["expected_source_topology_hash"] == variant_first["snapshots"]["ARTIFACT"]["provenance"]["source_topology_hash"]
        if variant_path != baseline_path and (FIXTURE_ROOT / variant_path).read_bytes() != (FIXTURE_ROOT / baseline_path).read_bytes():
            assert variant_first["snapshots"]["ARTIFACT"]["provenance"] != baseline["snapshots"]["ARTIFACT"]["provenance"]


def test_fixture_discovery_order_does_not_change_semantic_results() -> None:
    groups = load_groups()
    forward = [run_pipeline(g["baseline"], g)["snapshots"]["ARTIFACT"]["semantic"] for g in groups]
    reverse = [run_pipeline(g["baseline"], g)["snapshots"]["ARTIFACT"]["semantic"] for g in reversed(groups)]
    assert sorted(canonical_json_text(item) for item in forward) == sorted(canonical_json_text(item) for item in reverse)


def test_negative_groups_fail_or_produce_distinct_identity_deterministically() -> None:
    baseline_group = next(g for g in load_groups() if g["group_id"] == "json-field-order-equivalence")
    baseline = run_pipeline(baseline_group["baseline"], baseline_group)
    cases = sorted(json.loads(NEGATIVE_GROUPS_PATH.read_text(encoding="utf-8"))["groups"], key=lambda g: g["group_id"])
    for case in cases:
        first = run_pipeline(case["representation"], baseline_group, analysis_id=case.get("analysis_id"), configuration=case.get("configuration"), expected_ir_hash=case.get("expected_normalized_ir_hash"), expected_result_hash=case.get("expected_result_hash"))
        second = run_pipeline(case["representation"], baseline_group, analysis_id=case.get("analysis_id"), configuration=case.get("configuration"), expected_ir_hash=case.get("expected_normalized_ir_hash"), expected_result_hash=case.get("expected_result_hash"))
        assert canonical_json_text(first) == canonical_json_text(second)
        if case["expected"]["outcome"] == "DISTINCT":
            assert first_semantic_divergence(baseline_group, baseline_group["baseline"], case["representation"], baseline, first) is not None
        else:
            assert first["terminated_stage"] == case["expected"]["stage"]


@pytest.mark.parametrize("bad_max_depth", [-1, True, "1"])
def test_dependency_pass_rejects_malformed_configuration_before_execution(bad_max_depth: Any) -> None:
    with pytest.raises(ValueError):
        DependencyAnalysisPass().with_configuration(max_depth=bad_max_depth)


@pytest.mark.parametrize("valid_max_depth", [None, 0, 3])
def test_dependency_pass_accepts_valid_configuration(valid_max_depth: int | None) -> None:
    configured = DependencyAnalysisPass().with_configuration(max_depth=valid_max_depth)
    assert configured.max_depth == valid_max_depth


def test_divergence_report_identifies_real_earliest_stage_and_fixture_identity() -> None:
    group = next(g for g in load_groups() if g["group_id"] == "edge-order-equivalence")
    baseline = run_pipeline(group["baseline"], group)
    variant = run_pipeline("negative/semantically-distinct-edge-change.json", group)
    with pytest.raises(DivergenceAssertion) as excinfo:
        assert_no_semantic_divergence(group, group["baseline"], "negative/semantically-distinct-edge-change.json", baseline, variant)
    report = excinfo.value.report
    assert report["group_id"] == group["group_id"]
    assert report["fixture_path"] == "fixtures/representation_invariance/groups.json"
    assert report["earliest_stage"] == "NORMALIZATION"
    assert canonical_json_text(report) == canonical_json_text(excinfo.value.report)
