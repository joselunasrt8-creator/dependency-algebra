import dataclasses
import json
from pathlib import Path

import pytest

from dependency_algebra.analysis import DependencyAnalysisPass
from dependency_algebra.analysis_registry import UnknownAnalysisPassError, core_analysis_registry
from dependency_algebra.diagnostics import CompilerDiagnosticException
from dependency_algebra.engine import _analyze_artifact_legacy
from dependency_algebra.evidence import StructuralEvidenceValidationError, structural_evidence_artifact, validate_analysis_result
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import CanonicalIR
from dependency_algebra.serialization import analysis_result_hash, analysis_result_to_dict, canonical_json_text

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "fixtures" / "representation_invariance"
GROUPS_PATH = FIXTURE_ROOT / "groups.json"
STAGES = ("PARSE", "VALIDATION", "NORMALIZATION", "CANONICAL_IR", "REGISTRY", "ANALYSIS", "RESULT_VALIDATION", "SERIALIZATION", "ARTIFACT")


class DivergenceAssertion(AssertionError):
    def __init__(self, report):
        self.report = report
        super().__init__(canonical_json_text(report))


def load_groups():
    data = json.loads(GROUPS_PATH.read_text(encoding="utf-8"))
    return sorted(data["groups"], key=lambda g: g["group_id"])


def run_pipeline(path, group, *, analysis_id=None, configuration=None, expected_ir_hash=None, expected_result_hash=None):
    source = (FIXTURE_ROOT / path).read_text(encoding="utf-8")
    source_id = group["semantic_identity"]
    try:
        topology = parse_topology(source, source_id)
    except CompilerDiagnosticException as exc:
        return {"stage": "PARSE", "diagnostics": exc.diagnostic}
    try:
        ir_dict = validate_and_normalize(topology, source_id)
    except CompilerDiagnosticException as exc:
        return {"stage": "VALIDATION", "diagnostics": exc.diagnostic}
    if expected_ir_hash and ir_dict["normalized_ir_hash"] != expected_ir_hash:
        return {"stage": "RESULT_VALIDATION", "expected": expected_ir_hash, "actual": ir_dict["normalized_ir_hash"], "field": "normalized_ir_hash"}
    ir = CanonicalIR.from_dict(ir_dict)
    try:
        analysis_pass = core_analysis_registry().get(analysis_id or group["analysis_id"])
    except UnknownAnalysisPassError as exc:
        return {"stage": "REGISTRY", "diagnostics": str(exc)}
    try:
        configured_pass = analysis_pass.with_configuration(**(configuration if configuration is not None else group.get("configuration", {})))
    except (TypeError, ValueError) as exc:
        return {"stage": "REGISTRY", "diagnostics": str(exc)}
    result = configured_pass.execute(ir)
    try:
        validate_analysis_result(configured_pass.metadata, ir, result, result_hash=expected_result_hash or analysis_result_hash(result))
    except StructuralEvidenceValidationError as exc:
        return {"stage": "RESULT_VALIDATION", "diagnostics": str(exc)}
    result_payload = analysis_result_to_dict(result)
    artifact = structural_evidence_artifact(
        analysis_pass=configured_pass,
        canonical_ir=ir,
        source_topology_hash=ir.normalized_ir_hash,
        result=result,
    )
    legacy = _analyze_artifact_legacy(ir)
    return {
        "stage": "ARTIFACT",
        "ir_dict": ir_dict,
        "canonical_ir": {
            "normalized_ir_hash": ir.normalized_ir_hash,
            "components": list(ir.components),
            "adjacency": {k: [edge.to_dict() for edge in v] for k, v in ir.adjacency.items()},
            "workloads": [dataclasses.asdict(w) for w in ir.workloads],
            "serialization": canonical_json_text(ir_dict),
        },
        "analysis": {
            "classification": result.classification,
            "dependencies": result_payload["dependencies"],
            "reachability": result_payload["reachability"],
            "serialization": canonical_json_text(result_payload),
            "result_hash": analysis_result_hash(result),
        },
        "artifact": {
            "analysis_id": artifact["analysis"]["analysis_id"],
            "analysis_version": artifact["analysis"]["analysis_version"],
            "deterministic_configuration": artifact["analysis"]["deterministic_configuration"],
            "accepted_input": artifact["analysis"]["accepted_input"],
            "output_contract_identity": artifact["analysis"]["output_contract_identity"],
            "specification_references": artifact["analysis"]["specification_references"],
            "normalized_ir_hash": artifact["input"]["normalized_ir_hash"],
            "result_hash": artifact["result"]["result_hash"],
            "serialization": canonical_json_text(artifact),
            "artifact_hash": artifact["artifact_hash"],
        },
        "legacy": canonical_json_text(analysis_result_to_dict(legacy)),
    }


