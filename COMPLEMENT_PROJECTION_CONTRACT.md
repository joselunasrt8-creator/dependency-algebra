# Complement Projection Contract

## Executive assessment

Complement projection freezes the structural meaning of `¬S` for Dependency Algebra v1. It is a deterministic transformation from normalized IR plus a candidate component set to a projected normalized IR with the candidate components and every incident edge removed. The contract is planning-only: it defines semantics, invariants, diagnostics, equality, and hash boundaries without adding an engine or any runtime surface.

## Intent, scope, and preserved invariants

- Intent: define the canonical structural transformation consumed by later dependency predicate evaluation.
- Exact scope: contract documentation, projection result schema, canonical projection fixtures, and schema/contract tests.
- Affected surfaces: `COMPLEMENT_PROJECTION_CONTRACT.md`, `schemas/projection.schema.json`, `fixtures/projection/`, documentation indexes, and schema tests.
- Preserved invariants: source topology, AST, source normalized IR, workload identifiers, workload definitions, graph direction, identifier spelling, and canonical ordering remain stable.
- Mutation-capable surfaces introduced: none. Fixtures and tests are static contract artifacts only.
- Replay implications: identical normalized IR and equivalent candidate sets must produce byte-identical projected IR and `projected_ir_hash`.
- Proof requirements: schema validation, invariant checks, deterministic ordering checks, canonical hash checks, and forbidden-field checks.
- Unresolved ambiguity: deferred questions are listed explicitly below rather than silently implemented.

## Canonical definition

```text
Normalized IR + candidate component set S
        ↓
Remove every component in S
        ↓
Remove every edge incident to any removed component
        ↓
Rebuild canonical structural tables for the remaining graph
        ↓
Projected normalized IR
```

`¬S` is defined only over normalized IR in v1. Projection does not parse topology JSON, construct AST, normalize IR, evaluate reachability, classify dependency, compute resilience, emit compiler artifacts, invoke governance, or mutate external state.

## Projection semantics

1. Input IR must already satisfy the normalized IR contract.
2. `candidate_set` contains component identifiers only in v1.
3. Candidate identifiers are canonicalized for projection context by lexicographic ordering and duplicate detection.
4. Unknown candidates are rejected with `PROJECTION.UNKNOWN_COMPONENT` and no projected IR is required.
5. Empty candidate sets remain invalid in v1 and produce `PROJECTION.EMPTY_CANDIDATE_SET`.
6. Duplicate candidates are rejected with `PROJECTION.DUPLICATE_CANDIDATE` before removal.
7. For every candidate component, projection removes that component and all incident incoming, outgoing, and self-loop edges.
8. Projection preserves all non-removed components and all edges whose endpoints both remain.
9. Projection preserves workload objects unchanged, including roots, target, `candidate_set`, source lineage, metadata, and expected classification.
10. Projection diagnostics are structural context only and do not affect reachability or classification.

## Component-removal rules

- Isolated component: remove the component; no edges are removed.
- Source/root component: remove normally and emit `PROJECTION.REMOVED_ROOT`; workload roots are not rewritten.
- Target component: remove normally and emit `PROJECTION.REMOVED_TARGET`; workload target is not rewritten.
- Cycle participant: remove normally; every incident cycle edge is removed; remaining cycle fragments are preserved.
- Self-loop component: remove the component and the self-loop edge.
- Bridge component: remove normally; projection does not classify bridge impact.
- Multiple components: canonicalize candidates lexicographically, then remove as one set; candidate order never changes projected IR identity.
- Empty candidate set: invalid in v1; no successful projected IR is defined.

## Edge-removal rules

An edge is removed if and only if `edge.from` or `edge.to` is in the canonical candidate set. Removed edge identifiers are not retained in projected IR. They may appear only in diagnostics if a future diagnostic code explicitly requires edge subjects; v1 does not require a removed-edge list.

## Workload preservation rules

Workloads are analysis context, not projection mutation targets. Projection never removes, renumbers, rewrites, or deduplicates workload roots, targets, candidate sets, expected classifications, metadata, or source lineage. Removed components may therefore still appear inside workload definitions after projection as unchanged references; those references are not graph endpoints and are interpreted by downstream passes in context.

