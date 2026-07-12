# SYNAPSE Open Issues Current-State Audit

## 1. Executive summary

This audit compares the open SYNAPSE issue backlog visible from GitHub issue search on 2026-07-12 against the current repository state on the checked-out default/work branch. It is an audit and planning artifact only: no code was implemented, no issue body was rewritten, and no GitHub issue was closed.

Executable repository evidence shows that SYNAPSE already has a working package/CLI surface, canonical topology-to-IR normalization, deterministic canonical JSON serialization and hashing, structural evidence artifact emission, dependency-predicate computation, reachability-profile projection, automatic research-object projection discovery, a foundation conformance adapter, CI test/package workflows, and a Python package console script. The backlog still contains broad architecture, conformance, benchmark, scope, and projection issues whose acceptance criteria are only partially satisfied because the current repo lacks a full conformance runner, CI artifact preservation/upload contract, benchmark/reference corpus, minimal-cut projection implementation, formal release/versioning policy, and complete handoff documentation.

**Final determination: `PARTIAL`.** The backlog can be compressed, but not fully: several issues are ready to close as completed or superseded by merged implementation surfaces, while issue families #78, #80, #81, #82, #83, and #100 still contain unresolved contract/productization work.

## 2. Open-issue inventory

GitHub issue search exposed these open issues for `joselunasrt8-creator/SYNAPSE` during this audit. Objective and acceptance criteria are summarized from issue titles and visible descriptions where available, then reconciled against the repository.

