import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from conformance import foundation_adapter
from conformance.foundation_adapter import (
    PAPER1_DEPENDENCY_FIXTURE_ID,
    PAPER1_DEPENDENCY_RESEARCH_OBJECT_ID,
    PAPER1_NORMALIZED_IR_HASH,
    PAPER1_SOURCE_FIXTURE_HASH,
    RESEARCH_ROOT,
    run_paper1_dependency_conformance,
    _paper1_topology_from_fixture,
)
from dependency_algebra.evidence import compile_structural_evidence_artifact
from dependency_algebra.serialization import canonical_json_bytes, canonical_json_text

FIXTURE_PATH = RESEARCH_ROOT / "conformance" / "fixtures" / "dependency-predicate.fixture.json"


def _fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class Paper1CrossRepositoryConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not FIXTURE_PATH.is_file():
            raise unittest.SkipTest(f"canonical Paper 1 fixture is unavailable: {FIXTURE_PATH}")

    def _write_fixture(self, fixture):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with handle:
            json.dump(fixture, handle, sort_keys=True)
        return Path(handle.name)

    def test_paper1_dependency_fixture_crosses_registered_synapse_path(self):
        result = run_paper1_dependency_conformance(FIXTURE_PATH)

        self.assertEqual(result["conformance_case_id"], "paper1-dependency-predicate-basic-v1-to-synapse-dependency-analysis")
        self.assertEqual(result["research_object_id"], PAPER1_DEPENDENCY_RESEARCH_OBJECT_ID)
        self.assertEqual(result["fixture_id"], PAPER1_DEPENDENCY_FIXTURE_ID)
        self.assertEqual(result["analysis_id"], "dependency-algebra.dependency-analysis")
        self.assertEqual(result["analysis_version"], "1")
        self.assertEqual(result["source_fixture_hash"], PAPER1_SOURCE_FIXTURE_HASH)
        self.assertEqual(result["normalized_ir_hash"], PAPER1_NORMALIZED_IR_HASH)
        self.assertEqual(result["expected_classification"], "NULL")
        self.assertEqual(result["actual_classification"], "NULL")
        self.assertEqual(result["verdict"], "PASS")
        self.assertTrue(all(result[field].startswith("sha256:") for field in ("result_hash", "artifact_hash")))
        self.assertEqual([item["code"] for item in result["diagnostics"]], ["CONFORMANCE_PASS"])
        self.assertEqual(
            result["traceability"],
            [
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
        )

    def test_adapter_preserves_fixture_edge_order_before_synapse_normalization(self):
        topology = _paper1_topology_from_fixture(_fixture())
        self.assertEqual(
            topology["edges"],
            [
                {"id": "e0", "from": "r", "to": "a"},
                {"id": "e1", "from": "a", "to": "b"},
                {"id": "e2", "from": "b", "to": "t"},
            ],
        )

    def test_repeated_focused_conformance_result_is_byte_identical(self):
        first = canonical_json_bytes(run_paper1_dependency_conformance(FIXTURE_PATH))
        second = canonical_json_bytes(run_paper1_dependency_conformance(FIXTURE_PATH))
        self.assertEqual(first, second)

    def test_unknown_research_object_fails_deterministically(self):
        fixture = _fixture()
        fixture["research_object_id"] = "definition.unknown"
        result = run_paper1_dependency_conformance(self._write_fixture(fixture))
        self.assertEqual(result["verdict"], "NOT_APPLICABLE")
        self.assertEqual(result["diagnostics"][0]["code"], "UNKNOWN_RESEARCH_OBJECT")

    def test_unsupported_fixture_version_fails_deterministically(self):
        fixture = _fixture()
        fixture["fixture_id"] = "paper1.dependency-predicate.basic-v2"
        result = run_paper1_dependency_conformance(self._write_fixture(fixture))
        self.assertEqual(result["verdict"], "NOT_APPLICABLE")
        self.assertEqual(result["diagnostics"][0]["code"], "UNSUPPORTED_FIXTURE_VERSION")

    def test_malformed_fixture_fails_deterministically(self):
        fixture = _fixture()
        del fixture["input"]["workload"]["candidate_component_set"]
        result = run_paper1_dependency_conformance(self._write_fixture(fixture))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "MALFORMED_FIXTURE")

    def test_multiple_targets_fail_deterministically(self):
        fixture = _fixture()
        fixture["input"]["workload"]["targets"].append("extra-target")
        result = run_paper1_dependency_conformance(self._write_fixture(fixture), expected_source_fixture_hash=None)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "MALFORMED_FIXTURE")

    def test_missing_removed_components_fails_deterministically(self):
        fixture = _fixture()
        del fixture["expected_semantics"]["structural_invariants"]["removed_components"]
        result = run_paper1_dependency_conformance(self._write_fixture(fixture), expected_source_fixture_hash=None)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "MALFORMED_FIXTURE")

    def test_missing_normative_reference_fails_deterministically(self):
        fixture = _fixture()
        del fixture["research_object_path"]
        result = run_paper1_dependency_conformance(self._write_fixture(fixture))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "MISSING_NORMATIVE_REFERENCE")

    def test_missing_registered_analysis_fails_deterministically(self):
        result = run_paper1_dependency_conformance(FIXTURE_PATH, analysis_id="missing.analysis")
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "MISSING_REGISTERED_ANALYSIS")

    def test_source_hash_mismatch_fails_deterministically(self):
        result = run_paper1_dependency_conformance(FIXTURE_PATH, expected_source_fixture_hash="sha256:" + "0" * 64)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "SOURCE_HASH_MISMATCH")

    def test_normalized_ir_hash_mismatch_fails_deterministically(self):
        result = run_paper1_dependency_conformance(FIXTURE_PATH, expected_normalized_ir_hash="sha256:" + "0" * 64)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "NORMALIZED_IR_HASH_MISMATCH")

    def test_fixture_drift_is_rejected_by_default_pinned_source_hash(self):
        fixture = _fixture()
        fixture["input"]["graph"]["nodes"].append("unused")
        result = run_paper1_dependency_conformance(self._write_fixture(fixture))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "SOURCE_HASH_MISMATCH")

    def test_malformed_analysis_result_fails_deterministically(self):
        def fail_validation(*args, **kwargs):
            raise foundation_adapter.StructuralEvidenceValidationError("analysis result hash mismatch")

        with mock.patch.object(foundation_adapter, "compile_structural_evidence_artifact", fail_validation):
            result = run_paper1_dependency_conformance(FIXTURE_PATH)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "MALFORMED_ANALYSIS_RESULT")

    def test_expected_classification_mismatch_fails_deterministically(self):
        fixture = _fixture()
        fixture["expected_semantics"]["canonical_outputs"]["is_dependency"] = False
        fixture_path = self._write_fixture(fixture)
        result = run_paper1_dependency_conformance(fixture_path, expected_source_fixture_hash=_hash_file(fixture_path))
        self.assertEqual(result["verdict"], "FAIL")
        self.assertGreaterEqual(
            {item["code"] for item in result["diagnostics"]},
            {"DEPENDENCY_SEMANTIC_MISMATCH", "EXPECTED_CLASSIFICATION_MISMATCH"},
        )

    def test_repeated_run_divergence_fails_deterministically(self):
        fixture = _fixture()
        topology = _paper1_topology_from_fixture(fixture)
        artifact = compile_structural_evidence_artifact(canonical_json_text(topology), source_id=fixture["fixture_id"])
        divergent = copy.deepcopy(artifact)
        divergent["diagnostics"] = [{"code": "DIVERGED"}]
        result = run_paper1_dependency_conformance(FIXTURE_PATH, second_artifact_override=divergent)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["diagnostics"][0]["code"], "REPEATED_RUN_DIVERGENCE")

    def test_missing_fixture_path_returns_blocked_result(self):
        result = run_paper1_dependency_conformance("/tmp/synapse-missing-paper1-fixture.json")
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertEqual(result["diagnostics"][0]["code"], "FIXTURE_UNAVAILABLE")

    def test_missing_research_repository_path_is_unobserved_not_crashing(self):
        result = run_paper1_dependency_conformance(FIXTURE_PATH, research_repo_path="/tmp/synapse-missing-research-repo")
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertEqual(result["diagnostics"][0]["code"], "REPOSITORY_COMMIT_UNOBSERVED")
        self.assertEqual(result["research_repository_commit"], "UNOBSERVED")

    def test_negative_outputs_are_byte_identical(self):
        cases = [
            (lambda fixture: fixture.update({"research_object_id": "definition.unknown"}), "UNKNOWN_RESEARCH_OBJECT"),
            (lambda fixture: fixture.update({"fixture_id": "paper1.dependency-predicate.basic-v2"}), "UNSUPPORTED_FIXTURE_VERSION"),
            (lambda fixture: fixture["input"]["graph"].pop("nodes"), "MALFORMED_FIXTURE"),
        ]
        for mutate, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                fixture = _fixture()
                mutate(fixture)
                path = self._write_fixture(fixture)
                first = canonical_json_bytes(run_paper1_dependency_conformance(path))
                second = canonical_json_bytes(run_paper1_dependency_conformance(path))
                self.assertEqual(first, second)
                self.assertIn(expected_code.encode("utf-8"), first)


def _hash_file(path):
    import hashlib

    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
