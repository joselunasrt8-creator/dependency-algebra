import tempfile
import unittest
from pathlib import Path

from conformance.adapters import Adapter
from conformance.compare import compare
from conformance.evidence import validate_evidence
from conformance.fixtures import CanonicalFixture, discover_fixtures, validate_fixture
from conformance.runner import run
from conformance.status import PASS, UNOBSERVED


class ConformanceHarnessTests(unittest.TestCase):
    def test_research_object_fixtures_are_discovered_and_valid(self):
        fixtures = discover_fixtures()
        self.assertGreaterEqual(len(fixtures), 2)
        self.assertEqual([fixture.fixture_id for fixture in fixtures], sorted(fixture.fixture_id for fixture in fixtures))
        for fixture in fixtures:
            self.assertEqual(validate_fixture(fixture), [])

    def test_equivalent_evidence_compares_pass_with_order_variation(self):
        expected = {"canonical_outputs": {"b": 2, "a": [1]}, "required_diagnostics": []}
        observed = {"required_diagnostics": [], "canonical_outputs": {"a": [1], "b": 2}}
        matched, mismatches = compare(expected, observed)
        self.assertTrue(matched)
        self.assertEqual(mismatches, [])

    def test_semantic_mismatch_is_deterministic_drift(self):
        matched, mismatches = compare({"canonical_outputs": {"value": True}}, {"canonical_outputs": {"value": False}})
        self.assertFalse(matched)
        self.assertEqual(mismatches[0]["path"], "canonical_outputs")

    def test_malformed_evidence_validation_identifies_paths(self):
        errors = validate_evidence({}, fixture_id="f", research_object_id="r", adapter_id="a")
        self.assertIn({"path": "schema_version", "message": "missing required field"}, errors)

    def test_runner_passes_canonical_fixtures_and_writes_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run(report_path=Path(tmp) / "report.json")
        self.assertEqual(report["summary"][PASS], len(report["comparison_matrix"]))
        self.assertEqual(report["mismatches"], [])
        self.assertTrue(all(item["replay"]["status"] == PASS for item in report["comparison_matrix"]))

    def test_missing_adapter_is_unobserved(self):
        # Exercise the canonical no-adapter status through a fixture validation path by monkeypatching at module level.
        import conformance.runner as runner
        original = runner.discover_adapters
        runner.discover_adapters = lambda: ()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                report = runner.run(report_path=Path(tmp) / "report.json")
        finally:
            runner.discover_adapters = original
        self.assertEqual(report["summary"][UNOBSERVED], len(report["comparison_matrix"]))

    def test_blocked_unsupported_research_object_fixture(self):
        fixture = CanonicalFixture(
            path=Path("unsupported.json"),
            fixture_hash="sha256:" + "0" * 64,
            document={
                "schema_version": "structural-analysis-foundations.conformance-fixture.v1",
                "fixture_id": "unsupported",
                "research_object_id": "unsupported.object",
                "deterministic_timestamp": "2026-01-01T00:00:00Z",
                "input": {},
                "expected_evidence": {"canonical_outputs": {}},
            },
        )
        self.assertEqual(validate_fixture(fixture), [{"path": "research_object_id", "message": "unsupported research object"}])

    def test_blocked_adapter_execution_is_reported(self):
        import conformance.runner as runner
        fixture = discover_fixtures()[0]
        original_adapters = runner.discover_adapters
        original_fixtures = runner.discover_fixtures
        runner.discover_adapters = lambda: (Adapter("broken", ("python", "-c", "import sys; sys.exit(7)")),)
        runner.discover_fixtures = lambda: (fixture,)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                report = runner.run(report_path=Path(tmp) / "report.json")
        finally:
            runner.discover_adapters = original_adapters
            runner.discover_fixtures = original_fixtures
        self.assertEqual(report["summary"]["FAIL"], 1)
        self.assertEqual(report["blockers"][0]["path"], "adapter.returncode")


if __name__ == "__main__":
    unittest.main()
