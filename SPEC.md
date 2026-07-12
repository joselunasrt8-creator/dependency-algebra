# SYNAPSE Normative Specification Index

**Specification version:** `synapse.spec.v1`
**Status:** normative repository entry point for frozen SYNAPSE structural contracts
**Applies to:** the current Dependency Algebra compiler implementation and all frozen contract artifacts indexed below

`SPEC.md` is the authoritative repository-level index for SYNAPSE contracts. When another document defines detailed semantics, this file summarizes the contract and links to the canonical source instead of duplicating the full body. Future frozen contracts MUST be linked from this file before they are treated as repository-normative.

## 1. Purpose and scope

SYNAPSE is a deterministic structural analysis framework. In this repository, SYNAPSE owns the contracts and implementation boundary for transforming declared topology into canonical structural objects, deterministic structural analysis, structural classifications, compiler receipts, and evidence artifacts.

The current reference implementation is the Dependency Algebra compiler. It answers structural questions about component topology; it does not decide authority, legitimacy, policy approval, runtime execution, or execution eligibility.

Normative boundary documents:

- [Repository boundary](BOUNDARY.md)
- [Scope and ecosystem handoffs v1](docs/scope-and-handoffs-v1.md)
- [Architecture closure report](ARCHITECTURE_CLOSURE_REPORT.md)
- [README navigation and current status](README.md)

## 2. Mathematical model, separate from implementation

The mathematical model is structural graph analysis over normalized topology. The core predicate is:

```text
Dependency(S, W) ⇔ Reach(W | ¬S) = ∅
```

Where:

- `W` is a workload with roots, target, candidate component set, and expected structural classification.
- `S` is a finite set of candidate component identifiers.
- `¬S` is complement projection: the graph induced by removing every component in `S` and every incident edge.
- `Reach(W)` is directed path existence from any workload root to the workload target.

Mathematical semantics are frozen by these documents:

- [AST and IR contract](AST_IR_CONTRACT.md) for canonical source-to-IR meaning.
- [Complement projection contract](COMPLEMENT_PROJECTION_CONTRACT.md) for `¬S`.
- [Reachability semantics contract](REACHABILITY_CONTRACT.md) for `Reach(W)`.
- [Dependency predicate contract](DEPENDENCY_PREDICATE_CONTRACT.md) for `Dependency(S, W)`.
- [Determinism contract](DETERMINISM.md) for replay-safe canonical identity.

Implementation is intentionally separate. Current implementation owners are `dependency_algebra/frontend.py`, `dependency_algebra/ir.py`, `dependency_algebra/projection.py`, `dependency_algebra/reachability.py`, `dependency_algebra/predicate.py`, `dependency_algebra/classification.py`, `dependency_algebra/engine.py`, `dependency_algebra/serialization.py`, `dependency_algebra/compiler.py`, and `dependency_algebra/cli.py`. Those modules implement or adapt the contracts; they do not redefine mathematical semantics.

## 3. Canonical terminology

| Term | Canonical meaning | Boundary note |
| --- | --- | --- |
| topology | Source structural graph document with components, directed edges, and workloads. | Input shape is constrained by [`schemas/topology.schema.json`](schemas/topology.schema.json). |
| structural object | Any SYNAPSE-owned topology, AST, IR, projected IR, reachability, dependency, classification, receipt, diagnostic, or artifact object. | Structural objects are not authority objects. |
| canonical IR | Normalized analysis-ready graph representation with deterministic component, edge, adjacency, reverse-adjacency, workload, and hash fields. | Defined by [`AST_IR_CONTRACT.md`](AST_IR_CONTRACT.md) and [`schemas/ir.schema.json`](schemas/ir.schema.json). |
| normalization | Validation and deterministic transformation from source topology/AST into canonical IR. | Invalid input is rejected before analysis and is not classified as `NULL`. |
| canonicalization | Stable ordering and canonical JSON byte representation used for equality and hashing. | Defined by [`DETERMINISM.md`](DETERMINISM.md) and serialization code. |
| projection | Complement projection `¬S` over normalized IR. | Defined by [`COMPLEMENT_PROJECTION_CONTRACT.md`](COMPLEMENT_PROJECTION_CONTRACT.md). |
| reachability | Directed structural path existence from workload roots to target. | Defined by [`REACHABILITY_CONTRACT.md`](REACHABILITY_CONTRACT.md). |
| structural predicate | The dependency relation over projected reachability. | Defined by [`DEPENDENCY_PREDICATE_CONTRACT.md`](DEPENDENCY_PREDICATE_CONTRACT.md). |
| structural classification | Aggregate `VALID`, `DEGRADED`, or `NULL` classification from dependency results. | Structural only; never permission to execute. |
| evidence artifact | Deterministic compiler artifact containing structural evidence such as hashes, classification, reachability, dependency lattice, and diagnostics. | Shape is constrained by [`schemas/artifact.schema.json`](schemas/artifact.schema.json). |
| compiler receipt | Deterministic hash receipt emitted by the compiler facade. | Receipt identity is structural evidence, not legitimacy. |
| validity | Structural classification or schema/semantic acceptability, depending on context. | Do not use `VALID` as execution authorization. |
| legitimacy | Downstream governance/authorization concept outside SYNAPSE. | Owned by ContinuityOS, not this repository. |
| execution eligibility | Downstream decision that execution may occur. | Not emitted by SYNAPSE. |