| Domain | Issue | Title | Objective | Acceptance criteria / dependencies / related PRs / overlap | Current implementation surfaces |
|---|---:|---|---|---|---|
| architecture and scope | #7 | Formalize Core Algebra Definition | Define dependency algebra semantics. | Depends on canonical terminology and executable predicate semantics; overlaps #82 and current compiler/predicate work. | `DEPENDENCY_PREDICATE_CONTRACT.md`, `dependency_algebra/predicate.py`, tests. |
| architecture and scope | #17 | Draft Architecture Closure Report | Record architecture closure and follow-ups. | Acceptance is documentation/report publication; likely related to closure docs. | `ARCHITECTURE_CLOSURE_REPORT.md`. |
| documentation | #18 | Define Dependency Algebra terminology glossary | Stabilize terms. | Depends on scope terminology; overlaps #82. | `SPEC.md`, `BOUNDARY.md`, `README.md`, contract docs. |
| packaging and release | #23 | Add pyproject.toml metadata | Package metadata. | Requires project metadata and build backend. | `pyproject.toml`. |
| compiler and CLI | #24 | Expose dependency-algebra CLI entrypoint | Console entry point. | Requires package script/CLI command. | `pyproject.toml`, `dependency_algebra/cli.py`. |
| compiler and CLI | #25 | Implement basic CLI argument parsing | Stable CLI arguments and diagnostics. | Depends on CLI. | `dependency_algebra/cli.py`, `tests/cli_tests.py`. |
| compiler and CLI | #26 | Add machine-readable output option | JSON output artifact. | Depends on compiler artifact emission. | `dependency_algebra/cli.py`, `dependency_algebra/serialization.py`. |
| packaging and release | #27 | Add Python package import surface | Public import API. | Requires package exports. | `dependency_algebra/__init__.py`. |
| packaging and release | #28 | Define initial package version | Version surface. | Requires version field. | `pyproject.toml`, `dependency_algebra/version.py`. |
| documentation | #29 | Add minimal README usage example | Document package/CLI. | Depends on CLI/package. | `README.md`. |
| packaging and release | #30 | Add minimal packaging smoke test | Validate build/package metadata. | Depends packaging workflow/tests. | `.github/workflows/package.yml`, `tests/architecture_tests.py`. |
| compiler and CLI | #31 | Define CLI exit codes | Stable exit code contract. | Depends CLI diagnostics. | `dependency_algebra/cli.py`, `README.md`. |
| architecture and scope | #32 | Add architecture boundary document | State boundaries. | Overlaps #82. | `BOUNDARY.md`, `ARCHITECTURE_CLOSURE_REPORT.md`. |
| schemas and evidence contracts | #60 | Implement Shared Evidence Envelope | Common evidence envelope. | Dependencies: artifact schema/provenance; overlaps #78 and #83. | `schemas/artifact.schema.json`, `conformance/foundation_adapter.py`. |
| research-object projections | #69 | Register Dependency Predicate as Research Object | Register dependency predicate projection. | Related PRs likely #96/#98; overlaps registry issues. | `conformance/research_objects/dependency_predicate.py`, registry/discovery. |
| research-object projections | #71 | Self-register Dependency Predicate projection | Projection module self-registration. | Depends registry. Related PR #96. | `conformance/research_objects/dependency_predicate.py`. |
| research-object projections | #72 | Add Research Object Projection Registry | Handler registry. | Related PR #96. | `conformance/research_objects/registry.py`. |
| research-object projections | #73 | Auto-discover projection modules | Import modules automatically. | Related PR #98. | `conformance/research_objects/discovery.py`, registry discovery. |
| research-object projections | #74 | Register Reachability Profile as Research Object | Reachability profile projection. | Related PR #103. | `conformance/research_objects/reachability_profile.py`, test file. |
| conformance | #75 | Add conformance artifact for Reachability Profile | Produce/test reachability conformance artifact. | Depends reachability projection and adapter. | `conformance/research_objects/reachability_profile.py`, `tests/reachability_profile_conformance_tests.py`. |
| schemas and evidence contracts | #78 | Canonical Structural Evidence Artifact Contract | Canonical artifact schema/contract. | Foundational for #81/#83/#100. Overlaps #60. | `schemas/artifact.schema.json`, `compile_artifact`, `README.md`. |
| benchmarks and fixtures | #80 | Benchmark and Reference Corpus | Corpus for deterministic/conformance runs. | Depends canonical contracts and fixtures. | Many fixtures exist, but no benchmark corpus contract/runner. |
| conformance | #81 | Representation-Invariance Conformance Suite | Verify equivalent inputs produce invariant canonical outputs. | Depends canonical serialization/hash and fixtures; no full suite/runner. | Determinism fixtures and tests. |
| architecture and scope | #82 | Scope, Terminology, and Ecosystem Handoff Specification | Define SYNAPSE vs external repo responsibilities. | Foundational for closure and avoiding external responsibility creep. | `BOUNDARY.md`, `SPEC.md`, `ARCHITECTURE_CLOSURE_REPORT.md`, `README.md`. |
| ecosystem integration | #83 | Foundation Conformance Adapter | Adapter to Foundation/Structural Analysis fixtures. | Depends #78 and registry. | `conformance/foundation_adapter.py`. |
| research-object projections | #100 | Minimal Cut Projection | Implement minimal-cut research object projection. | Depends canonical artifact and projection registry; related PR #103 only covers reachability profile. | No minimal-cut module/schema/test found. |

## 3. Current capability map

