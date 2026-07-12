# Structural Analysis Foundations Issue #27 Audit

## Continuity Coding preamble

- **Intent:** audit the current repository state before any Issue #27 implementation and prevent duplicate authority surfaces.
- **Exact scope:** repository-local evidence only: `conformance/`, `schemas/`, fixtures, adapters, comparator/reporting surfaces, runners/CLIs, tests, workflows, docs, generated artifacts, and reachable Git history on the current branch.
- **Affected files:** this audit report only.
- **Preserved invariants:** canonical semantics remain in repository-owned schemas, fixtures, compiler contracts, and comparison rules; participating repositories own adapter-specific evidence generation; no repository-specific semantics are absorbed into foundation code.
- **Mutation-capable surfaces:** Python compiler modules, conformance adapter modules, CLI entry points, tests, workflows, package metadata, and generated or preserved artifacts. This audit does not mutate those surfaces.
- **Replay implications:** any later implementation must validate the exact object it executes, preserve deterministic canonical JSON and hash boundaries, and avoid wall-clock, environment, path, or random identity fields in canonical results.
- **Proof requirements:** executable tests or commands must prove each conformance claim; documentation alone is not enough.
- **Validation requirements:** at minimum, run the repository test suite and any new conformance command introduced by a future implementation.
- **Unresolved ambiguity:** the full text of Issue #27 and any remote `main` branch are not present in this checkout; there is no configured Git remote and only the local `work` branch is available.

## Phase 1 — Repository audit

### Current execution surfaces

- **Compiler facade:** `dependency_algebra.compiler.compile_artifact` parses topology JSON, validates and normalizes it, runs analysis, emits deterministic artifact fields, and appends `artifact_hash` after hashing the payload.
- **Frontend and normalization:** `dependency_algebra.frontend.parse_topology` and `validate_and_normalize` provide actual JSON parsing, semantic validation, deterministic ordering, adjacency construction, workload normalization, and `normalized_ir_hash` generation.
- **Analysis:** `dependency_algebra.engine.analyze` evaluates reachability and dependency predicate results, then serializes the typed analysis result.
- **Reachability:** `dependency_algebra.reachability.evaluate` and `traverse_edges` implement deterministic traversal over normalized IR.
- **Projection and dependency predicate:** `dependency_algebra.projection.project` and `dependency_algebra.predicate.evaluate` implement complement projection and per-workload dependency results.
- **Serialization and hashing:** `dependency_algebra.serialization` owns canonical JSON encoding and all hash helper boundaries.
- **CLI runner:** `dependency_algebra.cli` exposes `synapse compile` style behavior and deterministic machine-readable diagnostics.
- **Foundation adapter:** `conformance/foundation_adapter.py` converts a research-object fixture into a topology, compiles it, loads a research-object projection, and writes evidence JSON.
- **Research-object projection registry:** `conformance/research_objects/registry.py` and `discovery.py` import projection modules; `dependency_predicate.py` and `reachability_profile.py` register handlers.
- **CI:** `.github/workflows/test.yml` runs the unit suite after installing dev dependencies; `.github/workflows/package.yml` builds the package, installs the wheel, smoke-tests the CLI, and runs tests.

### Existing implementation inventory