Ambiguous or deprecated usage: any use of `valid`, `proof`, `authority`, `legitimacy`, `policy`, `runtime`, or `execution` that implies SYNAPSE approval is deprecated unless it explicitly states that SYNAPSE does not own that concept.

## 4. Compiler pipeline

The current repository pipeline is represented by the implemented stages and architecture closure audit:

```text
Source topology
  → Parse (`parse_topology`)
  → Validate / AST-shape checks (`validate_and_normalize` shape phase)
  → Normalize (`validate_and_normalize` semantic phase)
  → Canonical IR (`dependency-algebra.ir.v1`)
  → Projection (`ProjectedIR` / complement projection)
  → Reachability (`ReachabilityResult`)
  → Structural predicate (`DependencyResult`)
  → Classification (`ClassificationResult`)
  → AnalysisResult
  → Serialization
  → Artifact / receipt
  → CLI / public API consumer
```

Every stage is structural-only. Stage ownership and remaining boundary debt are audited in [Architecture closure report](ARCHITECTURE_CLOSURE_REPORT.md). The frontend contract further separates Parse, AST construction, and Normalization in [Compiler frontend contract](COMPILER_FRONTEND_CONTRACT.md).

## 5. Artifact lifecycle

```text
Source input
  → canonical structural representation
  → deterministic analysis
  → structural result
  → evidence artifact / compiler receipt
  → downstream consumption
```

Structural evidence is not authority:

```text
Structural evidence ≠ authority ≠ legitimacy ≠ execution eligibility
```

Artifact and receipt contracts are indexed by:

- [`schemas/artifact.schema.json`](schemas/artifact.schema.json)
- [`schemas/classification.schema.json`](schemas/classification.schema.json)
- [`schemas/diagnostic.schema.json`](schemas/diagnostic.schema.json)
- [`DETERMINISM.md`](DETERMINISM.md)
- [`BOUNDARY.md`](BOUNDARY.md)

## 6. Algorithm conformance and diagnostics

Algorithm conformance is demonstrated through schemas, fixtures, and tests rather than hidden authority channels.

Canonical conformance materials:

- [`fixtures/`](fixtures/) and [fixture catalog](FIXTURES.md)
- [`conformance/`](conformance/) research-object adapters and discovery helpers
- [`schemas/`](schemas/) machine-readable contract envelopes
- [`tests/`](tests/) schema, architecture, boundary, CLI, and conformance tests

Diagnostic contracts:

- [`COMPILER_FRONTEND_CONTRACT.md`](COMPILER_FRONTEND_CONTRACT.md) parser, AST construction, and normalization diagnostics.
- [`schemas/diagnostic.schema.json`](schemas/diagnostic.schema.json) diagnostic envelope.
- [`fixtures/diagnostics/`](fixtures/diagnostics/) diagnostic conformance vectors.

Diagnostics are deterministic structural rejection or warning records. They must not express governance approval, runtime authorization, legitimacy, or execution eligibility.

## 7. Frozen contract index

| Contract area | Canonical source |
| --- | --- |
| Repository ownership and exclusions | [`BOUNDARY.md`](BOUNDARY.md) |
| Ecosystem ownership and handoffs | [`docs/scope-and-handoffs-v1.md`](docs/scope-and-handoffs-v1.md) |
| Product overview and navigation | [`README.md`](README.md) |
| Compiler architecture closure | [`ARCHITECTURE_CLOSURE_REPORT.md`](ARCHITECTURE_CLOSURE_REPORT.md) |
| Topology source schema | [`schemas/topology.schema.json`](schemas/topology.schema.json) |
| AST/IR contract and normalized IR hash | [`AST_IR_CONTRACT.md`](AST_IR_CONTRACT.md), [`schemas/ast.schema.json`](schemas/ast.schema.json), [`schemas/ir.schema.json`](schemas/ir.schema.json) |
| Frontend parse/validation/normalization diagnostics | [`COMPILER_FRONTEND_CONTRACT.md`](COMPILER_FRONTEND_CONTRACT.md), [`fixtures/diagnostics/`](fixtures/diagnostics/) |
| Complement projection | [`COMPLEMENT_PROJECTION_CONTRACT.md`](COMPLEMENT_PROJECTION_CONTRACT.md), [`schemas/projection.schema.json`](schemas/projection.schema.json), [`fixtures/projection/`](fixtures/projection/) |
| Reachability | [`REACHABILITY_CONTRACT.md`](REACHABILITY_CONTRACT.md), [`schemas/reachability.schema.json`](schemas/reachability.schema.json), [`fixtures/reachability/`](fixtures/reachability/) |
| Dependency predicate | [`DEPENDENCY_PREDICATE_CONTRACT.md`](DEPENDENCY_PREDICATE_CONTRACT.md), [`schemas/dependency.schema.json`](schemas/dependency.schema.json), [`fixtures/dependency/`](fixtures/dependency/) |
| Classification | [`schemas/classification.schema.json`](schemas/classification.schema.json), [`fixtures/valid/`](fixtures/valid/), [`fixtures/degraded/`](fixtures/degraded/), [`fixtures/null/`](fixtures/null/) |
| Artifact and receipt evidence | [`schemas/artifact.schema.json`](schemas/artifact.schema.json), [`DETERMINISM.md`](DETERMINISM.md) |
| Canonicalization / serialization / hash boundaries | [`DETERMINISM.md`](DETERMINISM.md), [`ARCHITECTURE_CLOSURE_REPORT.md`](ARCHITECTURE_CLOSURE_REPORT.md) |
| Fixture catalog | [`FIXTURES.md`](FIXTURES.md) |
| Conformance objects | [`conformance/`](conformance/) |

