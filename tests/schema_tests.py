import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SCHEMAS = ROOT / "schemas"
CLASSIFICATIONS = {"VALID", "DEGRADED", "NULL"}
ID_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_topology(doc):
    errors = []
    required = {"schema_version", "topology_id", "components", "edges", "workloads"}
    missing = sorted(required - set(doc))
    if missing:
        errors.append(f"missing required fields: {missing}")
    if doc.get("schema_version") != "dependency-algebra.topology.v1":
        errors.append("unknown schema_version")
    if not isinstance(doc.get("topology_id"), str) or not ID_RE.match(doc.get("topology_id", "")):
        errors.append("invalid topology_id")

    component_ids = []
    for component in doc.get("components", []):
        cid = component.get("id")
        if not isinstance(cid, str) or not ID_RE.match(cid):
            errors.append(f"invalid component id: {cid!r}")
        component_ids.append(cid)
    duplicates = sorted({cid for cid in component_ids if component_ids.count(cid) > 1})
    if duplicates:
        errors.append(f"duplicate component ids: {duplicates}")
    component_set = set(component_ids)

    edge_ids = []
    for edge in doc.get("edges", []):
        eid = edge.get("id")
        edge_ids.append(eid)
        if not isinstance(eid, str) or not ID_RE.match(eid):
            errors.append(f"invalid edge id: {eid!r}")
        if edge.get("from") not in component_set:
            errors.append(f"edge {eid} references unknown from component {edge.get('from')!r}")
        if edge.get("to") not in component_set:
            errors.append(f"edge {eid} references unknown to component {edge.get('to')!r}")
    duplicate_edges = sorted({eid for eid in edge_ids if edge_ids.count(eid) > 1})
    if duplicate_edges:
        errors.append(f"duplicate edge ids: {duplicate_edges}")

    for workload in doc.get("workloads", []):
        wid = workload.get("id")
        if not isinstance(wid, str) or not ID_RE.match(wid):
            errors.append(f"invalid workload id: {wid!r}")
        if workload.get("expected_classification") not in CLASSIFICATIONS:
            errors.append(f"invalid classification for workload {wid}")
        for root in workload.get("roots", []):
            if root not in component_set:
                errors.append(f"workload {wid} references unknown root {root!r}")
        if workload.get("target") not in component_set:
            errors.append(f"workload {wid} references unknown target {workload.get('target')!r}")
        for candidate in workload.get("candidate_set", []):
            if candidate not in component_set:
                errors.append(f"workload {wid} references unknown candidate {candidate!r}")
    return errors


class SchemaContractTests(unittest.TestCase):
    def test_schema_documents_are_json(self):
        for path in sorted(SCHEMAS.glob("*.schema.json")):
            with self.subTest(path=path):
                doc = load_json(path)
                self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_valid_and_determinism_fixtures_pass_contract(self):
        paths = sorted((FIXTURES / "valid").glob("*.json")) + sorted((FIXTURES / "degraded").glob("*.json")) + sorted((FIXTURES / "null").glob("*.json")) + sorted((FIXTURES / "determinism").glob("*.json"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(validate_topology(load_json(path)), [])

    def test_unknown_reference_fixture_fails_deterministically(self):
        path = FIXTURES / "invalid" / "unknown-node-reference.json"
        errors = validate_topology(load_json(path))
        self.assertEqual(
            errors,
            [
                "edge client-missing references unknown to component 'missing'",
                "workload broken references unknown target 'missing'",
            ],
        )

    def test_malformed_json_fixture_fails_parse(self):
        path = FIXTURES / "invalid" / "malformed-json.json"
        with self.assertRaises(json.JSONDecodeError):
            load_json(path)

    def test_canonical_json_serialization_is_stable(self):
        path = FIXTURES / "determinism" / "stable-ordering.json"
        doc = load_json(path)
        first = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        second = json.dumps(load_json(path), sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