def assert_no_divergence(group, baseline_path, variant_path, baseline, variant):
    for stage in STAGES:
        if baseline.get("stage") != variant.get("stage"):
            raise DivergenceAssertion({"group_id": group["group_id"], "baseline": baseline_path, "variant": variant_path, "earliest_stage": stage, "expected": baseline.get("stage"), "actual": variant.get("stage"), "fixture_path": str(GROUPS_PATH.relative_to(ROOT))})
        if stage == "CANONICAL_IR" and baseline["canonical_ir"] != variant["canonical_ir"]:
            raise DivergenceAssertion({"group_id": group["group_id"], "baseline": baseline_path, "variant": variant_path, "earliest_stage": stage, "expected": baseline["canonical_ir"], "actual": variant["canonical_ir"], "fixture_path": str(GROUPS_PATH.relative_to(ROOT))})
        if stage == "ANALYSIS" and baseline["analysis"] != variant["analysis"]:
            raise DivergenceAssertion({"group_id": group["group_id"], "baseline": baseline_path, "variant": variant_path, "earliest_stage": stage, "expected": baseline["analysis"], "actual": variant["analysis"], "fixture_path": str(GROUPS_PATH.relative_to(ROOT))})
        if stage == "ARTIFACT" and baseline["artifact"] != variant["artifact"]:
            raise DivergenceAssertion({"group_id": group["group_id"], "baseline": baseline_path, "variant": variant_path, "earliest_stage": stage, "expected": baseline["artifact"], "actual": variant["artifact"], "fixture_path": str(GROUPS_PATH.relative_to(ROOT))})


@pytest.mark.parametrize("group", load_groups())
def test_valid_equivalence_groups_are_invariant_and_repeat_byte_identically(group):
    paths = sorted(group["representations"])
    baseline_path = group["baseline"]
    baseline = run_pipeline(baseline_path, group)
    repeated = run_pipeline(baseline_path, group)
    assert canonical_json_text(baseline) == canonical_json_text(repeated)
    assert baseline["canonical_ir"]["normalized_ir_hash"] == group["expected"]["normalized_ir_hash"]
    assert baseline["analysis"]["result_hash"] == group["expected"]["result_hash"]
    assert baseline["artifact"]["artifact_hash"] == group["expected"]["artifact_hash"]
    assert baseline["analysis"]["serialization"] == baseline["legacy"]
    for variant_path in paths:
        variant_first = run_pipeline(variant_path, group)
        variant_second = run_pipeline(variant_path, group)
        assert canonical_json_text(variant_first) == canonical_json_text(variant_second)
        assert_no_divergence(group, baseline_path, variant_path, baseline, variant_first)


def test_fixture_discovery_order_does_not_change_results():
    groups = load_groups()
    forward = [run_pipeline(g["baseline"], g)["artifact"]["serialization"] for g in groups]
    reverse = [run_pipeline(g["baseline"], g)["artifact"]["serialization"] for g in reversed(groups)]
    assert sorted(forward) == sorted(reverse)


def test_negative_groups_fail_or_produce_distinct_identity_deterministically():
    baseline_group = next(g for g in load_groups() if g["group_id"] == "json-field-order-equivalence")
    baseline = run_pipeline(baseline_group["baseline"], baseline_group)
    for case in sorted(json.loads((FIXTURE_ROOT / "negative_groups.json").read_text(encoding="utf-8"))["groups"], key=lambda g: g["group_id"]):
        first = run_pipeline(case["representation"], baseline_group, analysis_id=case.get("analysis_id"), expected_ir_hash=case.get("expected_normalized_ir_hash"), configuration=case.get("configuration"), expected_result_hash=case.get("expected_result_hash"))
        second = run_pipeline(case["representation"], baseline_group, analysis_id=case.get("analysis_id"), expected_ir_hash=case.get("expected_normalized_ir_hash"), configuration=case.get("configuration"), expected_result_hash=case.get("expected_result_hash"))
        assert canonical_json_text(first) == canonical_json_text(second)
        if case["expected"]["outcome"] == "DISTINCT":
            assert first["canonical_ir"]["normalized_ir_hash"] != baseline["canonical_ir"]["normalized_ir_hash"] or first["analysis"]["result_hash"] != baseline["analysis"]["result_hash"]
        else:
            assert first["stage"] == case["expected"]["stage"]


def test_divergence_report_identifies_group_fixture_and_stage():
    group = next(g for g in load_groups() if g["group_id"] == "edge-order-equivalence")
    baseline = run_pipeline(group["baseline"], group)
    variant = run_pipeline("negative/semantically-distinct-edge-change.json", group)
    with pytest.raises(DivergenceAssertion) as excinfo:
        assert_no_divergence(group, group["baseline"], "negative/semantically-distinct-edge-change.json", baseline, variant)
    report = excinfo.value.report
    assert report["group_id"] == group["group_id"]
    assert report["fixture_path"] == "fixtures/representation_invariance/groups.json"
    assert report["earliest_stage"] in STAGES
    assert canonical_json_text(report) == canonical_json_text(excinfo.value.report)
