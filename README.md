# SYNAPSE

<p align="center">
  <img
    src="FEE00044-FF76-4C31-8D1C-E534773819C2.png"
    alt="SYNAPSE — Structural Analysis Engine & Framework"
    width="100%">
</p>

## Deterministic Structural Analysis Framework

SYNAPSE transforms declared software topology into deterministic structural analyses and reproducible structural evidence.

```text
Topology
    ↓
Canonical Structural Representation
    ↓
Deterministic Structural Analysis
    ↓
Structural Evidence
```

Dependency Algebra is the current reference implementation and the first implemented structural analysis. It demonstrates the framework without defining its complete identity.

The current implementation includes a structural compiler, analysis engine, canonical serialization utilities, public APIs, deterministic evidence artifacts, and a command-line interface.

---

## Core Runtime

```text
Source Topology
        ↓
Validation
        ↓
Canonical Structural Representation
        ↓
Registered Structural Analysis
        ↓
Deterministic Structural Result
        ↓
Structural Evidence Artifact
```

---

## What Problem Does Structural Analysis Solve?

Structural analysis answers repeatable questions about software structure.

SYNAPSE performs these analyses using canonical structural representations and deterministic analysis passes. Dependency Algebra is the first implemented structural analysis and asks whether removing a workload's candidate component set eliminates all directed paths from workload roots to the workload target.

The core implemented predicate is:

```text
Dependency(S, W) ⇔ Reach(W | ¬S) = ∅
```

Where:

- `W` is a workload with roots, target, candidate component set, and expected structural classification.
- `S` is the workload candidate component set.
- `¬S` is complement projection: remove each component in `S` and every incident edge.
- `Reach(W)` is directed path existence from any workload root to the workload target.

The result is structural evidence: deterministic facts about topology and analysis semantics.

---

## Inputs

SYNAPSE currently accepts UTF-8 JSON topology documents constrained by [`schemas/topology.schema.json`](schemas/topology.schema.json). A topology document contains:

- `schema_version`: currently `dependency-algebra.topology.v1`
- `topology_id`: stable topology identifier
- `components`: component identifiers plus optional `type` and string `labels`
- `edges`: directed edges with stable identifiers, `from`, `to`, and optional string `labels`
- `workloads`: workload identifiers, root components, target component, candidate component set, and expected structural classification

Fixtures under [`fixtures/`](fixtures/) provide accepted, rejected, diagnostic, determinism, projection, reachability, dependency, and artifact examples.

---

## Validation and Normalization

Validation is layered and fail-closed:

1. Parse UTF-8 JSON source.
2. Validate source shape and schema version.
3. Construct source-faithful topology objects for diagnostics.
4. Perform deterministic semantic validation, including duplicate identifiers and unresolved references.
5. Normalize accepted input into canonical IR.

Invalid input is rejected before analysis. Rejected input is not assigned a `VALID`, `DEGRADED`, or `NULL` structural classification.

Canonical IR is defined by [`AST_IR_CONTRACT.md`](AST_IR_CONTRACT.md) and [`schemas/ir.schema.json`](schemas/ir.schema.json). Its identity is `normalized_ir_hash`, a SHA-256 digest over canonical UTF-8 JSON bytes with sorted object keys, compact separators, canonical set ordering, and no trailing newline.

Diagnostic behavior is defined by [`COMPILER_FRONTEND_CONTRACT.md`](COMPILER_FRONTEND_CONTRACT.md), [`schemas/diagnostic.schema.json`](schemas/diagnostic.schema.json), and [`fixtures/diagnostics/`](fixtures/diagnostics/).

---

## Registered Structural Analyses

The currently implemented structural analysis is Dependency Algebra. It includes these deterministic passes:

- complement projection over canonical IR
- directed reachability from workload roots to workload target
- dependency predicate evaluation over projected reachability
- aggregate structural classification as `VALID`, `DEGRADED`, or `NULL`

The implemented analysis is registered through the deterministic core analysis registry. Future analyses can fit SYNAPSE by registering additional deterministic analysis passes over canonical structural representation and emitting structural results with explicit contracts, schemas, fixtures, and tests.

Unimplemented analyses are not currently available.

---

## Structural Evidence

SYNAPSE emits deterministic structural results and structural evidence artifacts.

The CLI emits a structural evidence artifact constrained by [`schemas/artifact.schema.json`](schemas/artifact.schema.json). The current artifact includes:

- artifact and source schema versions
- compiler and package versions
- `input_hash`
- `normalized_ir_hash`
- aggregate `classification`
- `reachability_graph`
- `dependency_lattice`
- `failure_surface`
- `redundancy_map`
- `k_of_n_resilience_profile`
- `annihilation_conditions`
- diagnostics, warnings, and errors arrays
- provenance with the implemented pipeline and analysis result hash
- `artifact_hash`

The compiler facade also exposes a deterministic hash receipt for callers that need receipt-shaped structural evidence rather than the full artifact.

Structural results are analysis outputs such as reachability, dependency, and classification. Structural evidence artifacts are serialized, hash-addressed payloads that carry those results across the public boundary.

---

## Compiler Pipeline

The current implementation maps the core runtime to these concrete stages:

```text
Source topology
  → parse_topology
  → validate_and_normalize
  → canonical IR
  → registered Dependency Algebra analysis
  → projection, reachability, dependency predicate, classification
  → AnalysisResult
  → serialization
  → artifact or hash receipt
  → CLI / public API consumer
```

