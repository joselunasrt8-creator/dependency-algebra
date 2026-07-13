import json
import unittest
from pathlib import Path
from typing import Any

from dependency_algebra.compiler import ARTIFACT_SCHEMA_VERSION, COMPILER_VERSION, compile_artifact
from dependency_algebra.engine import _analyze_artifact_legacy, analyze_artifact_registered
from dependency_algebra.frontend import TOPOLOGY_SCHEMA_VERSION, parse_topology, validate_and_normalize
from dependency_algebra.ir import CanonicalIR, Edge, Workload
from dependency_algebra.serialization import analysis_result_to_dict, canonical_json_text, sha256_bytes, sha256_digest
from dependency_algebra.version import __version__

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_FIXTURE_FAMILIES = {
    "valid": sorted((ROOT / "fixtures" / "valid").glob("*.json")),
    "degraded": sorted((ROOT / "fixtures" / "degraded").glob("*.json")),
    "null": sorted((ROOT / "fixtures" / "null").glob("*.json")),
    "determinism": sorted((ROOT / "fixtures" / "determinism").glob("*.json")),
    "basic": [ROOT / "fixtures" / "basic.json"],
}
DEPENDENCY_FIXTURE_FAMILY = sorted((ROOT / "fixtures" / "dependency").glob("*.json"))
INVALID_DEPENDENCY_FIXTURES = {
    "invalid-projected-ir-rejection.json",
    "invalid-reachability-result-rejection.json",
}
CANONICAL_TOPOLOGY_FIXTURES = [path for paths in TOPOLOGY_FIXTURE_FAMILIES.values() for path in paths]
CANONICAL_DEPENDENCY_FIXTURES = [
    path for path in DEPENDENCY_FIXTURE_FAMILY if path.name not in INVALID_DEPENDENCY_FIXTURES
]


