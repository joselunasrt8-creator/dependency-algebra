# SYNAPSE

### Structural Analysis Engine & Framework

> **From Questions to Trusted Insight Across Any System.**

---

## Current Repository

**dependency-algebra** is the reference implementation of the Dependency Algebra Compiler—the first structural compiler within the SYNAPSE framework.

Its responsibility is to transform topology descriptions into deterministic structural-analysis artifacts through reproducible compiler passes.

Current status: **planning-first**, with implementation beginning only after specification stabilization.

---

## Vision

SYNAPSE is a general-purpose structural analysis framework.

Its purpose is to transform topology into deterministic insight through formal mathematical models, compiler architecture, and reusable analysis engines.

Long-term evolution:

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

Dependency Algebra is the first formalism implemented within this framework.

---

## Boundary

Dependency Algebra owns structural analysis only:

- topology JSON contracts
- mathematical definitions
- parser, AST, and IR contracts
- reachability semantics
- complement projection semantics
- dependency predicate semantics
- structural classification semantics
- deterministic compiler artifact schemas
- canonical fixtures
- conformance tests

Dependency Algebra does **not** own:

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

## Current Milestone

This repository is currently in **Milestone 1 — Frozen Schemas and Canonical Fixtures**.

The implemented surface is intentionally schema-only:

- `SPEC.md`
- `BOUNDARY.md`
- `DETERMINISM.md`
- JSON schemas under `schemas/`
- canonical fixtures under `fixtures/`
- schema and boundary conformance tests under `tests/`

No compiler engine, CLI, GitHub Action, ContinuityOS integration, proof system, authority module, runtime hook, or execution surface is included in this milestone.

---

## Canonical Compiler Pipeline

```text
Topology JSON
        ↓
Parser
        ↓
AST
        ↓
IR
        ↓
Reachability
        ↓
Complement Projection
        ↓
Dependency Predicate
        ↓
Compiler Artifact
```

This repository freezes the contracts required before implementing that compiler.

---

## Long-Term Architecture

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

The compiler is one layer within the broader SYNAPSE framework.

---

## Validation

Validation is intentionally layered.

**Structural validation**

- JSON Schema validation defines the structural contract for topology and artifact schemas.

**Semantic validation**

- Deterministic semantic validation enforces graph integrity, including duplicate identifiers, unknown component references, and canonical diagnostics.

Run the conformance suite:

```bash
python -m unittest discover -s tests -p '*_tests.py'
```

## AST and IR Contract

Issue #10 freezes the compiler architecture boundary between source topology and normalized analysis representation in `AST_IR_CONTRACT.md`.

- AST is source-faithful and diagnostic-oriented.
- IR is canonical, normalized, and analysis-ready.
- Normalized IR equality is based on canonical UTF-8 JSON bytes with sorted object keys, compact separators, canonical set ordering, and no trailing newline.
- `normalized_ir_hash` is SHA-256 over that canonical normalized IR hash payload.

This contract remains planning-only and does not add parser, normalizer, reachability, projection, predicate, artifact emission, CLI, runtime, proof, authority, policy, governance, execution, or mutation surfaces.


## Reachability Contract

Issue #11 freezes canonical `Reach(W)` semantics in `REACHABILITY_CONTRACT.md`. Reachability is a per-workload, directed-edge, path-existence contract over normalized IR. It defines deterministic multi-root handling, unreachable results, cycle termination, self-loop handling, disconnected-component behavior, result shape, semantic-array canonicalization before hashing, ordering, and hash boundaries without adding a traversal engine, complement projection, dependency predicate evaluator, artifact emitter, CLI, runtime, proof, authority, policy, governance, execution, or mutation surface.

## Frontend Planning Contracts

`COMPILER_FRONTEND_CONTRACT.md` closes the pre-implementation frontend planning gaps by defining parser diagnostic taxonomy, AST construction rules, normalization design rules, diagnostic ordering, diagnostic schema boundaries, and diagnostics-only conformance vectors. It remains contract-only and does not add parser, AST builder, normalizer, analyzer, runtime, proof, authority, governance, policy, execution, or mutation behavior.