| Capability | Status | Repository evidence | Notes |
|---|---:|---|---|
| Research-object discovery | PARTIAL | `conformance/research_objects/discovery.py`, `conformance/research_objects/registry.py` | Projection modules are auto-imported. There is no manifest-driven research-object discovery. |
| Fixture discovery | PARTIAL | `tests/schema_tests.py`, fixture directories, `FIXTURES.md` | Tests glob some canonical topology fixture groups. Research-object fixtures are embedded in tests rather than discovered from manifests. |
| Adapter contracts | PARTIAL | `conformance/foundation_adapter.py`, `tests/reachability_profile_conformance_tests.py` | A concrete SYNAPSE foundation adapter exists. No versioned adapter contract schema or generic external adapter interface exists. |
| Adapter discovery | ABSENT | No generic adapter registry found | Only research-object projection discovery exists. |
| Evidence schemas | PARTIAL | `schemas/artifact.schema.json`, `schemas/reachability.schema.json`, `schemas/dependency.schema.json`, `schemas/projection.schema.json` | Compiler evidence schemas exist. A dedicated cross-repository conformance evidence envelope schema is absent. |
| Schema validation | PARTIAL | `tests/schema_tests.py` | JSON Schema validation is test-level, not a reusable conformance runner command. |
| Normalization | COMPLETE | `dependency_algebra/frontend.py` | Topology-to-IR normalization is implemented and covered by compiler tests. |
| Deterministic comparison | PARTIAL | `dependency_algebra/serialization.py`, determinism tests | Canonical serialization and replay tests exist. A dedicated comparator module comparing submitted evidence to canonical expected evidence is absent. |
| Replay checks | PARTIAL | `tests/cli_tests.py`, `tests/reachability_profile_conformance_tests.py` | Repeated compiler/projection outputs are tested. No harness-level replay command exists. |
| Report generation | ABSENT | No report module or CLI found | No conformance report writer exists. |
| Result classification | COMPLETE | `dependency_algebra/classification.py` | Structural classification is implemented and tested through artifacts. |
| CI enforcement | PARTIAL | `.github/workflows/test.yml`, `.github/workflows/package.yml` | Tests and packaging are enforced; no explicit conformance harness report/artifact workflow exists. |
| Artifact preservation | PARTIAL | `.github/workflows/package.yml` | Build artifacts are produced during package workflow but not uploaded/preserved as conformance artifacts. |
| Cross-repository participation | PARTIAL | `conformance/foundation_adapter.py` evidence metadata | Evidence metadata names SYNAPSE, but no multi-repository registry or participation protocol is implemented. |

## Phase 2 — Architecture reconstruction

```text
Canonical research object
→ fixture
→ schema validation
→ adapter execution
→ normalized evidence
→ comparator
→ conformance determination
→ report
→ CI artifact
```

| Stage | Implementation file | Canonical entry point | Current responsibility | Input contract | Output contract | Test coverage | CI coverage | Classification |
|---|---|---|---|---|---|---|---:|
| Canonical research object | `conformance/research_objects/*.py` | `register(RESEARCH_OBJECT_ID, handler)` | Registers projection behavior for dependency predicate and reachability profile | Compiled artifact plus injected canonical context | Projection fields merged into evidence | Handler discovery and projection tests | Unit suite in CI | PARTIAL |
| Fixture | `fixtures/**`, test-local `canonical_fixture()` | Fixture JSON files or in-test fixture factory | Canonical topology/result vectors and a reachability-profile test fixture | JSON documents or in-memory fixture dicts | Topology/evidence expectations | Schema and conformance tests | Unit suite in CI | PARTIAL |
| Schema validation | `tests/schema_tests.py`, `dependency_algebra/frontend.py` | `json_schema_validator`, `validate_and_normalize` | Validates schema shape in tests and semantic topology constraints in compiler | Topology/result fixture JSON | Validation success or deterministic diagnostics | Schema and CLI tests | Unit suite in CI | PARTIAL |
| Adapter execution | `conformance/foundation_adapter.py` | `main()` with `--fixture` and `--output` | Builds topology from fixture, compiles artifact, projects research-object evidence | Research-object fixture with `fixture_id`, `research_object_id`, timestamp, input | Evidence JSON | Subprocess adapter test | Unit suite in CI | PARTIAL |
| Normalized evidence | `dependency_algebra/compiler.py`, `conformance/foundation_adapter.py` | `compile_artifact`, adapter evidence envelope | Emits deterministic compiler artifact and adapter evidence | Topology JSON bytes plus fixture context | Artifact/evidence dict | CLI, schema, conformance tests | Unit suite and package workflow | PARTIAL |
| Comparator | `dependency_algebra/serialization.py`, projection tests | Canonical JSON equality in tests | Provides deterministic serialization and direct equality checks | JSON-serializable documents | Canonical text/hash/equality in tests | Determinism tests | Unit suite in CI | PARTIAL |
| Conformance determination | `conformance/foundation_adapter.py` | Evidence field `semantic_result` | Currently emits hard-coded `PASS` for adapter success | Adapter execution success | Evidence with `semantic_result` | Adapter test asserts PASS | Unit suite in CI | PARTIAL |
| Report | None | None | No report generator found | Not implemented | Not implemented | None | None | ABSENT |
| CI artifact | `.github/workflows/*.yml` | GitHub Actions jobs | Runs tests/build/smoke tests | Repository checkout | Job logs and package build products | Workflow definitions only | GitHub Actions | PARTIAL |

## Phase 3 — Issue #27 acceptance audit

