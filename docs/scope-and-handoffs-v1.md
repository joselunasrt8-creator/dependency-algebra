# SYNAPSE Scope and Ecosystem Handoffs v1

**Version:** `synapse.scope-handoffs.v1`
**Status:** normative scope and boundary specification
**Indexed by:** [`../SPEC.md`](../SPEC.md)

This document defines what SYNAPSE owns, what it does not own, and how information enters and leaves the system. It is structural-only and does not introduce runtime behavior, authority semantics, policy approval, governance logic, or execution capability.

## 1. SYNAPSE-owned concepts

SYNAPSE owns these repository-level concepts:

- **Topology contracts:** source graph and workload input shape, including components, directed edges, roots, targets, candidate sets, schema versions, and structural classifications.
- **Canonical structural objects:** AST contract objects, canonical IR, projected IR, reachability results, dependency results, classification results, diagnostics, analysis results, evidence artifacts, and compiler receipts.
- **Normalization:** deterministic validation and transformation from source topology/AST into canonical IR.
- **Canonicalization:** deterministic ordering, canonical JSON representation, and replay-safe hash boundaries.
- **Projection:** complement projection over normalized IR and component-only candidate sets.
- **Reachability:** deterministic directed structural path-existence evaluation.
- **Structural predicates:** dependency predicate evaluation over projected reachability.
- **Structural classifications:** aggregate `VALID`, `DEGRADED`, and `NULL` structural-only classifications.
- **Deterministic analysis artifacts:** schema-constrained structural evidence outputs.
- **Compiler receipts:** hash receipts binding input, normalized IR, dependency result, classification, compiler version, and package version.

## 2. Explicit non-owned concepts

SYNAPSE does not own or emit:

- authority;
- execution eligibility;
- policy approval;
- runtime execution;
- legitimacy proof;
- registry reconciliation;
- ContinuityOS governance decisions;
- runtime authorization;
- external-state mutation.

`VALID`, `DEGRADED`, and `NULL` are structural classifications only. Structural validity is not execution legitimacy. No SYNAPSE output grants permission to execute.

## 3. Ecosystem dependency graph

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

## 4. Compiler pipeline boundary

The current SYNAPSE compiler stages are:

```text
Source topology
  → Parse
  → Validate
  → Normalize
  → Canonical IR
  → Projection
  → Reachability
  → Structural predicate
  → Classification
  → AnalysisResult
  → Serialization
  → Artifact / receipt
```

Stage names map to the current implementation and architecture audit: parse and validation/normalization live in the frontend, analysis orchestration produces reachability, dependency, and classification artifacts, serialization owns representation and hash identity, and the compiler facade emits receipt or artifact objects.

## 5. Artifact lifecycle boundary

```text
Source input
  → canonical structural representation
  → deterministic analysis
  → structural result
  → evidence artifact
  → downstream consumption
```

```text
Structural evidence
  ≠ authority
  ≠ legitimacy
  ≠ execution eligibility
```

SYNAPSE's emitted evidence can be consumed by other systems, but downstream systems own any decision that depends on policy, legitimacy, authorization, registry reconciliation, or execution context.

## 6. Required handoffs

### 6.1 Structural Analysis Foundations → SYNAPSE

| Field | Boundary |
| --- | --- |
| Producer | Structural Analysis Foundations |
| Consumer | SYNAPSE |
| Accepted input | Formal definitions, proof obligations, terminology constraints, and mathematical contract amendments for structural analysis. |
| Emitted output | SYNAPSE contract updates, schemas, fixtures, tests, and implementation changes when explicitly scoped. |
| Authority boundary | Foundations define formal obligations; SYNAPSE owns repository implementation conformance. Neither side grants runtime authority. |
| Failure or rejection behavior | Ambiguous, unversioned, or non-structural obligations are rejected or recorded as deferred until a versioned amendment exists. |
| Versioning responsibility | Persistent semantic or boundary changes require a new SYNAPSE-indexed versioned amendment. |

### 6.2 Domain frontend → SYNAPSE