## 8. Ecosystem dependency graph

```text
MindShift
  → context and intent candidates
Structural Analysis Foundations
  → mathematical definitions and proof obligations
SYNAPSE
  → canonical structural objects and deterministic structural evidence
ContinuityOS
  → legitimacy and governed execution

Independent analysis consumers
  ← deterministic structural evidence from SYNAPSE
```

SYNAPSE receives formal definitions and topology inputs, emits deterministic structural evidence, and stops before legitimacy or execution decisions. Detailed handoffs are versioned in [Scope and ecosystem handoffs v1](docs/scope-and-handoffs-v1.md).

## 9. Responsibility matrix

| System | Owns | Does not own |
| --- | --- | --- |
| MindShift | context, cognition governance, intent candidates | structural truth, legitimacy, execution |
| Structural Analysis Foundations | formal definitions, proof obligations | implementation authority, runtime execution |
| SYNAPSE | canonical structural analysis and deterministic evidence | authority, policy approval, execution eligibility |
| ContinuityOS | legitimacy, authorization, execution eligibility | structural-analysis implementation ownership |

## 10. Determinism guarantees

SYNAPSE compiler artifacts must be reproducible from the validated input topology and frozen compiler contracts. Determinism includes canonical object ordering, canonical UTF-8 JSON bytes, SHA-256 hash boundaries, exclusion of timestamps/random IDs/machine-local paths/environment-derived values, deterministic diagnostic ordering, and byte-identical replay for the same accepted input. The normative determinism contract is [`DETERMINISM.md`](DETERMINISM.md).

## 11. End-to-end example using an existing fixture

`fixtures/valid/minimal-valid.json` is a source topology fixture with one workload and a candidate removal that does not collapse reachability.

```text
fixtures/valid/minimal-valid.json
  → parse JSON source
  → validate schema and semantic references
  → normalize into dependency-algebra.ir.v1 canonical IR
  → project the workload candidate set from the canonical IR
  → evaluate reachability over the projected IR
  → evaluate Dependency(S, W)
  → classify the structural result as VALID when no workload evaluates as dependency
  → emit deterministic hash receipt or structural evidence artifact
  → downstream consumer reads structural evidence
```

SYNAPSE responsibility ends at the deterministic structural evidence artifact or compiler receipt. A downstream ContinuityOS or independent consumer may use the evidence, but SYNAPSE does not convert `VALID` into legitimacy, policy approval, or execution eligibility.

## 12. Versioning and amendment rules

Current normative specification version: `synapse.spec.v1`.

A normative change is any change that modifies accepted topology, structural semantics, compiler stage responsibilities, artifact shapes, diagnostic meaning, hash boundaries, ecosystem ownership, handoff boundaries, or the interpretation of structural classifications.

A versioned amendment is required for:

- persistent boundary changes;
- new or removed SYNAPSE-owned concepts;
- changed non-owned concepts;
- changed mathematical semantics for projection, reachability, predicates, or classification;
- changed canonicalization, serialization, or hash boundaries;
- changed diagnostic codes or diagnostic ordering semantics;
- changed artifact, receipt, schema, or fixture contract meaning;
- new frozen contracts that become normative.

Editorial changes do not require a version bump when they only fix spelling, improve navigation, clarify existing meaning, or add non-normative examples without changing accepted behavior or contract interpretation.

Deprecated terms or contracts MUST be recorded in this file or in a versioned amendment linked from this file, with the replacement term/contract and the effective version. Future contract additions MUST be indexed in section 7 before being described as frozen or normative.