class DependencyPassEquivalenceTests(unittest.TestCase):
    def test_required_fixture_families_are_non_empty(self):
        for family, paths in TOPOLOGY_FIXTURE_FAMILIES.items():
            with self.subTest(family=family):
                self.assertGreater(len(paths), 0)
        self.assertGreater(len(DEPENDENCY_FIXTURE_FAMILY), 0)
        self.assertGreater(len(CANONICAL_DEPENDENCY_FIXTURES), 0)

    def _ir_for_topology_fixture(self, path: Path) -> CanonicalIR:
        source = path.read_text(encoding="utf-8")
        topology = parse_topology(source, str(path.relative_to(ROOT)))
        return CanonicalIR.from_dict(validate_and_normalize(topology, str(path.relative_to(ROOT))))

    def _ir_for_dependency_fixture(self, path: Path) -> CanonicalIR:
        doc = json.loads(path.read_text(encoding="utf-8"))
        roots = tuple(doc["roots"])
        target = doc["target"]
        candidate_set = tuple(doc["candidate_set"])
        reachable_after_projection = tuple(doc["reachable_after_projection"])
        workload = Workload(doc["workload_id"], roots, target, candidate_set)
        components = tuple(dict.fromkeys((*roots, *candidate_set, *reachable_after_projection, target)))
        adjacency: dict[str, tuple[Edge, ...]] = {component: () for component in components}
        if doc["dependency"]:
            candidate = candidate_set[0]
            adjacency[roots[0]] = (Edge(f"{roots[0]}-to-{candidate}", candidate),)
            if candidate != target:
                adjacency[candidate] = (Edge(f"{candidate}-to-{target}", target),)
        else:
            alternate = next(node for node in reachable_after_projection if node not in roots and node != target)
            candidate = candidate_set[0]
            adjacency[roots[0]] = (
                Edge(f"{roots[0]}-to-{candidate}", candidate),
                Edge(f"{roots[0]}-to-{alternate}", alternate),
            )
            adjacency[candidate] = (Edge(f"{candidate}-to-{target}", target),)
            adjacency[alternate] = (Edge(f"{alternate}-to-{target}", target),)
        return CanonicalIR(
            topology_id=f"dependency-fixture:{path.name}",
            normalized_ir_hash=doc["normalized_ir_hash"],
            components=components,
            adjacency=adjacency,
            workloads=(workload,),
        )

    def _assert_legacy_registered_analysis_equivalence(self, ir: CanonicalIR) -> None:
        legacy = _analyze_artifact_legacy(ir)
        registered = analyze_artifact_registered(ir)

        self.assertEqual(legacy.classification, registered.classification)
        self.assertEqual(
            tuple(item.workload_id for item in legacy.dependencies),
            tuple(item.workload_id for item in registered.dependencies),
        )
        self.assertEqual(analysis_result_to_dict(legacy)["dependencies"], analysis_result_to_dict(registered)["dependencies"])
        self.assertEqual(analysis_result_to_dict(legacy)["reachability"], analysis_result_to_dict(registered)["reachability"])
        self.assertEqual(legacy.normalized_ir_hash, registered.normalized_ir_hash)
        self.assertEqual(analysis_result_to_dict(legacy), analysis_result_to_dict(registered))

    def test_registered_dependency_pass_matches_legacy_execution_for_topology_fixtures(self):
        for path in CANONICAL_TOPOLOGY_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                self._assert_legacy_registered_analysis_equivalence(self._ir_for_topology_fixture(path))

    def test_registered_dependency_pass_matches_legacy_execution_for_dependency_fixtures(self):
        for path in CANONICAL_DEPENDENCY_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                self._assert_legacy_registered_analysis_equivalence(self._ir_for_dependency_fixture(path))

    def test_registered_execution_repeats_with_identical_analysis_serialization(self):
        for path in CANONICAL_TOPOLOGY_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                ir = self._ir_for_topology_fixture(path)
                first = canonical_json_text(analysis_result_to_dict(analyze_artifact_registered(ir)))
                second = canonical_json_text(analysis_result_to_dict(analyze_artifact_registered(ir)))
                self.assertEqual(first, second)

    def test_compiler_artifact_serialization_matches_legacy_and_repeats_identically(self):
        for path in CANONICAL_TOPOLOGY_FIXTURES:
            with self.subTest(fixture=str(path.relative_to(ROOT))):
                source = path.read_bytes()
                source_id = str(path.relative_to(ROOT))
                legacy = canonical_json_text(self._compile_artifact_legacy(source, source_id=source_id))
                registered_first = canonical_json_text(compile_artifact(source, source_id=source_id))
                registered_second = canonical_json_text(compile_artifact(source, source_id=source_id))
                self.assertEqual(legacy, registered_first)
                self.assertEqual(registered_first, registered_second)

    def _compile_artifact_legacy(self, source: bytes, *, source_id: str) -> dict[str, Any]:
        source_text = source.decode("utf-8")
        topology = parse_topology(source_text, source_id)
        ir = validate_and_normalize(topology, source_id)
        analysis = analysis_result_to_dict(_analyze_artifact_legacy(CanonicalIR.from_dict(ir)))
        dependencies = analysis["dependencies"]
        artifact = {
            "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
            "source_topology_schema_version": TOPOLOGY_SCHEMA_VERSION,
            "compiler_version": COMPILER_VERSION,
            "package_version": __version__,
            "input_hash": sha256_bytes(source),
            "normalized_ir_hash": ir["normalized_ir_hash"],
            "classification": analysis["classification"],
            "reachability_graph": analysis["reachability"],
            "dependency_lattice": dependencies,
            "failure_surface": [item for item in dependencies if item["dependency"]],
            "redundancy_map": {
                item["workload_id"]: {
                    "candidate_set": item["candidate_set"],
                    "dependency": item["dependency"],
                    "dependency_reason": item["dependency_reason"],
                }
                for item in dependencies
            },
            "k_of_n_resilience_profile": {
                item["workload_id"]: {
                    "candidate_count": len(item["candidate_set"]),
                    "reachable_after_projection_count": len(item["reachable_after_projection"]),
                }
                for item in dependencies
            },
            "annihilation_conditions": [
                {
                    "workload_id": item["workload_id"],
                    "candidate_set": item["candidate_set"],
                    "target": item["target"],
                }
                for item in dependencies
                if item["dependency"]
            ],
            "diagnostics": [],
            "warnings": [],
            "errors": [],
            "provenance": {
                "source_id": source_id,
                "pipeline": ["parse_topology", "validate_and_normalize", "analyze", "emit_artifact"],
                "analysis_result_hash": analysis["dependency_result_hash"],
            },
        }
        artifact["artifact_hash"] = sha256_digest(artifact)
        return artifact


if __name__ == "__main__":
    unittest.main()