Compiler stages exchange immutable typed artifacts. Serialization owns dictionary conversion and canonical JSON. Hashing owns artifact identity across serialized payload boundaries. Compatibility APIs cross the serialization boundary explicitly so public functions and CLI output remain dictionary- and JSON-shaped while the core compiler remains artifact-oriented.

---

## SYNAPSE CLI

The stable command shape is:

```bash
python -m dependency_algebra.cli compile --input fixtures/basic.json --output out/artifact.json
```

The package also installs a `synapse` console script when installed from [`pyproject.toml`](pyproject.toml):

```bash
synapse compile --input fixtures/basic.json --output out/artifact.json
```

The CLI compiles canonical topology JSON into a deterministic structural evidence artifact. On success, it writes the artifact to `--output` and writes no success output to stdout or stderr. Diagnostics are canonical machine-readable JSON on stderr.

Stable exit codes:

| Code | Meaning |
| ---: | --- |
| 0 | Success |
| 1 | Input, schema, or validation failure |
| 2 | Compiler semantic failure |
| 3 | Artifact emission failure |
| 4 | Unexpected runtime failure |

The CLI never mutates input files.

---

## Determinism Validation

Determinism is defined by [`DETERMINISM.md`](DETERMINISM.md). SYNAPSE determinism requires:

- canonical object ordering
- canonical UTF-8 JSON bytes
- SHA-256 hash boundaries
- no wall-clock timestamps in compiler artifacts
- no random identifiers in compiler artifacts
- no machine-local absolute paths in compiler artifacts
- no environment-derived values in compiler artifacts
- deterministic diagnostic ordering
- byte-identical replay for the same accepted input

Run the conformance and regression suite:

```bash
python -m pytest tests
```

The CLI determinism tests compile the same fixture repeatedly and compare byte-identical artifact output.

---

## Normative Contracts

[`SPEC.md`](SPEC.md) is the authoritative repository-level index for SYNAPSE contracts. The current normative contract set includes:

| Contract area | Canonical source |
| --- | --- |
| Repository ownership and exclusions | [`BOUNDARY.md`](BOUNDARY.md) |
| Topology source schema | [`schemas/topology.schema.json`](schemas/topology.schema.json) |
| AST and canonical IR | [`AST_IR_CONTRACT.md`](AST_IR_CONTRACT.md), [`schemas/ast.schema.json`](schemas/ast.schema.json), [`schemas/ir.schema.json`](schemas/ir.schema.json) |
| Frontend parse, validation, normalization, diagnostics | [`COMPILER_FRONTEND_CONTRACT.md`](COMPILER_FRONTEND_CONTRACT.md), [`schemas/diagnostic.schema.json`](schemas/diagnostic.schema.json), [`fixtures/diagnostics/`](fixtures/diagnostics/) |
| Complement projection | [`COMPLEMENT_PROJECTION_CONTRACT.md`](COMPLEMENT_PROJECTION_CONTRACT.md), [`schemas/projection.schema.json`](schemas/projection.schema.json), [`fixtures/projection/`](fixtures/projection/) |
| Reachability | [`REACHABILITY_CONTRACT.md`](REACHABILITY_CONTRACT.md), [`schemas/reachability.schema.json`](schemas/reachability.schema.json), [`fixtures/reachability/`](fixtures/reachability/) |
| Dependency predicate | [`DEPENDENCY_PREDICATE_CONTRACT.md`](DEPENDENCY_PREDICATE_CONTRACT.md), [`schemas/dependency.schema.json`](schemas/dependency.schema.json), [`fixtures/dependency/`](fixtures/dependency/) |
| Classification | [`schemas/classification.schema.json`](schemas/classification.schema.json), [`fixtures/valid/`](fixtures/valid/), [`fixtures/degraded/`](fixtures/degraded/), [`fixtures/null/`](fixtures/null/) |
| Artifact and receipt evidence | [`schemas/artifact.schema.json`](schemas/artifact.schema.json), [`schemas/structural-evidence.schema.json`](schemas/structural-evidence.schema.json), [`DETERMINISM.md`](DETERMINISM.md) |
| Fixture catalog | [`FIXTURES.md`](FIXTURES.md) |
| Architecture closure | [`ARCHITECTURE_CLOSURE_REPORT.md`](ARCHITECTURE_CLOSURE_REPORT.md) |

---

## Repository Boundary

SYNAPSE is limited to deterministic structural analysis.

It:

- accepts declared topology
- validates and normalizes structural input
- constructs canonical structural representations
- executes registered structural analyses
- produces deterministic structural results
- serializes structural evidence artifacts

SYNAPSE deliberately ends at structural evidence.

`VALID`, `DEGRADED`, and `NULL` are structural classifications only. They summarize deterministic analysis results and do not cause external actions or state changes.

---

## Future Structural Analyses

Future structural analyses may be added as additional deterministic analysis passes over the canonical structural representation. A future analysis should define:

- the structural question it answers
- the canonical input object it consumes
- deterministic semantics and ordering rules
- result and evidence artifact fields
- schema and fixture coverage
- conformance tests
- hash boundaries, if the result crosses a serialized evidence boundary

Every registered structural analysis operates over the canonical structural representation and preserves SYNAPSE's deterministic analysis model.
