# SYNAPSE

<p align="center">
  <img
    src="FEE00044-FF76-4C31-8D1C-E534773819C2.png"
    alt="SYNAPSE — Structural Analysis Engine & Framework"
    width="100%">
</p>

## Structural Analysis Engine & Framework

> From questions to trusted structural insight.

SYNAPSE is a general-purpose structural analysis framework for transforming topology into deterministic structural insight through formal mathematical models, compiler architecture, and reusable analysis engines.

The Dependency Algebra Compiler is the first structural compiler implemented within SYNAPSE and serves as the current reference implementation.

---

## Current Status

SYNAPSE has reached the **architecture-closure compiler milestone** for its first reference implementation. The current implementation includes:

- frozen schemas and fixtures
- frontend validator and normalizer
- canonical IR
- immutable typed compiler artifacts
- projection
- reachability
- predicate
- classification
- serialization boundary
- deterministic hash receipts
- thin CLI / argparse adapter
- compatibility APIs

The implemented surface remains a structural compiler facade, analysis engine, canonical serialization utilities, and a thin CLI harness. It does not add GitHub Actions, ContinuityOS integration, a proof system, authority module, runtime hook, governance surface, policy surface, or external-state mutation surface.

---

## Vision

SYNAPSE is the long-term framework for converting structured questions about systems into deterministic structural analysis.

```text
Question
    ↓
Mathematical Model
    ↓
Formal Specification
    ↓
Compiler
    ↓
Structural Analysis Engine
    ↓
Applications
```

Dependency Algebra is the first implemented formalism within this framework. It defines the current reference path from topology contracts through structural compiler artifacts and deterministic analysis results.

---

## Repository Boundary

### This repository owns

- topology JSON contracts
- mathematical definitions
- parser / AST / IR contracts
- reachability semantics
- complement projection semantics
- dependency predicate semantics
- structural classification semantics
- deterministic compiler artifact schemas
- canonical fixtures
- conformance tests

### This repository does not own

- ContinuityOS governance validation
- execution eligibility
- runtime authorization
- proof generation
- authority propagation
- runtime policy
- mutation execution
- external-state mutation

`VALID`, `DEGRADED`, and `NULL` are **structural classifications only**. They are **not** governance decisions, execution authorizations, runtime proofs, or legitimacy results.

---

## Compiler Pipeline

```text
Raw Input
    ↓
Frontend Validation
    ↓
Canonical IR
    ↓
Projection
    ↓
Reachability
    ↓
Predicate
    ↓
AnalysisResult
    ↓
Serialization
    ↓
Hash Receipt
    ↓
CLI / Public API
```

Compiler stages exchange immutable typed artifacts. Serialization owns representation by converting typed artifacts into dictionaries and canonical JSON. Hashing owns artifact identity across serialized payload boundaries. Compatibility APIs cross the serialization boundary explicitly so public functions and CLI output remain dictionary- and JSON-shaped while the core compiler remains artifact-oriented.

---

## Long-Term SYNAPSE Architecture

```text
Topology
    ↓
Structural Compiler
    ↓
Structural Analysis Engine
    ↓
Visualization
    ↓
Optimization
    ↓
Simulation
```

The current repository implements the compiler layer of this architecture. Visualization, optimization, simulation, runtime policy, authority propagation, and external-state mutation remain outside this repository boundary.

---


## SYNAPSE CLI

Issue #57 owns the active CLI implementation surface. The stable command shape is:

```bash
python -m dependency_algebra.cli compile --input fixtures/basic.json --output out/artifact.json
```

The command is exposed with `prog` name `synapse`; packaging a console script named `synapse` is intentionally deferred to the distribution and release issue. The CLI compiles canonical topology JSON into the deterministic structural evidence artifact and writes no success output to stdout or stderr. Diagnostics are canonical machine-readable JSON on stderr.

Stable exit codes:

| Code | Meaning |
| ---: | --- |
| 0 | Success |
| 1 | Input, schema, or validation failure |
| 2 | Compiler semantic failure |
| 3 | Artifact emission failure |
| 4 | Unexpected runtime failure |

The CLI never mutates input files and does not perform cross-repository conformance, packaging, release, publishing, or GitHub Action integration.

## Validation

Validation is intentionally layered:

- JSON Schema structural validation
- deterministic semantic validation
- conformance suite

Run the conformance suite:

```bash
python -m unittest discover -s tests -p '*_tests.py'
```

---

## Contracts

All contracts are structural-analysis contracts only. They do not introduce governance, proof, authority, execution, policy, runtime, or mutation behavior.

### `AST_IR_CONTRACT.md`

- **Purpose:** Defines the compiler architecture boundary between source topology and normalized analysis representation.
- **Boundary:** AST remains source-faithful and diagnostic-oriented; IR is canonical, normalized, and analysis-ready. Normalized IR equality is based on canonical UTF-8 JSON bytes with sorted object keys, compact separators, canonical set ordering, and no trailing newline. `normalized_ir_hash` is SHA-256 over that canonical normalized IR hash payload.
- **Current status:** Frozen planning contract from Issue #10.

### `REACHABILITY_CONTRACT.md`

- **Purpose:** Defines canonical `Reach(W)` semantics.
- **Boundary:** Reachability is a per-workload, directed-edge, path-existence contract over normalized IR. It defines deterministic multi-root handling, unreachable results, cycle termination, self-loop handling, disconnected-component behavior, result shape, ordering, and hash boundaries.
- **Current status:** Frozen planning contract from Issue #11.

### `COMPILER_FRONTEND_CONTRACT.md`

- **Purpose:** Closes pre-implementation frontend planning gaps.
- **Boundary:** Defines parser diagnostic taxonomy, AST construction rules, normalization design rules, diagnostic ordering, diagnostic schema boundaries, and diagnostics-only conformance vectors.
- **Current status:** Contract-only frontend specification.

### `COMPLEMENT_PROJECTION_CONTRACT.md`

- **Purpose:** Defines canonical `¬S` complement projection semantics.
- **Boundary:** Complement projection is a deterministic, structural-only transformation from normalized IR plus a component candidate set to projected normalized IR. It removes candidate components and incident edges, preserves unaffected graph structure and workload definitions, defines `projected_ir_hash`, and emits structural diagnostics only.
- **Current status:** Frozen planning contract from Issue #12.

## Structural Analysis Foundation conformance

The canonical conformance path is registration-driven and deterministic:

```text
Research object registration
→ canonical fixture discovery
→ fixture/schema validation
→ adapter invocation
→ canonical evidence validation
→ deterministic normalization
→ semantic comparison
→ conformance classification
→ deterministic report generation
→ CI artifact preservation
```

Foundation-owned contracts live in this repository: research-object projection registration under `conformance/research_objects/`, canonical fixtures under `conformance/fixtures/`, conformance evidence/report schemas under `schemas/`, comparison rules in `conformance/compare.py`, orchestration in `conformance/runner.py`, and the command entry point `python -m conformance`. Participating repositories own their implementation-specific execution and adapters; adapters must not redefine canonical fixture semantics or comparison logic.

Adapters are discovered from `conformance/adapters.json`. Each adapter command receives `--fixture`, `--output`, and `--adapter-id`, must leave the canonical fixture immutable, and must emit canonical evidence with implementation identity, version or commit provenance, research-object ID, fixture ID, normalized evidence, diagnostics, and explicit blocked/unsupported states. Raw implementation output is not canonical evidence until it validates against `schemas/conformance-evidence.schema.json` and passes fixture identity checks.

The harness result taxonomy is `PASS`, `DRIFT`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`, and `UNOBSERVED`. `DRIFT` means validated evidence differs semantically from the canonical fixture expectation. `FAIL` means adapter execution or evidence validation failed. `BLOCKED`, `NOT_APPLICABLE`, and `UNOBSERVED` are never treated as `PASS`.

Local validation commands:

```bash
python tools/validate_research_objects.py
python tools/validate_canonical_fixtures.py
python -m conformance
python -m unittest discover -s tests -p '*_tests.py'
```

The deterministic machine-readable report is written to `conformance_artifacts/report.json`. CI validates research-object registration, validates canonical fixtures, runs the harness, runs the unit suite, and uploads the report as a workflow artifact. To add a research object, add a projection module that self-registers through the existing registry and add canonical fixtures. To add a repository adapter, add adapter metadata to the adapter registry; do not copy canonical comparison or fixture semantics into the participating repository.