| Capability requested in audit | Current state | Evidence |
|---|---|---|
| Package and CLI surfaces | Implemented. | `pyproject.toml` declares project metadata and `synapse` console script; `dependency_algebra/cli.py` defines `synapse compile`. |
| Public API | Implemented. | Package facade exports compiler APIs and diagnostics. |
| Canonical structural artifact schema | Partial/implemented baseline. | `compile_artifact` emits `dependency-algebra.artifact.v1`; schema file exists. |
| Canonical serialization and hashing | Implemented. | `canonical_json_bytes/text`, `sha256_digest`, stage-specific hash helpers. |
| Deterministic replay | Partial. | Canonical ordering, hashes, fixtures, and tests exist; no replay runner or artifact-preservation workflow. |
| Representation invariance | Partial. | Reordered fixture and deterministic serialization tests exist; no full conformance suite. |
| Research-object registry | Implemented. | Registry, registration, and discovery modules exist. |
| Self-registration | Implemented. | Projection modules call `register(...)`. |
| Automatic projection discovery | Implemented. | Discovery imports projection modules via `pkgutil`. |
| Dependency-predicate projection | Implemented. | Projection module exists and is registered. |
| Reachability-profile projection | Implemented. | Projection module and conformance tests exist. |
| Minimal-cut projection | Not started. | No `minimal_cut` projection module or tests found. |
| Foundation adapter | Partial. | Adapter exists, but commit/branch are hard-coded placeholders and no CI artifact preservation is present. |
| Shared evidence envelope | Partial. | Adapter emits envelope-like evidence; no shared reusable envelope abstraction/contract. |
| Conformance runner | Partial/not complete. | Unit tests exist; no generic conformance runner CLI found. |
| CI artifact preservation | Not started. | Workflows run tests/package checks but do not upload conformance artifacts. |
| Benchmark corpus | Partial. | Fixtures exist; no explicit benchmark/reference corpus manifest. |
| Handoff documentation | Partial. | Boundary/spec/readme exist; no complete ecosystem handoff spec. |
| Scope and terminology specification | Partial. | Boundary/spec terminology exists; likely insufficient for #82 full scope. |
| Versioning and release policy | Partial. | Static package version exists; no release policy doc. |

## 4. Issue-by-issue evidence matrix

| Issue | Requested capability | Status | Implementation evidence | Test evidence | Documentation evidence | Remaining gap | Recommended action |
|---:|---|---|---|---|---|---|---|
| #7 | Core algebra definition | PARTIAL | Predicate/compiler implementation exists. | Predicate-related tests via architecture/schema/CLI coverage. | Contract docs exist. | Formal canonical algebra spec may remain broader than implementation. | KEEP_OPEN or REWRITE_SCOPE |
| #17 | Architecture closure report | COMPLETE | N/A documentation deliverable. | N/A | Closure report exists. | None if report publication was sole criterion. | CLOSE_COMPLETED |
| #18 | Terminology glossary | PARTIAL | N/A | N/A | Several docs define terms. | No single glossary/handoff terminology artifact. | SPLIT_REMAINDER or merge into #82 |
| #23 | pyproject metadata | COMPLETE | `pyproject.toml` has build/project metadata. | Packaging workflow. | README packaging notes. | None. | CLOSE_COMPLETED |
| #24 | CLI entrypoint | COMPLETE | Console script and CLI module. | CLI tests. | README CLI docs. | None. | CLOSE_COMPLETED |
| #25 | CLI argument parsing | COMPLETE | Argparse parser with compile args. | CLI tests. | README CLI docs. | None. | CLOSE_COMPLETED |
| #26 | Machine-readable output | COMPLETE | Canonical JSON artifact output and diagnostics. | CLI/schema tests. | README. | None. | CLOSE_COMPLETED |
| #27 | Python import surface | COMPLETE | Package facade. | Import exercised by tests. | README. | None. | CLOSE_COMPLETED |
| #28 | Initial package version | COMPLETE | Version file and package metadata. | Architecture/package checks. | README. | Release policy still separate. | CLOSE_COMPLETED |
| #29 | Minimal README usage | COMPLETE | N/A | N/A | README usage sections. | None. | CLOSE_COMPLETED |
| #30 | Packaging smoke test | COMPLETE | Package workflow. | Package workflow and tests. | N/A | None. | CLOSE_COMPLETED |
| #31 | CLI exit codes | COMPLETE | Exit constants and mapped error paths. | CLI tests. | README exit code docs. | None. | CLOSE_COMPLETED |
| #32 | Architecture boundary document | COMPLETE | N/A | Boundary tests. | Boundary document and closure report. | Broader ecosystem handoff remains #82. | CLOSE_COMPLETED |
| #60 | Shared evidence envelope | PARTIAL | Artifact provenance and adapter envelope. | Adapter not generically tested as shared envelope. | Schema/docs. | Reusable shared envelope schema/API and tests. | KEEP_OPEN or SPLIT_REMAINDER |
| #69 | Dependency Predicate research object | COMPLETE | Projection module exists. | Foundation/registry path indirectly covered. | README/conformance docs limited. | None for registration. | CLOSE_COMPLETED |
| #71 | Self-register dependency projection | COMPLETE | Module calls `register`. | Discovery/adapter path. | N/A | None. | CLOSE_COMPLETED |
| #72 | Projection registry | COMPLETE | Registry exists. | Used by adapter/tests. | N/A | None. | CLOSE_COMPLETED |
| #73 | Auto-discovery | COMPLETE | Discovery imports modules automatically. | Used by adapter/tests. | N/A | None. | CLOSE_COMPLETED |
| #74 | Reachability Profile research object | COMPLETE | Projection module exists and registers. | Reachability profile conformance tests. | N/A | None for projection. | CLOSE_COMPLETED |
| #75 | Reachability conformance artifact | COMPLETE | Adapter plus projection produce evidence. | Dedicated tests. | N/A | If issue required CI artifact uploads, gap belongs #81/#83. | CLOSE_COMPLETED |
| #78 | Canonical artifact contract | PARTIAL | Artifact emitter/schema exist. | Schema tests. | README/docs. | Contract likely needs frozen schema/examples/versioning and conformance artifacts. | KEEP_OPEN |
| #80 | Benchmark/reference corpus | PARTIAL | Rich fixtures exist. | Tests consume fixtures. | Fixtures docs exist. | No benchmark corpus manifest, expected-output lockfile, or benchmark runner. | KEEP_OPEN |
| #81 | Representation-invariance suite | PARTIAL | Canonical serialization and hashes. | Some deterministic/reordered tests. | Determinism docs. | No complete conformance suite/runner/artifact preservation. | KEEP_OPEN |
| #82 | Scope/terminology/handoff | PARTIAL | Boundary/spec/readme/closure docs. | Boundary tests. | Multiple docs. | No final ecosystem handoff spec mapping Structural Analysis Foundations, SYNAPSE, ContinuityOS, StateGate responsibilities. | KEEP_OPEN |
| #83 | Foundation adapter | PARTIAL | Adapter exists. | Limited conformance tests. | N/A | Placeholder commit/branch, no artifact upload/runner, no external contract fixture manifest. | KEEP_OPEN |
| #100 | Minimal Cut projection | NOT_STARTED | None found. | None found. | None found. | Implement projection, fixtures, registry, tests, docs. | KEEP_OPEN |