Because Issue #27 text is not present in the checkout, this table evaluates the acceptance areas named in the prompt rather than hidden issue wording.

| Acceptance criterion | Status | Supporting file or test | Observed behavior | Remaining gap | Smallest valid remediation |
|---|---:|---|---|---|---|
| Discover canonical research objects | PARTIAL | `conformance/research_objects/registry.py`, `discovery.py` | Python modules self-register and can be retrieved by ID | No manifest/catalog authority for research objects | Add a manifest-backed catalog only if Issue #27 requires it; otherwise document registry as current authority |
| Discover fixtures | PARTIAL | `tests/schema_tests.py`, `FIXTURES.md` | Tests discover some fixture directories with globs | No conformance fixture manifest or runner-wide fixture discovery | Add a small fixture manifest/loader if needed, without redefining semantics |
| Define adapter contract | PARTIAL | `conformance/foundation_adapter.py` | One adapter CLI accepts `--fixture` and `--output` | No generic adapter schema/contract for participating repositories | Specify minimal adapter command contract and evidence envelope schema |
| Discover adapters | ABSENT | None found | No registry or configuration for multiple participant adapters | Cross-repository participation cannot be enumerated | Add adapter registry metadata outside semantic schemas |
| Validate evidence schema | PARTIAL | `schemas/artifact.schema.json`, tests | Compiler artifact schema is validated in tests | Adapter evidence envelope lacks schema validation | Add `schemas/conformance-evidence.schema.json` or equivalent if in scope |
| Normalize submitted evidence | PARTIAL | `serialization.canonical_json_*` | Canonical JSON helpers exist | No harness-level normalizer for submitted evidence | Reuse serialization helpers in a comparator module |
| Deterministically compare expected vs observed evidence | PARTIAL | replay/equality tests | Tests compare selected fields and whole projections | No reusable comparator with mismatch diagnostics | Add comparator over canonicalized semantic slices |
| Replay checks | PARTIAL | CLI determinism test; projection replay test | Repeated local execution is byte- or object-stable | No harness command reruns adapters and compares outputs | Add replay mode to future harness runner |
| Generate report | ABSENT | None found | No report surface | No JSON/Markdown conformance report | Add minimal deterministic JSON report writer only after comparator exists |
| Classify conformance result | PARTIAL | hard-coded `semantic_result`; `classification.py` for structural classification | Adapter reports PASS when execution succeeds | No PASS/FAIL/SKIP/ERROR taxonomy tied to comparator outcomes | Add harness result taxonomy distinct from structural `VALID/DEGRADED/NULL` |
| Enforce in CI | PARTIAL | `.github/workflows/test.yml`, `package.yml` | Unit/package checks run | No explicit conformance harness job or artifact upload | Add workflow step after harness CLI exists |
| Preserve artifacts | PARTIAL | package workflow build step | Build products are created transiently | No upload of conformance evidence/report artifacts | Use `actions/upload-artifact` for conformance report outputs |
| Support cross-repository participation | PARTIAL | evidence metadata in adapter | Evidence includes repository fields | No participant registry or external adapter execution model | Add non-semantic participant registry mapping repo to adapter command |

## Phase 4 — Duplication and authority audit

- **Canonical fixture ownership:** currently lives in `fixtures/**` plus a test-local research-object fixture. A new harness must not introduce a second expected-semantics store; if manifests are added, they should point at canonical fixtures rather than duplicate them.
- **Evidence schemas:** compiler artifact/result schemas exist. A conformance envelope schema would be additive if it wraps evidence; it must not redefine artifact, reachability, projection, or dependency semantics.
- **Adapter interfaces:** `conformance/foundation_adapter.py` is a concrete adapter. A generic adapter command contract can be introduced, but repository-specific adapter internals should remain in participating repositories.
- **Comparison logic:** canonical JSON/hash helpers exist and should be reused. A comparator should consume normalized semantic slices rather than inventing new equivalence rules.
- **Result taxonomies:** structural `VALID/DEGRADED/NULL` is not conformance `PASS/FAIL/ERROR/SKIP`. Do not overload one taxonomy with the other.
- **Validation commands:** existing unit tests and CLI validation should not be replaced by a second topology validator. A harness should call or import the existing compiler/schema validation boundaries.
- **Reporting surfaces:** no report surface exists. Add one only as a deterministic output of the comparator and runner.
- **CI workflows:** existing test/package workflows should be extended after a harness command exists, not duplicated as a separate authority over semantics.

