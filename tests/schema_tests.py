import importlib.util
import json
import re
import unittest
from pathlib import Path

if importlib.util.find_spec("jsonschema") is None:
    Draft202012Validator = None
    Resource = None
    Registry = None
    ValidationError = Exception
else:
    from jsonschema import Draft202012Validator, ValidationError
    from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
SCHEMAS = ROOT / "schemas"
CLASSIFICATIONS = {"VALID", "DEGRADED", "NULL"}
ID_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")
SCHEMA_PATHS = [
    SCHEMAS / "topology.schema.json",
    SCHEMAS / "artifact.schema.json",
    SCHEMAS / "classification.schema.json",
]
TOPOLOGY_SCHEMA_PATH = SCHEMAS / "topology.schema.json"
CLASSIFICATION_SCHEMA_PATH = SCHEMAS / "classification.schema.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def schema_documents():
    return {schema["$id"]: schema for schema in (load_json(path) for path in SCHEMA_PATHS)}


def schema_registry():
    return Registry().with_resources(
        (schema_id, Resource.from_contents(schema))
        for schema_id, schema in schema_documents().items()
    )


def json_schema_validator(path: Path):
    schema = load_json(path)
    return Draft202012Validator(schema, registry=schema_registry())


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


@unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
class JsonSchemaContractTests(unittest.TestCase):
    def test_schema_documents_are_valid_draft_2020_12_schemas(self):
        for path in SCHEMA_PATHS:
            with self.subTest(path=path):
                schema = load_json(path)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                Draft202012Validator.check_schema(schema)

    def test_classification_schema_accepts_only_structural_classifications(self):
        validator = json_schema_validator(CLASSIFICATION_SCHEMA_PATH)
        for classification in sorted(CLASSIFICATIONS):
            with self.subTest(classification=classification):
                validator.validate(classification)
        for classification in ["UNKNOWN", "valid", "", None, {"classification": "VALID"}]:
            with self.subTest(classification=classification):
                with self.assertRaises(ValidationError):
                    validator.validate(classification)


    def test_artifact_schema_accepts_schema_only_reserved_outputs(self):
        validator = json_schema_validator(SCHEMAS / "artifact.schema.json")
        artifact = {
            "artifact_schema_version": "dependency-algebra.artifact.v1",
            "source_topology_schema_version": "dependency-algebra.topology.v1",
            "compiler_version": "schema-only-milestone-1",
            "input_hash": "sha256:" + "0" * 64,
            "normalized_ir_hash": "sha256:" + "1" * 64,
            "artifact_hash": "sha256:" + "2" * 64,
            "classification": "VALID",
            "reachability_graph": {},
            "dependency_lattice": [],
            "failure_surface": [],
            "redundancy_map": {},
            "k_of_n_resilience_profile": {},
            "annihilation_conditions": [],
            "diagnostics": [],
            "warnings": [],
            "errors": [],
        }
        validator.validate(artifact)

    def test_artifact_schema_rejects_volatile_or_authority_fields(self):
        validator = json_schema_validator(SCHEMAS / "artifact.schema.json")
        artifact = {
            "artifact_schema_version": "dependency-algebra.artifact.v1",
            "source_topology_schema_version": "dependency-algebra.topology.v1",
            "compiler_version": "schema-only-milestone-1",
            "input_hash": "sha256:" + "0" * 64,
            "normalized_ir_hash": "sha256:" + "1" * 64,
            "artifact_hash": "sha256:" + "2" * 64,
            "classification": "VALID",
            "reachability_graph": {},
            "dependency_lattice": [],
            "failure_surface": [],
            "redundancy_map": {},
            "k_of_n_resilience_profile": {},
            "annihilation_conditions": [],
            "diagnostics": [],
            "warnings": [],
            "errors": [],
            "generated_at": "2026-07-05T00:00:00Z",
        }
        with self.assertRaises(ValidationError):
            validator.validate(artifact)

    def test_canonical_topology_fixtures_pass_json_schema_contract(self):
        paths = sorted((FIXTURES / "valid").glob("*.json")) + sorted((FIXTURES / "degraded").glob("*.json")) + sorted((FIXTURES / "null").glob("*.json")) + sorted((FIXTURES / "determinism").glob("*.json"))
        self.assertGreaterEqual(len(paths), 5)
        validator = json_schema_validator(TOPOLOGY_SCHEMA_PATH)
        for path in paths:
            with self.subTest(path=path):
                validator.validate(load_json(path))

    def test_semantic_invalid_fixtures_can_pass_json_schema_shape(self):
        validator = json_schema_validator(TOPOLOGY_SCHEMA_PATH)
        for path in [
            FIXTURES / "invalid" / "unknown-node-reference.json",
            FIXTURES / "invalid" / "duplicate-identifiers.json",
        ]:
            with self.subTest(path=path):
                doc = load_json(path)
                validator.validate(doc)
                self.assertNotEqual(validate_topology(doc), [])


class SemanticTopologyValidationTests(unittest.TestCase):
    def test_valid_and_determinism_fixtures_pass_semantic_contract(self):
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

    def test_duplicate_identifier_fixture_fails_deterministically(self):
        path = FIXTURES / "invalid" / "duplicate-identifiers.json"
        errors = validate_topology(load_json(path))
        self.assertEqual(
            errors,
            [
                "duplicate component ids: ['client']",
                "duplicate edge ids: ['client-api']",
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
