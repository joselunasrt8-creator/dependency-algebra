import unittest
from pathlib import Path

from dependency_algebra.compiler import compile_artifact
from dependency_algebra.engine import analyze_artifact_legacy, analyze_artifact_registered
from dependency_algebra.frontend import parse_topology, validate_and_normalize
from dependency_algebra.ir import CanonicalIR
from dependency_algebra.serialization import analysis_result_to_dict, canonical_json_text

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_FIXTURES = (
    sorted((ROOT / "fixtures" / "valid").glob("*.json"))
    + sorted((ROOT / "fixtures" / "degraded").glob("*.json"))
    + sorted((ROOT / "fixtures" / "null").glob("*.json"))
    + sorted((ROOT / "fixtures" / "determinism").glob("*.json"))
    + [ROOT / "fixtures" / "basic.json"]
)


class DependencyPassEquivalenceTests(unittest.TestCase):
    def _ir_for_fixture(self, path: Path) -> CanonicalIR:
        source = path.read_text(encoding="utf-8")
        topology = parse_topology(source, str(path.relative_to(ROOT)))
        return CanonicalIR.from_dict(validate_and_normalize(topology, str(path.relative_to(ROOT))))

    def test_registered_dependency_pass_matches_legacy_execution_for_every_canonical_fixture(self):
        for path in CANONICAL_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                ir = self._ir_for_fixture(path)
                legacy = analyze_artifact_legacy(ir)
                registered = analyze_artifact_registered(ir)

                self.assertEqual(legacy.classification, registered.classification)
                self.assertEqual(tuple(item.workload_id for item in legacy.dependencies), tuple(item.workload_id for item in registered.dependencies))
                self.assertEqual(analysis_result_to_dict(legacy)["dependencies"], analysis_result_to_dict(registered)["dependencies"])
                self.assertEqual(analysis_result_to_dict(legacy)["reachability"], analysis_result_to_dict(registered)["reachability"])
                self.assertEqual(legacy.normalized_ir_hash, registered.normalized_ir_hash)
                self.assertEqual(analysis_result_to_dict(legacy), analysis_result_to_dict(registered))

    def test_registered_execution_repeats_with_identical_analysis_serialization(self):
        for path in CANONICAL_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                ir = self._ir_for_fixture(path)
                first = canonical_json_text(analysis_result_to_dict(analyze_artifact_registered(ir)))
                second = canonical_json_text(analysis_result_to_dict(analyze_artifact_registered(ir)))
                self.assertEqual(first, second)

    def test_compiler_artifact_serialization_repeats_identically(self):
        for path in CANONICAL_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                source = path.read_bytes()
                source_id = str(path.relative_to(ROOT))
                first = canonical_json_text(compile_artifact(source, source_id=source_id))
                second = canonical_json_text(compile_artifact(source, source_id=source_id))
                self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