## 5. Acceptance-criteria verification

- **Completed packaging/CLI issues (#23-#31)**: SATISFIED. Metadata, console script, import surface, version, argparse command, deterministic JSON output, diagnostics, and exit code constants are present and exercised by CLI/package tests.
- **Architecture report/boundary issues (#17, #32)**: SATISFIED for the narrow deliverables. Broader terminology/handoff work is tracked separately by #18/#82.
- **Research object registry/projection issues (#69, #71, #72, #73, #74, #75)**: SATISFIED for dependency-predicate and reachability-profile registration/discovery/projection behavior. The adapter/projection path is executable, but generalized conformance productization remains under #81/#83.
- **#7 Core Algebra Definition**: PARTIAL. Executable predicate semantics exist, but the acceptance criteria should be rewritten to separate implemented semantics from any remaining formal proof/spec work.
- **#18 Terminology glossary**: PARTIAL. Terminology exists across docs, but no single glossary appears to own the issue.
- **#60 Shared Evidence Envelope**: PARTIAL. Evidence envelope shape appears in the foundation adapter, but there is no reusable shared contract/schema abstraction with dedicated tests.
- **#78 Canonical Structural Evidence Artifact Contract**: PARTIAL. The artifact is executable and hashed, but the issue should remain open until schema fixtures, versioning, examples, and conformance expectations are frozen.
- **#80 Benchmark and Reference Corpus**: PARTIAL. Many fixtures exist; a benchmark/reference corpus manifest and expected canonical outputs are missing.
- **#81 Representation-Invariance Conformance Suite**: PARTIAL. Deterministic hashing/ordering are implemented; the conformance suite is not complete.
- **#82 Scope, Terminology, and Ecosystem Handoff Specification**: PARTIAL. Existing boundary docs help, but the requested four-repository responsibility boundary is not fully codified.
- **#83 Foundation Conformance Adapter**: PARTIAL. Adapter exists; placeholders and missing CI artifact preservation prevent completion.
- **#100 Minimal Cut Projection**: UNSATISFIED. No implementation evidence found.

## 6. Duplicate and supersession analysis

- **#78 vs #60**: Overlapping but not duplicates. #78 owns canonical structural artifact contract; #60 owns shared evidence envelope. Keep both only if #60 is narrowed to reusable envelope semantics outside the artifact body. Otherwise split/merge #60 into #78/#83.
- **#80 vs #81**: Related but not duplicates. #80 is corpus data/manifest; #81 is executable representation-invariance conformance.
- **#81 vs deterministic execution issues**: Current deterministic serialization work satisfies part of #81, but a suite/runner remains.
- **#82 vs #18/#32**: #32 can close as completed boundary document. #18 should either close as duplicate of #82 if glossary scope is absorbed there, or be rewritten to a narrow glossary deliverable.
- **#83 vs earlier adapter/registry/projection issues (#69, #71-#75)**: Earlier registry/projection issues are completed by merged implementation surfaces. #83 should remain open for adapter productization and external conformance packaging.
- **#100 vs reachability/dependency projections**: Not a duplicate. Minimal cut requires different computation/projection and remains open.

## 7. Dependency graph

```text
#82 Scope/terminology/handoff
  -> #7 Core algebra formalization
  -> #78 Canonical structural artifact contract
      -> #60 Shared evidence envelope
      -> #80 Benchmark/reference corpus
      -> #81 Representation-invariance suite
      -> #83 Foundation conformance adapter
      -> #100 Minimal-cut projection

Completed/productized base:
#23 -> #24 -> #25/#26/#31
#27 -> public API users
#28 -> package metadata/version
#69/#71 -> #72 -> #73 -> #74/#75 -> #83
#17/#32 -> #82
```

### Topologically ordered execution queue

1. #82 — finalize SYNAPSE boundary and external handoff responsibilities.
2. #78 — freeze canonical structural evidence artifact contract.
3. #60 — extract/define shared evidence envelope or close into #78/#83.
4. #80 — create benchmark/reference corpus manifest and expected outputs.
5. #81 — implement representation-invariance conformance runner using #80.
6. #83 — productize foundation adapter with real provenance and CI artifact preservation.
7. #100 — implement minimal-cut projection once artifact/projection contracts are frozen.
8. #7/#18 — rewrite or close residual formal terminology/spec tasks after #82.

Boundary preservation:

- Structural Analysis Foundations owns canonical research objects and fixtures.
- SYNAPSE owns deterministic structural computation and evidence generation.
- ContinuityOS owns legitimacy and execution eligibility.
- StateGate owns repository state-transition validation.

## 8. Closure candidates

### Close as completed

#17, #23, #24, #25, #26, #27, #28, #29, #30, #31, #32, #69, #71, #72, #73, #74, #75.

### Close as superseded or duplicate

- #18 may be closed as duplicate/superseded by #82 **only if** #82 is explicitly updated to own the glossary deliverable; otherwise keep #18 open with narrowed scope.
- #60 may be split or partially superseded by #78/#83; do not close until shared envelope acceptance criteria are mapped.

### Keep open

#7, #18 or #82-owned rewrite, #60, #78, #80, #81, #82, #83, #100.

## 9. Remaining actionable issues

- #82: write final scope/terminology/handoff spec for SYNAPSE vs Structural Analysis Foundations, ContinuityOS, and StateGate.
- #78: freeze artifact schema, examples, hash boundaries, provenance semantics, and versioning expectations.
- #60: define reusable shared evidence envelope or close into artifact/adapter scopes.
- #80: add corpus manifest, canonical expected outputs, and benchmark/reference docs.
- #81: build conformance runner for representation invariance over equivalent inputs.
- #83: replace placeholder provenance, run adapter in CI, preserve artifacts.
- #100: implement minimal-cut research-object projection, fixtures, schema/docs, and tests.
- #7/#18: rewrite as residual formal glossary/spec tasks after #82.

## 10. Priority queue

### Priority 1 — #82 Scope, Terminology, and Ecosystem Handoff Specification

Why it matters: removes architecture ambiguity and prevents SYNAPSE from absorbing ContinuityOS, StateGate, or Structural Analysis Foundations responsibilities. Dependencies: existing boundary docs. Expected closure effect: clarifies #7/#18/#60/#78/#83. Recommended next PR scope: `docs: finalize SYNAPSE ecosystem handoff and terminology boundary`.

### Priority 2 — #78 Canonical Structural Evidence Artifact Contract

Why it matters: defines the canonical contract that downstream conformance, corpus, adapter, and projections consume. Dependencies: #82 boundary. Expected closure effect: unblocks #60/#80/#81/#83/#100. Recommended next PR scope: `docs/schemas: freeze structural evidence artifact contract`.

### Priority 3 — #80 Benchmark and Reference Corpus

Why it matters: creates externally testable evidence and avoids duplicate fixture semantics. Dependencies: #78. Expected closure effect: unblocks full #81 and strengthens #83. Recommended next PR scope: `test: add benchmark corpus manifest and canonical expected artifacts`.

### Priority 4 — #81 Representation-Invariance Conformance Suite

Why it matters: proves implementation-independent deterministic behavior. Dependencies: #78/#80. Expected closure effect: converts deterministic claims into executable conformance evidence. Recommended next PR scope: `test: add representation-invariance conformance runner`.

### Priority 5 — #83 Foundation Conformance Adapter

Why it matters: productizes ecosystem integration and artifact preservation. Dependencies: #78/#80/#81. Expected closure effect: creates external adoption path without widening SYNAPSE authority. Recommended next PR scope: `ci: run foundation adapter and upload conformance artifacts`.

### Priority 6 — #100 Minimal Cut Projection

Why it matters: adds a new research-object projection after contracts stabilize. Dependencies: #78 and registry. Expected closure effect: expands externally consumable structural evidence. Recommended next PR scope: `feat: add minimal-cut research object projection`.

## 11. Recommended GitHub actions

1. Close completed issues: #17, #23, #24, #25, #26, #27, #28, #29, #30, #31, #32, #69, #71, #72, #73, #74, #75.
2. Comment on #18 that terminology should be absorbed by #82 or narrowed to a standalone glossary.
3. Comment on #60 that the existing adapter/artifact partially satisfies the issue, but reusable envelope criteria remain.
4. Keep #78, #80, #81, #82, #83, and #100 open.
5. Open the next PR for #82 before implementing more projections or conformance infrastructure.

## 12. Final determination

**Final determination: `PARTIAL`.**

- Issues ready to close as completed: #17, #23, #24, #25, #26, #27, #28, #29, #30, #31, #32, #69, #71, #72, #73, #74, #75.
- Issues ready to close as superseded: none without an explicit maintainer decision; #18 and #60 are candidates for rewrite/split rather than immediate closure.
- Issues that should remain open: #7, #18, #60, #78, #80, #81, #82, #83, #100.
- Highest-leverage next issue: #82 Scope, Terminology, and Ecosystem Handoff Specification.
- Exact recommended next PR title: `docs: finalize SYNAPSE ecosystem handoff and terminology boundary`.
- Evidence gaps that prevented stronger conclusions: complete issue bodies were not locally available; no generic conformance runner was found; no benchmark corpus manifest was found; foundation adapter provenance contains placeholders; workflows do not preserve conformance artifacts; no minimal-cut implementation was found.
