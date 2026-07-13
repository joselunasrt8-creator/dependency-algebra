import copy
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
    SCHEMAS / "ast.schema.json",
    SCHEMAS / "ir.schema.json",
    SCHEMAS / "diagnostic.schema.json",
    SCHEMAS / "reachability.schema.json",
    SCHEMAS / "dependency.schema.json",
    SCHEMAS / "projection.schema.json",
    SCHEMAS / "structural-evidence.schema.json",
]
TOPOLOGY_SCHEMA_PATH = SCHEMAS / "topology.schema.json"
CLASSIFICATION_SCHEMA_PATH = SCHEMAS / "classification.schema.json"
AST_SCHEMA_PATH = SCHEMAS / "ast.schema.json"
IR_SCHEMA_PATH = SCHEMAS / "ir.schema.json"
DIAGNOSTIC_SCHEMA_PATH = SCHEMAS / "diagnostic.schema.json"
REACHABILITY_SCHEMA_PATH = SCHEMAS / "reachability.schema.json"
DEPENDENCY_SCHEMA_PATH = SCHEMAS / "dependency.schema.json"
PROJECTION_SCHEMA_PATH = SCHEMAS / "projection.schema.json"


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
            "provenance": {
                "source_id": "schema-test",
                "pipeline": ["parse_topology", "validate_and_normalize", "analyze", "emit_artifact"],
                "analysis_result_hash": "sha256:" + "3" * 64,
            },
        }
        validator.validate(artifact)

    def test_structural_evidence_schema_accepts_v2_fixture(self):
        validator = json_schema_validator(SCHEMAS / "structural-evidence.schema.json")
        validator.validate(load_json(FIXTURES / "structural_evidence" / "minimal-valid-v2.json"))

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


@unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
class AstIrContractTests(unittest.TestCase):
    FORBIDDEN_IR_FIELDS = {
        "timestamp",
        "absolute_path",
        "environment",
        "diagnostics",
        "runtime",
        "authority",
        "proof",
        "governance",
        "policy",
        "execution",
        "continuityos",
    }

    def canonical_bytes(self, doc):
        payload = dict(doc)
        payload.pop("normalized_ir_hash", None)
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def contract_test_ast_projection(self, doc):
        """Project AST fixture content for contract tests only.

        This helper is deliberately scoped to fixture assertions. It is not a
        parser, compiler normalizer, or implementation surface; it only removes
        source-order/object-order noise so tests can assert that equivalent AST
        fixtures carry the same structural contract content.
        """
        return {
            "schema_version": doc["schema_version"],
            "topology_id": doc["topology_id"],
            "source": doc["source"],
            "components": sorted(
                (
                    {
                        "id": component["id"],
                        "type": component.get("type"),
                        "metadata": component.get("metadata", {}),
                        "source_id": component["source_location"]["source_id"],
                    }
                    for component in doc["components"]
                ),
                key=lambda component: component["id"],
            ),
            "edges": sorted(
                (
                    {
                        "id": edge["id"],
                        "from": edge["from"],
                        "to": edge["to"],
                        "metadata": edge.get("metadata", {}),
                        "source_id": edge["source_location"]["source_id"],
                    }
                    for edge in doc["edges"]
                ),
                key=lambda edge: edge["id"],
            ),
            "workloads": sorted(
                (
                    {
                        "id": workload["id"],
                        "roots": sorted(set(workload["roots"])),
                        "target": workload["target"],
                        "candidate_set": sorted(set(workload["candidate_set"])),
                        "expected_classification": workload["expected_classification"],
                        "source_id": workload["source_location"]["source_id"],
                    }
                    for workload in doc["workloads"]
                ),
                key=lambda workload: workload["id"],
            ),
        }

    def assert_ir_invariants(self, doc):
        component_ids = [component["id"] for component in doc["components"]]
        edge_ids = [edge["id"] for edge in doc["edges"]]
        workload_ids = [workload["id"] for workload in doc["workloads"]]
        component_set = set(component_ids)
        edge_set = set(edge_ids)
        edge_by_id = {edge["id"]: edge for edge in doc["edges"]}
        forward_edge_ids = []
        reverse_edge_ids = []

        self.assertEqual(component_ids, sorted(component_ids))
        self.assertEqual(edge_ids, sorted(edge_ids))
        self.assertEqual(workload_ids, sorted(workload_ids))
        self.assertEqual(len(component_ids), len(component_set))
        self.assertEqual(len(edge_ids), len(edge_set))
        self.assertEqual(len(workload_ids), len(set(workload_ids)))
        self.assertEqual(set(doc["adjacency"]), component_set)
        self.assertEqual(set(doc["reverse_adjacency"]), component_set)

        for edge in doc["edges"]:
            self.assertIn(edge["from"], component_set)
            self.assertIn(edge["to"], component_set)
        for source, outbound in doc["adjacency"].items():
            self.assertEqual([item["edge_id"] for item in outbound], sorted(item["edge_id"] for item in outbound))
            for item in outbound:
                self.assertIn(item["edge_id"], edge_set)
                self.assertIn(item["component_id"], component_set)
                edge = edge_by_id[item["edge_id"]]
                self.assertEqual(edge["from"], source)
                self.assertEqual(edge["to"], item["component_id"])
                forward_edge_ids.append(item["edge_id"])
        for target, inbound in doc["reverse_adjacency"].items():
            self.assertEqual([item["edge_id"] for item in inbound], sorted(item["edge_id"] for item in inbound))
            for item in inbound:
                self.assertIn(item["edge_id"], edge_set)
                self.assertIn(item["component_id"], component_set)
                edge = edge_by_id[item["edge_id"]]
                self.assertEqual(edge["to"], target)
                self.assertEqual(edge["from"], item["component_id"])
                reverse_edge_ids.append(item["edge_id"])
        self.assertEqual(sorted(forward_edge_ids), edge_ids)
        self.assertEqual(sorted(reverse_edge_ids), edge_ids)
        for workload in doc["workloads"]:
            self.assertEqual(workload["roots"], sorted(set(workload["roots"])))
            self.assertEqual(workload["candidate_set"], sorted(set(workload["candidate_set"])))
            self.assertIn(workload["target"], component_set)
            self.assertTrue(set(workload["roots"]).issubset(component_set))
            self.assertTrue(set(workload["candidate_set"]).issubset(component_set))
            self.assertGreater(len(workload["candidate_set"]), 0)

    def test_ast_fixture_validates(self):
        validator = json_schema_validator(AST_SCHEMA_PATH)
        for path in sorted((FIXTURES / "ast").glob("*.json")):
            with self.subTest(path=path):
                validator.validate(load_json(path))

    def test_ir_fixtures_validate_and_satisfy_contract_invariants(self):
        validator = json_schema_validator(IR_SCHEMA_PATH)
        for path in sorted((FIXTURES / "ir").glob("*.json")):
            with self.subTest(path=path):
                doc = load_json(path)
                validator.validate(doc)
                self.assert_ir_invariants(doc)

    def test_reordered_equivalent_ast_has_same_contract_ir(self):
        canonical_ast = load_json(FIXTURES / "ast" / "minimal-valid-ast.json")
        reordered_ast = load_json(FIXTURES / "ast" / "reordered-equivalent-ast.json")
        self.assertEqual(
            self.contract_test_ast_projection(canonical_ast),
            self.contract_test_ast_projection(reordered_ast),
        )

    def test_invalid_topology_fixtures_cannot_be_valid_ir(self):
        validator = json_schema_validator(IR_SCHEMA_PATH)
        for path in [
            FIXTURES / "invalid" / "unknown-node-reference.json",
            FIXTURES / "invalid" / "duplicate-identifiers.json",
        ]:
            with self.subTest(path=path):
                with self.assertRaises(ValidationError):
                    validator.validate(load_json(path))

    def test_ir_schema_excludes_volatile_and_forbidden_fields(self):
        schema_text = json.dumps(load_json(IR_SCHEMA_PATH)).lower()
        for field in self.FORBIDDEN_IR_FIELDS:
            with self.subTest(field=field):
                self.assertNotIn(field, schema_text)

    def test_canonical_ir_serialization_and_hash_vector_are_stable(self):
        import hashlib

        doc = load_json(FIXTURES / "ir" / "minimal-valid-ir.json")
        first = self.canonical_bytes(doc)
        second = self.canonical_bytes(load_json(FIXTURES / "ir" / "minimal-valid-ir.json"))
        self.assertEqual(first, second)
        self.assertFalse(first.endswith(b"\n"))
        self.assertEqual(
            "sha256:" + hashlib.sha256(first).hexdigest(),
            doc["normalized_ir_hash"],
        )


@unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
class FrontendDiagnosticSchemaTests(unittest.TestCase):
    def test_diagnostic_fixtures_validate(self):
        validator = json_schema_validator(DIAGNOSTIC_SCHEMA_PATH)
        for path in sorted((FIXTURES / "diagnostics").glob("*.json")):
            with self.subTest(path=path):
                validator.validate(load_json(path))


class FrontendDiagnosticContractTests(unittest.TestCase):
    FORBIDDEN_DIAGNOSTIC_TERMS = {
        "absolute_path",
        "timestamp",
        "environment",
        "random",
        "authorization",
        "authority",
        "proof",
        "governance",
        "policy",
        "execution",
        "mutation",
    }

    def diagnostic_sort_key(self, diagnostic):
        source = diagnostic.get("source", {})
        subject = diagnostic["subject"]
        return (
            diagnostic["code"],
            subject["kind"],
            subject["id"],
            source.get("source_id", ""),
            source.get("source_order", 10**12),
        )

    def test_diagnostic_fixtures_are_deterministically_ordered(self):
        for path in sorted((FIXTURES / "diagnostics").glob("*.json")):
            with self.subTest(path=path):
                diagnostics = load_json(path)["diagnostics"]
                self.assertEqual(diagnostics, sorted(diagnostics, key=self.diagnostic_sort_key))

    def test_diagnostic_fixtures_exclude_forbidden_terms(self):
        for path in sorted((FIXTURES / "diagnostics").glob("*.json")):
            fixture_text = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path):
                for term in self.FORBIDDEN_DIAGNOSTIC_TERMS:
                    self.assertNotIn(term, fixture_text)

    def test_required_frontend_failure_vectors_exist(self):
        expected = {
            "malformed-json.json",
            "unsupported-schema-version.json",
            "duplicate-component-id.json",
            "duplicate-workload-id.json",
            "unresolved-edge-endpoint.json",
            "unresolved-workload-root.json",
            "empty-candidate-set.json",
            "ordered-multiple-diagnostics.json",
        }
        actual = {path.name for path in (FIXTURES / "diagnostics").glob("*.json")}
        self.assertEqual(actual, expected)


@unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
class ReachabilitySchemaContractTests(unittest.TestCase):
    FORBIDDEN_REACHABILITY_TERMS = {
        "absolute_path",
        "timestamp",
        "environment",
        "random",
        "authorization",
        "authority",
        "proof",
        "governance",
        "policy",
        "execution",
        "mutation",
    }

    def canonical_bytes(self, doc):
        payload = dict(doc)
        payload.pop("reachability_result_hash", None)
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def diagnostic_sort_key(self, diagnostic):
        subject = diagnostic["subject"]
        return (diagnostic["code"], diagnostic["severity"], subject["kind"], subject["id"])

    def assert_reachability_ordering(self, doc):
        workload_ids = [result["workload_id"] for result in doc["results"]]
        self.assertEqual(workload_ids, sorted(workload_ids))
        for result in doc["results"]:
            self.assertEqual(result["roots"], sorted(set(result["roots"])))
            self.assertEqual(result["reached_by"], sorted(set(result["reached_by"])))
            self.assertEqual(result["visited_nodes"], sorted(set(result["visited_nodes"])))
            self.assertEqual(
                result["traversal_edges"],
                sorted(
                    result["traversal_edges"],
                    key=lambda edge: (edge["edge_id"], edge["from"], edge["to"]),
                ),
            )
            self.assertEqual(result["diagnostics"], sorted(result["diagnostics"], key=self.diagnostic_sort_key))
            if result["reachable"]:
                self.assertGreaterEqual(len(result["reached_by"]), 1)
            else:
                self.assertEqual(result["reached_by"], [])
                self.assertIn("REACHABILITY.UNREACHABLE_TARGET", [diagnostic["code"] for diagnostic in result["diagnostics"]])

    def test_reachability_fixtures_validate_and_are_ordered(self):
        validator = json_schema_validator(REACHABILITY_SCHEMA_PATH)
        for path in sorted((FIXTURES / "reachability").glob("*.json")):
            with self.subTest(path=path):
                doc = load_json(path)
                validator.validate(doc)
                self.assert_reachability_ordering(doc)

    def test_required_reachability_vectors_exist(self):
        expected = {
            "cycle-termination.json",
            "multi-root-partial.json",
            "reachable-single-root.json",
            "self-loop.json",
            "unreachable-disconnected.json",
        }
        actual = {path.name for path in (FIXTURES / "reachability").glob("*.json")}
        self.assertEqual(actual, expected)

    def test_reachability_hash_vectors_are_stable(self):
        import hashlib

        for path in sorted((FIXTURES / "reachability").glob("*.json")):
            with self.subTest(path=path):
                doc = load_json(path)
                self.assertFalse(self.canonical_bytes(doc).endswith(b"\n"))
                self.assertEqual(
                    "sha256:" + hashlib.sha256(self.canonical_bytes(doc)).hexdigest(),
                    doc["reachability_result_hash"],
                )

    def test_reachability_schema_excludes_forbidden_terms(self):
        schema_text = json.dumps(load_json(REACHABILITY_SCHEMA_PATH)).lower()
        fixture_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in (FIXTURES / "reachability").glob("*.json"))
        for term in self.FORBIDDEN_REACHABILITY_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, schema_text)
                self.assertNotIn(term, fixture_text)


@unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
class DependencyPredicateSchemaContractTests(unittest.TestCase):
    FORBIDDEN_DEPENDENCY_TERMS = {
        "absolute_path",
        "timestamp",
        "environment",
        "random",
        "authorization",
        "authority",
        "proof",
        "governance",
        "policy",
        "execution",
        "mutation",
        "continuityos",
        "unknown",
    }
    VALID_FIXTURES = {
        "bridge-dependency.json",
        "dependency-false.json",
        "dependency-hash.json",
        "dependency-true.json",
        "multiple-candidate-dependency.json",
        "redundant-topology.json",
        "root-dependency.json",
        "target-dependency.json",
    }
    INVALID_FIXTURES = {
        "invalid-projected-ir-rejection.json",
        "invalid-reachability-result-rejection.json",
    }

    SET_LIKE_DEPENDENCY_ARRAYS = ("candidate_set", "reachable_after_projection", "roots")

    def diagnostic_sort_key(self, diagnostic):
        subject = diagnostic["subject"]
        return (diagnostic["code"], diagnostic["severity"], subject["kind"], subject["id"])

    def canonical_dependency_payload(self, doc):
        """Return the canonical dependency result payload used for equality and hashing.

        This is not a predicate evaluator or compiler implementation. It only
        applies the documented dependency_result_hash boundary to static
        dependency-result fixtures: remove the derived hash field, canonicalize
        set-like arrays, canonicalize deterministic diagnostics, and leave all
        remaining structural fields unchanged for sorted-key JSON emission.
        """
        payload = copy.deepcopy(doc)
        payload.pop("dependency_result_hash", None)
        for field in self.SET_LIKE_DEPENDENCY_ARRAYS:
            if field in payload:
                payload[field] = sorted(set(payload[field]))
        if "diagnostics" in payload:
            payload["diagnostics"] = sorted(payload["diagnostics"], key=self.diagnostic_sort_key)
        return payload

    def canonical_dependency_bytes(self, doc):
        """Contract helper for fixture comparison only."""
        return json.dumps(
            self.canonical_dependency_payload(doc),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def assert_dependency_ordering(self, doc):
        self.assertEqual(doc["roots"], sorted(set(doc["roots"])))
        self.assertEqual(doc["candidate_set"], sorted(set(doc["candidate_set"])))
        self.assertEqual(doc["reachable_after_projection"], sorted(set(doc["reachable_after_projection"])))
        self.assertEqual(doc["diagnostics"], sorted(doc["diagnostics"], key=self.diagnostic_sort_key))

    def test_dependency_schema_validates(self):
        Draft202012Validator.check_schema(load_json(DEPENDENCY_SCHEMA_PATH))

    def test_dependency_fixtures_validate(self):
        validator = json_schema_validator(DEPENDENCY_SCHEMA_PATH)
        for path in sorted((FIXTURES / "dependency").glob("*.json")):
            if path.name in self.INVALID_FIXTURES:
                continue
            with self.subTest(path=path):
                doc = load_json(path)
                validator.validate(doc)
                self.assert_dependency_ordering(doc)

    def test_required_dependency_vectors_exist(self):
        actual = {path.name for path in (FIXTURES / "dependency").glob("*.json")}
        self.assertEqual(actual, self.VALID_FIXTURES | self.INVALID_FIXTURES)

    def test_predicate_truth_table_matches_fixtures(self):
        for path in sorted((FIXTURES / "dependency").glob("*.json")):
            if path.name in self.INVALID_FIXTURES:
                continue
            with self.subTest(path=path):
                doc = load_json(path)
                if doc["reachable_after_projection"] == []:
                    self.assertTrue(doc["dependency"])
                    self.assertEqual(doc["dependency_reason"], "no_structurally_valid_path_after_projection")
                    self.assertIn("DEPENDENCY.EMPTY_REACHABILITY", [d["code"] for d in doc["diagnostics"]])
                else:
                    self.assertFalse(doc["dependency"])
                    self.assertEqual(doc["dependency_reason"], "structurally_valid_path_remaining_after_projection")
                    self.assertIn("DEPENDENCY.REACHABILITY_REMAINING", [d["code"] for d in doc["diagnostics"]])

    def test_dependency_equality_is_deterministic_and_candidate_order_insensitive(self):
        import hashlib

        doc = load_json(FIXTURES / "dependency" / "multiple-candidate-dependency.json")
        reordered = dict(doc)
        reordered["candidate_set"] = list(reversed(doc["candidate_set"]))
        self.assertEqual(
            self.canonical_dependency_payload(reordered),
            self.canonical_dependency_payload(doc),
        )
        self.assertEqual(
            "sha256:" + hashlib.sha256(self.canonical_dependency_bytes(reordered)).hexdigest(),
            doc["dependency_result_hash"],
        )

    def test_dependency_result_hash_matches_canonical_fixture(self):
        import hashlib

        doc = load_json(FIXTURES / "dependency" / "dependency-hash.json")
        self.assertFalse(self.canonical_dependency_bytes(doc).endswith(b"\n"))
        self.assertEqual(
            "sha256:" + hashlib.sha256(self.canonical_dependency_bytes(doc)).hexdigest(),
            doc["dependency_result_hash"],
        )

    def test_invalid_projected_ir_is_rejected(self):
        validator = json_schema_validator(DEPENDENCY_SCHEMA_PATH)
        with self.assertRaises(ValidationError):
            validator.validate(load_json(FIXTURES / "dependency" / "invalid-projected-ir-rejection.json"))

    def test_invalid_reachability_result_is_rejected(self):
        validator = json_schema_validator(DEPENDENCY_SCHEMA_PATH)
        with self.assertRaises(ValidationError):
            validator.validate(load_json(FIXTURES / "dependency" / "invalid-reachability-result-rejection.json"))

    def test_forbidden_runtime_authority_governance_proof_fields_remain_excluded(self):
        schema_text = json.dumps(load_json(DEPENDENCY_SCHEMA_PATH)).lower()
        fixture_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in (FIXTURES / "dependency").glob("*.json"))
        for term in self.FORBIDDEN_DEPENDENCY_TERMS:
            with self.subTest(term=term):
                self.assertNotIn(term, schema_text)
                self.assertNotIn(term, fixture_text)


