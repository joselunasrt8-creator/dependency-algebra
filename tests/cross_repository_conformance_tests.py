import copy
import json
from pathlib import Path

import pytest

from conformance import foundation_adapter
from conformance.foundation_adapter import (
    PAPER1_DEPENDENCY_FIXTURE_ID,
    PAPER1_DEPENDENCY_RESEARCH_OBJECT_ID,
    RESEARCH_ROOT,
    run_paper1_dependency_conformance,
    _paper1_topology_from_fixture,
)
from dependency_algebra.evidence import compile_structural_evidence_artifact
from dependency_algebra.serialization import canonical_json_bytes, canonical_json_text

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = RESEARCH_ROOT / "conformance" / "fixtures" / "dependency-predicate.fixture.json"


def _fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _write_fixture(tmp_path, fixture):
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(fixture, sort_keys=True), encoding="utf-8")
    return path


def test_paper1_dependency_fixture_crosses_registered_synapse_path():
    result = run_paper1_dependency_conformance(FIXTURE_PATH)

    assert result["conformance_case_id"] == "paper1-dependency-predicate-basic-v1-to-synapse-dependency-analysis"
    assert result["research_object_id"] == PAPER1_DEPENDENCY_RESEARCH_OBJECT_ID
    assert result["fixture_id"] == PAPER1_DEPENDENCY_FIXTURE_ID
    assert result["analysis_id"] == "dependency-algebra.dependency-analysis"
    assert result["analysis_version"] == "1"
    assert result["expected_classification"] == "NULL"
    assert result["actual_classification"] == "NULL"
    assert result["verdict"] == "PASS"
    assert all(result[field].startswith("sha256:") for field in ("source_fixture_hash", "normalized_ir_hash", "result_hash", "artifact_hash"))
    assert [item["code"] for item in result["diagnostics"]] == ["CONFORMANCE_PASS"]
    assert result["traceability"] == [
        "Paper 1 Dependency Predicate",
        "Canonical Research Object",
        "Canonical Fixture",
        "Cross-Repository Adapter",
        "CanonicalIR",
        "Registered Dependency Pass",
        "Validated Result",
        "Structural Evidence Artifact",
        "Conformance Result",
    ]


def test_adapter_preserves_fixture_edge_order_before_synapse_normalization():
    topology = _paper1_topology_from_fixture(_fixture())
    assert topology["edges"] == [
        {"id": "e0", "from": "r", "to": "a"},
        {"id": "e1", "from": "a", "to": "b"},
        {"id": "e2", "from": "b", "to": "t"},
    ]


def test_repeated_focused_conformance_suite_is_byte_identical():
    first = canonical_json_bytes(run_paper1_dependency_conformance(FIXTURE_PATH))
    second = canonical_json_bytes(run_paper1_dependency_conformance(FIXTURE_PATH))
    assert first == second


def test_unknown_research_object_fails_deterministically(tmp_path):
    fixture = _fixture()
    fixture["research_object_id"] = "definition.unknown"
    result = run_paper1_dependency_conformance(_write_fixture(tmp_path, fixture))
    assert result["verdict"] == "NOT_APPLICABLE"
    assert result["diagnostics"][0]["code"] == "UNKNOWN_RESEARCH_OBJECT"


def test_unsupported_fixture_version_fails_deterministically(tmp_path):
    fixture = _fixture()
    fixture["fixture_id"] = "paper1.dependency-predicate.basic-v2"
    result = run_paper1_dependency_conformance(_write_fixture(tmp_path, fixture))
    assert result["verdict"] == "NOT_APPLICABLE"
    assert result["diagnostics"][0]["code"] == "UNSUPPORTED_FIXTURE_VERSION"


def test_malformed_fixture_fails_deterministically(tmp_path):
    fixture = _fixture()
    del fixture["input"]["workload"]["candidate_component_set"]
    result = run_paper1_dependency_conformance(_write_fixture(tmp_path, fixture))
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "MALFORMED_FIXTURE"


def test_missing_normative_reference_fails_deterministically(tmp_path):
    fixture = _fixture()
    del fixture["research_object_path"]
    result = run_paper1_dependency_conformance(_write_fixture(tmp_path, fixture))
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "MISSING_NORMATIVE_REFERENCE"


def test_missing_registered_analysis_fails_deterministically():
    result = run_paper1_dependency_conformance(FIXTURE_PATH, analysis_id="missing.analysis")
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "MISSING_REGISTERED_ANALYSIS"


def test_source_hash_mismatch_fails_deterministically():
    result = run_paper1_dependency_conformance(FIXTURE_PATH, expected_source_fixture_hash="sha256:" + "0" * 64)
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "SOURCE_HASH_MISMATCH"


def test_normalized_ir_hash_mismatch_fails_deterministically():
    result = run_paper1_dependency_conformance(FIXTURE_PATH, expected_normalized_ir_hash="sha256:" + "0" * 64)
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "NORMALIZED_IR_HASH_MISMATCH"


def test_malformed_analysis_result_fails_deterministically(monkeypatch):
    def fail_validation(*args, **kwargs):
        raise foundation_adapter.StructuralEvidenceValidationError("analysis result hash mismatch")

    monkeypatch.setattr(foundation_adapter, "compile_structural_evidence_artifact", fail_validation)
    result = run_paper1_dependency_conformance(FIXTURE_PATH)
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "MALFORMED_ANALYSIS_RESULT"


def test_expected_classification_mismatch_fails_deterministically(tmp_path):
    fixture = _fixture()
    fixture["expected_semantics"]["canonical_outputs"]["is_dependency"] = False
    result = run_paper1_dependency_conformance(_write_fixture(tmp_path, fixture))
    assert result["verdict"] == "FAIL"
    assert {item["code"] for item in result["diagnostics"]} >= {
        "DEPENDENCY_SEMANTIC_MISMATCH",
        "EXPECTED_CLASSIFICATION_MISMATCH",
    }


def test_repeated_run_divergence_fails_deterministically():
    fixture = _fixture()
    topology = _paper1_topology_from_fixture(fixture)
    artifact = compile_structural_evidence_artifact(canonical_json_text(topology), source_id=fixture["fixture_id"])
    divergent = copy.deepcopy(artifact)
    divergent["diagnostics"] = [{"code": "DIVERGED"}]
    result = run_paper1_dependency_conformance(FIXTURE_PATH, second_artifact_override=divergent)
    assert result["verdict"] == "FAIL"
    assert result["diagnostics"][0]["code"] == "REPEATED_RUN_DIVERGENCE"


@pytest.mark.parametrize(
    "mutate,expected_code",
    [
        (lambda fixture: fixture.update({"research_object_id": "definition.unknown"}), "UNKNOWN_RESEARCH_OBJECT"),
        (lambda fixture: fixture.update({"fixture_id": "paper1.dependency-predicate.basic-v2"}), "UNSUPPORTED_FIXTURE_VERSION"),
        (lambda fixture: fixture["input"]["graph"].pop("nodes"), "MALFORMED_FIXTURE"),
    ],
)
def test_negative_outputs_are_byte_identical(tmp_path, mutate, expected_code):
    fixture = _fixture()
    mutate(fixture)
    path = _write_fixture(tmp_path, fixture)
    first = canonical_json_bytes(run_paper1_dependency_conformance(path))
    second = canonical_json_bytes(run_paper1_dependency_conformance(path))
    assert first == second
    assert expected_code.encode("utf-8") in first