| Field | Boundary |
| --- | --- |
| Producer | Domain frontend or caller that prepares topology JSON. |
| Consumer | SYNAPSE parser/compiler facade. |
| Accepted input | Source topology JSON conforming to the topology schema and semantic validation rules. |
| Emitted output | Canonical IR, deterministic diagnostics on rejection, structural evidence artifact, or compiler receipt depending on API path. |
| Authority boundary | The frontend supplies structural declarations only. SYNAPSE validates and analyzes structure; it does not accept authority, legitimacy, policy, runtime, or execution claims from the input. |
| Failure or rejection behavior | Malformed JSON, unsupported schema versions, duplicate identifiers, unresolved references, empty candidate sets, and invalid shapes are rejected with deterministic diagnostics. |
| Versioning responsibility | Input shape or semantic validation changes require indexed schema/contract amendments and fixture updates. |

### 6.3 SYNAPSE → ContinuityOS

| Field | Boundary |
| --- | --- |
| Producer | SYNAPSE compiler facade, artifact emitter, or public API. |
| Consumer | ContinuityOS or a ContinuityOS adapter. |
| Accepted input | Valid source topology supplied to SYNAPSE; ContinuityOS receives only emitted structural evidence, artifacts, diagnostics, and receipts. |
| Emitted output | Deterministic structural evidence: classifications, reachability evidence, dependency evidence, hashes, diagnostics, artifacts, and receipts. |
| Authority boundary | SYNAPSE evidence may inform ContinuityOS. ContinuityOS owns legitimacy, authorization, execution eligibility, governed execution, and registry reconciliation. |
| Failure or rejection behavior | SYNAPSE rejects invalid topology before evidence emission. ContinuityOS must reject or quarantine evidence it cannot validate against indexed SYNAPSE versions. |
| Versioning responsibility | SYNAPSE versions structural evidence contracts; ContinuityOS versions legitimacy and execution policies. Boundary changes require explicit versioned amendments. |

### 6.4 SYNAPSE → independent analysis consumers

| Field | Boundary |
| --- | --- |
| Producer | SYNAPSE compiler facade, artifact emitter, CLI, or public API. |
| Consumer | Independent analysis tools, auditors, visualizers, optimizers, or research-object consumers. |
| Accepted input | Valid topology accepted by SYNAPSE and/or canonical SYNAPSE artifacts matching indexed schemas. |
| Emitted output | Deterministic structural evidence artifacts, compiler receipts, diagnostics, fixture vectors, and conformance objects. |
| Authority boundary | Consumers may interpret evidence for their own purposes, but SYNAPSE does not delegate authority or certify execution. |
| Failure or rejection behavior | Consumers should reject unknown schema versions, hash mismatches, unsupported contract versions, or missing indexed contracts. SYNAPSE rejects invalid source input deterministically. |
| Versioning responsibility | SYNAPSE versions emitted structural contracts; consumers version their own interpretation layers. Persistent interop changes require explicit versioned contract references. |

## 7. Responsibility matrix

| System | Owns | Does Not Own |
| --- | --- | --- |
| MindShift | context, cognition governance, intent candidates | structural truth, legitimacy, execution |
| Structural Analysis Foundations | formal definitions, proof obligations | implementation authority, runtime execution |
| SYNAPSE | canonical structural analysis and deterministic evidence | authority, policy approval, execution eligibility |
| ContinuityOS | legitimacy, authorization, execution eligibility | structural-analysis implementation ownership |

## 8. Versioning and amendments

Current version: `synapse.scope-handoffs.v1`.

A normative handoff change includes any persistent change to producer/consumer roles, accepted inputs, emitted outputs, authority boundary, failure behavior, versioning ownership, owned concepts, or non-owned concepts.

Versioned amendment required:

- adding or removing a handoff;
- changing a handoff producer or consumer;
- allowing authority, policy, legitimacy, registry reconciliation, or execution fields into SYNAPSE artifacts;
- changing where SYNAPSE responsibility ends;
- changing the meaning of structural validity or classification;
- adopting a new formal foundation obligation as repository-normative.

Editorial changes may clarify wording, fix links, or add examples without changing the above boundaries. Deprecated terms must be recorded in [`../SPEC.md`](../SPEC.md) or a successor versioned scope document before replacement language becomes normative.