## Phase 5 — Minimal implementation plan

This repository is not empty; Issue #27 should be implemented as a thin harness layer over existing compiler, schema, registry, and serialization authorities.

1. **Define the missing harness boundary only.** Add a conformance evidence envelope schema and a tiny result taxonomy that distinguishes harness outcomes from structural classifications.
2. **Create fixture/participant metadata without duplicating semantics.** Add manifest entries that point to canonical fixtures and adapter commands; do not copy expected semantic payloads into the registry.
3. **Add a comparator module.** Reuse `dependency_algebra.serialization.canonical_json_text` and compare declared semantic slices from canonical fixture output to observed adapter evidence.
4. **Add a runner CLI.** Execute configured adapter commands against discovered fixtures, validate evidence envelope shape, compare observed vs expected semantic slices, and emit deterministic JSON report.
5. **Add replay validation.** Run the same adapter/fixture pair twice and require byte-identical normalized semantic evidence or canonical equality when envelope metadata is intentionally excluded.
6. **Extend CI after the runner exists.** Add a workflow step to run the harness and upload the deterministic report as an artifact.

### Planning-only boundary

No implementation beyond this audit report is performed here because the full Issue #27 acceptance text and remote `main` state are unavailable. The smallest safe next mutation is a bounded harness design patch once those acceptance criteria are visible.

## Final implementation evidence

### Implemented gaps

- Added canonical fixture discovery and validation for foundation-owned research-object fixtures.
- Added canonical conformance evidence and report schemas.
- Added adapter registry loading that reuses the existing `conformance/foundation_adapter.py` command interface instead of creating a repository-specific comparison path.
- Added deterministic semantic comparison over normalized evidence slices.
- Added canonical conformance orchestration through `python -m conformance`.
- Added deterministic report generation at `conformance_artifacts/report.json`.
- Added replay validation for adapter evidence.
- Extended existing CI workflows to validate research objects, validate canonical fixtures, run the harness, run tests, and upload the conformance report artifact.

### Changed files

- `conformance/__main__.py`
- `conformance/adapters.json`
- `conformance/adapters.py`
- `conformance/compare.py`
- `conformance/evidence.py`
- `conformance/fixtures.py`
- `conformance/fixtures/dependency-predicate.json`
- `conformance/fixtures/reachability-profile.json`
- `conformance/foundation_adapter.py`
- `conformance/jsonutil.py`
- `conformance/runner.py`
- `conformance/status.py`
- `schemas/conformance-evidence.schema.json`
- `schemas/conformance-report.schema.json`
- `tests/conformance_harness_tests.py`
- `tests/schema_tests.py`
- `tools/validate_research_objects.py`
- `tools/validate_canonical_fixtures.py`
- `.github/workflows/test.yml`
- `.github/workflows/package.yml`
- `README.md`

### Validation commands

- `python tools/validate_research_objects.py`
- `python tools/validate_canonical_fixtures.py`
- `python -m conformance`
- `python -m unittest discover -s tests -p '*_tests.py'`

### Test results

All validation commands passed in this checkout after implementation.

### CI path

The existing `test.yml` and `package.yml` workflows now run research-object validation, canonical-fixture validation, the canonical conformance harness, and the unit suite. Both workflows preserve `conformance_artifacts/report.json` with `actions/upload-artifact` using `if: always()`.

### Acceptance criteria now satisfied

- Research-object registration and validation have an executable command.
- Canonical fixture discovery and validation have an executable command.
- Adapter invocation uses a registry-discovered command and the existing adapter CLI.
- Canonical evidence validation occurs before semantic comparison.
- Deterministic comparison detects drift over normalized evidence.
- Harness classifications distinguish `PASS`, `DRIFT`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`, and `UNOBSERVED`.
- Deterministic reports include aggregate summary, per-research-object status, per-adapter status, comparison matrix, mismatches, blockers, provenance, schema versions, fixture hashes, evidence hashes, and replay result.
- CI validates foundation-owned contracts and preserves the machine-readable report artifact.

### Remaining external repository work

External participating repositories still need to add their own adapters and implementation-specific evidence generation. That work remains outside the Foundation boundary and is not required for Foundation-owned contract closure.

### Final determination

READY_TO_CLOSE for the foundation-owned Issue #27 conformance boundary. External repository adapter adoption may proceed separately through the canonical adapter registry and evidence schema.