## Projected IR invariants

Projected IR must guarantee:

- remaining component identifiers are unique;
- remaining edge identifiers are unique;
- every remaining edge endpoint resolves to a remaining component;
- workload identifiers and definitions are unchanged;
- topology identity is unchanged;
- graph direction is unchanged;
- component, edge, adjacency, reverse adjacency, and workload ordering is canonical;
- no dangling edges remain;
- no unresolved remaining graph references remain;
- no runtime, authority, governance, proof, policy, execution, mutation, timestamp, machine-path, random-ID, or environment-derived field is present.

## Deterministic ordering

Projection emits arrays in normalized IR order: components by component id, edges by edge id, workloads by workload id, candidate sets by component id when represented as projection context, and adjacency entries by adjacent component id then edge id. Object keys are serialized canonically for hashing.

## Projection equality semantics

Equivalent normalized IR plus equivalent candidate set must produce equivalent projected IR. Candidate sets are equivalent after canonical ordering; input candidate ordering differences must not affect projected IR identity. Diagnostics may differ only when input candidate representation differs in ways that are invalid, such as duplicates.

## `projected_ir_hash`

`projected_ir_hash = SHA-256(canonical UTF-8 JSON(projected_ir without projected_ir_hash))`.

Canonical serialization uses sorted object keys, canonical set ordering, compact separators, UTF-8, no trailing newline, and excludes timestamps, machine paths, random IDs, runtime fields, authority fields, governance fields, proof fields, policy fields, execution fields, mutation fields, and diagnostics. Diagnostics are hash-excluded because they describe projection context, not the projected graph identity.

## Diagnostics taxonomy

Diagnostics are deterministic and structural only:

| Code | Severity | Meaning | Hash boundary |
| --- | --- | --- | --- |
| `PROJECTION.UNKNOWN_COMPONENT` | error | Candidate does not resolve to an IR component. | Excluded |
| `PROJECTION.EMPTY_CANDIDATE_SET` | error | Candidate set is empty, invalid in v1. | Excluded |
| `PROJECTION.DUPLICATE_CANDIDATE` | error | Candidate appears more than once. | Excluded |
| `PROJECTION.REMOVED_ROOT` | warning | Removed component is a workload root. | Excluded |
| `PROJECTION.REMOVED_TARGET` | warning | Removed component is a workload target. | Excluded |
| `PROJECTION.COMPONENT_REMOVED` | info | Component was removed by projection. | Excluded |

Informational diagnostics are allowed when they remain deterministic and structural.

## Explicit questions resolved

1. Projection is defined only over normalized IR in v1.
2. Candidate sets are component-only in v1.
3. Removed components may appear only in preserved workload definitions and diagnostics, never as remaining components or edge endpoints.
4. Removed edge IDs are not retained in projected IR.
5. Projection preserves workload metadata and definitions unchanged.
6. Projection may emit deterministic informational diagnostics.
7. Removed roots are removed normally plus a structural warning.
8. Removed targets are removed normally plus a structural warning.
9. Multiple removals are canonicalized lexicographically and applied as a set.
10. `projected_ir_hash` covers projected IR structural fields excluding `projected_ir_hash` itself and diagnostics.
11. All projection diagnostics are hash-excluded.
12. Projected IR uses normalized IR arrays plus adjacency maps, matching the IR contract.

## Deferred questions

- Edge, group, or predicate-based candidate sets are deferred.
- Empty candidate set semantics beyond invalid-v1 diagnostics are deferred.
- Whether future artifacts include removed-component or removed-edge audit tables is deferred.
- Dependency predicate truth tables and classifications are deferred.
- Any compiler API, CLI, runtime integration, or ContinuityOS integration is deferred.

## Boundary confirmation

Complement projection remains structural analysis only. This contract introduces no parser, AST implementation, IR implementation, projection engine, reachability engine, dependency predicate evaluator, artifact emitter, CLI, GitHub Action consumer, ContinuityOS integration, runtime, authority, proof, policy, governance, execution, or external-state mutation surface.