if __name__ == "__main__":
    unittest.main()



def canonical_hash(doc):
    payload = json.loads(json.dumps(doc))
    payload.pop("projected_ir_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    import hashlib
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


class ProjectionContractTests(unittest.TestCase):
    """Contract helpers only; these tests do not implement a projection engine."""

    def projection_paths(self):
        return sorted((FIXTURES / "projection").glob("*.json"))

    @unittest.skipIf(Draft202012Validator is None, "jsonschema is not installed")
    def test_projection_schema_and_fixtures_validate(self):
        validator = json_schema_validator(PROJECTION_SCHEMA_PATH)
        paths = self.projection_paths()
        self.assertGreaterEqual(len(paths), 10)
        for path in paths:
            with self.subTest(path=path):
                validator.validate(load_json(path))

    def test_projected_ir_invariants_hold_for_success_fixtures(self):
        for path in self.projection_paths():
            doc = load_json(path)
            if "projected_ir" not in doc:
                continue
            with self.subTest(path=path):
                ir = doc["projected_ir"]
                component_ids = [c["id"] for c in ir["components"]]
                edge_ids = [e["id"] for e in ir["edges"]]
                self.assertEqual(component_ids, sorted(component_ids))
                self.assertEqual(edge_ids, sorted(edge_ids))
                self.assertEqual(len(component_ids), len(set(component_ids)))
                self.assertEqual(len(edge_ids), len(set(edge_ids)))
                component_set = set(component_ids)
                for edge in ir["edges"]:
                    self.assertIn(edge["from"], component_set)
                    self.assertIn(edge["to"], component_set)
                self.assertEqual(ir["topology_id"], doc["topology_id"])
                self.assertEqual([w["id"] for w in ir["workloads"]], sorted(w["id"] for w in ir["workloads"]))

    def test_incident_edges_removed_and_unaffected_structure_remains(self):
        doc = load_json(FIXTURES / "projection" / "remove-non-critical-component.json")
        ir = doc["projected_ir"]
        self.assertEqual([c["id"] for c in ir["components"]], ["api", "client", "db"])
        self.assertEqual([e["id"] for e in ir["edges"]], ["api-db", "client-api"])
        self.assertNotIn("cache", ir["adjacency"])
        self.assertEqual(ir["workloads"][0]["candidate_set"], ["cache"])

    def test_candidate_ordering_does_not_affect_projected_ir_identity(self):
        left = load_json(FIXTURES / "projection" / "remove-multiple-components.json")
        right = json.loads(json.dumps(left))
        right["candidate_set"] = list(reversed(right["candidate_set"]))
        self.assertEqual(left["projected_ir"], right["projected_ir"])
        self.assertEqual(left["projected_ir"]["components"], right["projected_ir"]["components"])
        self.assertEqual(left["projected_ir"]["edges"], right["projected_ir"]["edges"])
        self.assertEqual(canonical_hash(left["projected_ir"]), canonical_hash(right["projected_ir"]))

    def test_projected_ir_hash_matches_canonical_fixture(self):
        doc = load_json(FIXTURES / "projection" / "projected-ir-hash.json")
        self.assertEqual(doc["projected_ir_hash"], canonical_hash(doc["projected_ir"]))

    def test_projection_rejection_diagnostics_are_structural(self):
        expectations = {
            "unknown-candidate-rejection.json": "PROJECTION.UNKNOWN_COMPONENT",
            "duplicate-candidate-rejection.json": "PROJECTION.DUPLICATE_CANDIDATE",
        }
        for filename, code in expectations.items():
            with self.subTest(filename=filename):
                doc = load_json(FIXTURES / "projection" / filename)
                self.assertNotIn("projected_ir", doc)
                self.assertEqual(doc["diagnostics"][0]["code"], code)

    def test_forbidden_runtime_authority_governance_proof_fields_excluded(self):
        forbidden = {"runtime", "authority", "governance", "proof", "policy", "execution", "mutation", "generated_at", "machine_path"}
        for path in self.projection_paths():
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                for field in forbidden:
                    self.assertNotRegex(text, rf'"{field}"\s*:')
