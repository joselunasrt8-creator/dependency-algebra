import json
import subprocess
import sys
from pathlib import Path

import pytest

from conformance.foundation_adapter import canonical_context_from_fixture, canonical_json, topology_from_fixture
from conformance.research_objects.reachability_profile import _verify_invariants, reachability_profile_projection
from conformance.research_objects.registry import get_handler
from dependency_algebra import compile_artifact


RESEARCH_OBJECT_ID = "concept.structural-observation.reachability-profile"


def canonical_fixture():
    return {
        "fixture_id": "canonical-reachability-profile",
        "research_object_id": RESEARCH_OBJECT_ID,
        "deterministic_timestamp": "2026-01-01T00:00:00Z",
        "input": {
            "structural_object": {
                "nodes": ["target-b", "root-b", "target-a", "root-a"],
                "relations": [
                    {"from": "root-b", "to": "target-b"},
                    {"from": "root-a", "to": "target-a"},
                ],
            },
            "workload": {
                "roots": ["root-b", "root-a"],
                "targets": ["target-b", "target-a"],
            },
        },
        "expected_semantics": {
            "reachable_pairs": [
                {"root": "root-a", "target": "target-a"},
                {"root": "root-b", "target": "target-b"},
            ],
            "unreachable_pairs": [
                {"root": "root-a", "target": "target-b"},
                {"root": "root-b", "target": "target-a"},
            ],
            "reachability_density": 0.5,
        },
    }


def projection_for(fixture):
    topology = topology_from_fixture(fixture)
    artifact = compile_artifact(canonical_json(topology), source_id=fixture["fixture_id"])
    artifact["canonical_context"] = canonical_context_from_fixture(fixture)
    return reachability_profile_projection(artifact)


def test_reachability_profile_canonical_fixture_semantics():
    projection = projection_for(canonical_fixture())
    outputs = projection["canonical_outputs"]

    assert outputs["reachable_pairs"] == canonical_fixture()["expected_semantics"]["reachable_pairs"]
    assert outputs["unreachable_pairs"] == canonical_fixture()["expected_semantics"]["unreachable_pairs"]
    assert outputs["root_coverage"] == [
        {"root": "root-a", "reachable_target_count": 1, "unreachable_target_count": 1, "target_count": 2},
        {"root": "root-b", "reachable_target_count": 1, "unreachable_target_count": 1, "target_count": 2},
    ]
    assert outputs["target_coverage"] == [
        {"target": "target-a", "reachable_root_count": 1, "unreachable_root_count": 1, "root_count": 2},
        {"target": "target-b", "reachable_root_count": 1, "unreachable_root_count": 1, "root_count": 2},
    ]
    assert outputs["reachability_density"] == 0.5
    assert projection["structural_metrics"]["reachable_pair_count"] == 2
    assert projection["structural_metrics"]["unreachable_pair_count"] == 2
    assert all(projection["structural_invariants"].values())


def test_reachability_profile_handler_is_discoverable():
    assert get_handler(RESEARCH_OBJECT_ID) is reachability_profile_projection


def test_malformed_root_or_target_references_fail_deterministically():
    fixture = canonical_fixture()
    fixture["input"]["workload"]["roots"] = ["missing-root"]
    with pytest.raises(Exception) as excinfo:
        projection_for(fixture)
    assert "UNRESOLVED_WORKLOAD_ROOT" in str(excinfo.value)


def test_incomplete_pair_classification_fails_invariant_verification():
    with pytest.raises(ValueError, match="every_root_target_pair_classified"):
        _verify_invariants(
            ("root-a",),
            ("target-a", "target-b"),
            [{"root": "root-a", "target": "target-a"}],
            [],
            [{"root": "root-a", "reachable_target_count": 1, "unreachable_target_count": 0, "target_count": 2}],
            [
                {"target": "target-a", "reachable_root_count": 1, "unreachable_root_count": 0, "root_count": 1},
                {"target": "target-b", "reachable_root_count": 0, "unreachable_root_count": 0, "root_count": 1},
            ],
            0.5,
        )


def test_non_canonical_ordering_is_normalized():
    projection = projection_for(canonical_fixture())
    outputs = projection["canonical_outputs"]
    assert outputs["nodes"] == ["root-a", "root-b", "target-a", "target-b"]
    assert outputs["roots"] == ["root-a", "root-b"]
    assert outputs["targets"] == ["target-a", "target-b"]
    assert [item["code"] for item in projection["required_diagnostics"]] == [
        "REACHABILITY_PROFILE_EVALUATED",
        "REACHABILITY_INVARIANTS_VERIFIED",
        "CANONICAL_ORDERING_CONFIRMED",
    ]


def test_replay_produces_identical_semantic_output():
    first = projection_for(canonical_fixture())
    second = projection_for(canonical_fixture())
    assert first == second


def test_adapter_emits_valid_canonical_evidence_envelope_and_conformance_pass(tmp_path):
    fixture_path = tmp_path / "fixture.json"
    out_path = tmp_path / "evidence.json"
    fixture_path.write_text(json.dumps(canonical_fixture()))

    subprocess.run(
        [sys.executable, "conformance/foundation_adapter.py", "--fixture", str(fixture_path), "--output", str(out_path)],
        check=True,
    )
    evidence = json.loads(out_path.read_text())

    assert evidence["semantic_result"] == "PASS"
    assert evidence["research_object_id"] == RESEARCH_OBJECT_ID
    assert evidence["canonical_outputs"]["reachable_pairs"] == canonical_fixture()["expected_semantics"]["reachable_pairs"]
    assert evidence["canonical_outputs"]["unreachable_pairs"] == canonical_fixture()["expected_semantics"]["unreachable_pairs"]
    assert evidence["structural_metrics"]["reachability_density"] == 0.5
    assert all(evidence["structural_invariants"].values())
    assert {item["code"] for item in evidence["required_diagnostics"]} == {
        "REACHABILITY_PROFILE_EVALUATED",
        "REACHABILITY_INVARIANTS_VERIFIED",
        "CANONICAL_ORDERING_CONFIRMED",
    }


def test_existing_dependency_predicate_projection_remains_available():
    assert get_handler("definition.dependency.dependency-predicate") is not None
