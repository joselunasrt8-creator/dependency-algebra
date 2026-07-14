# Issue 83 Cross-Repository Conformance Adapter

## Boundary

The Issue #83 adapter is implemented in `conformance/foundation_adapter.py` as
`run_paper1_dependency_conformance`. It is a deterministic comparison wrapper
for one canonical research fixture:

```text
structural-analysis-foundations/conformance/fixtures/dependency-predicate.fixture.json
  -> SYNAPSE topology representation
  -> parse_topology / validate_and_normalize
  -> CanonicalIR
  -> core_analysis_registry().get("dependency-algebra.dependency-analysis")
  -> DependencyAnalysisPass
  -> validate_analysis_result
  -> compile_structural_evidence_artifact
  -> synapse.cross-repository-conformance-result.v1
```

Structural Analysis Foundations owns the research object, fixture, canonical
schema, normative statement, and expected semantics. SYNAPSE owns parsing,
normalization, CanonicalIR, analysis registration, dependency analysis, result
validation, and structural evidence generation.

The adapter owns only deterministic representation translation, lineage
binding, expected-versus-actual comparison, and conformance reporting.

## Supported Case

- Research object: `definition.dependency.dependency-predicate`
- Fixture: `paper1.dependency-predicate.basic-v1`
- Normative reference:
  `paper-1-dependency/research-objects/definition.dependency.dependency-predicate.json#canonical_statement`
- SYNAPSE analysis: `dependency-algebra.dependency-analysis`
- SYNAPSE evidence API: `compile_structural_evidence_artifact`

The adapter preserves fixture edge order in the translated source topology.
SYNAPSE normalization then owns CanonicalIR ordering and normalized identity.

## Result

The emitted result is canonical JSON with schema version
`synapse.cross-repository-conformance-result.v1` and includes repository
commits, fixture identity, normative reference, analysis identity, source
fixture hash, normalized IR hash, result hash, structural evidence artifact
hash, expected and actual classification, verdict, diagnostics, and the
traceability chain.

The status model is:

```text
PASS
DRIFT
FAIL
BLOCKED
NOT_APPLICABLE
UNOBSERVED
```

Issue #83 currently uses `PASS`, `FAIL`, and `NOT_APPLICABLE` for the declared
positive and negative cases. Missing evidence is never reported as `PASS`.

## Validation

Run the focused conformance suite twice:

```bash
python -m pytest tests/cross_repository_conformance_tests.py
python -m pytest tests/cross_repository_conformance_tests.py
```

The suite covers the positive canonical fixture and deterministic failures for
unknown research object, unsupported fixture version, malformed fixture, missing
normative reference, missing registered analysis, source hash mismatch,
normalized IR hash mismatch, malformed analysis result, expected classification
mismatch, and repeated-run divergence.
