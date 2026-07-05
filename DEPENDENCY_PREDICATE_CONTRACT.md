# Dependency Predicate Contract

## Executive assessment

This contract freezes the canonical structural dependency predicate consumed after complement projection and projected reachability. It defines the mathematical and serialized meaning of `Dependency(S, W)` before any predicate evaluator, compiler pass, runtime surface, artifact emitter, authority module, proof module, governance integration, or ContinuityOS integration exists.

The predicate is a structural yes/no relation only. It consumes already-normalized and already-projected structural results; it does not compute projection, traverse reachability, classify workloads, emit compiler artifacts, or decide whether execution is allowed.

## Boundary confirmation

In scope:

- dependency predicate semantics;
- required predicate inputs;
- deterministic predicate outputs;
- truth-table behavior;
- predicate invariants;
- dependency result schema;
- equality semantics;
- `dependency_result_hash` boundary;
- deterministic structural diagnostics;
- deferred questions with v1 decisions and rationale.

Out of scope:

- parser implementation;
- AST implementation;
- IR implementation;
- reachability engine;
- complement projection engine;
- dependency evaluator;
- compiler artifact emitter;
- CLI, library API, GitHub Action, or external consumer;
- ContinuityOS integration;
- runtime, authority, proof, policy, governance, execution, mutation, or external-state surfaces.

## Canonical pipeline position

```text
Topology JSON
→ Parser
→ AST
→ IR
→ Reachability
→ Complement Projection
→ Dependency Predicate
→ Compiler Artifact
```

The dependency predicate is evaluated only after a projected IR and a reachability result over that projected IR exist.

## Dependency predicate definition

For a workload `W` and candidate component set `S`:

```text
Dependency(S, W) ⇔ Reach(W | ¬S) = ∅
```

Meaning: `S` is a structural dependency of `W` if removing `S` from normalized IR eliminates every structurally valid directed path from the workload roots to the workload target.

Rationale: this keeps dependency semantics tied to graph structure and avoids silently mixing dependency with downstream classification, resilience, authority, execution, or legitimacy concepts.

## Predicate inputs

The v1 predicate has exactly these inputs and no hidden inputs:

1. normalized IR;
2. `normalized_ir_hash`;
3. workload identifier;
4. workload roots;
5. workload target;
6. candidate component set;
7. projected IR;
8. `projected_ir_hash`;
9. reachability result over the projected IR.

No timestamp, machine-local path, random value, runtime state, authority token, governance context, proof material, execution eligibility, external state, or ContinuityOS legitimacy input is part of the predicate.

## Predicate outputs

A dependency result contains:

- `schema_version`;
- `workload_id`;
- `normalized_ir_hash`;
- `roots`;
- `target`;
- `candidate_set`;
- `projected_ir_hash`;
- `reachability_result_hash`;
- `dependency` (`true` or `false`);
- `dependency_reason`;
- `reachable_after_projection`;
- `dependency_result_hash`;
- deterministic structural `diagnostics`.

`dependency_reason` is intentionally limited to whether no structural path remains or at least one structural path remains. Future `VALID`, `DEGRADED`, and `NULL` classifications are downstream consumers and are not evaluated here.

## Truth table

| Case | Projected reachability | `dependency` | Required reason | Required diagnostics |
| --- | --- | --- | --- | --- |
| 1 | `Reach(W | ¬S) = ∅` | `true` | `no_structurally_valid_path_after_projection` | `DEPENDENCY.TRUE`, `DEPENDENCY.EMPTY_REACHABILITY` |
| 2 | `Reach(W | ¬S) ≠ ∅` | `false` | `structurally_valid_path_remaining_after_projection` | `DEPENDENCY.FALSE`, `DEPENDENCY.REACHABILITY_REMAINING` |

Validation failure is not a third truth-table value. Invalid inputs are rejected with `DEPENDENCY.INVALID_INPUT` diagnostics by validators or future callers before a valid predicate result is accepted.

## Predicate invariants

The predicate must guarantee:

- deterministic inputs;
- deterministic outputs;
- deterministic diagnostics;
- workload identity preserved;
- workload roots preserved after normalization;
- workload target preserved;
- candidate set preserved after set normalization;
- projected IR identity preserved;
- projected reachability identity preserved;
- no mutation of normalized IR;
- no mutation of projected IR;
- no graph rewriting;
- no classification;
- no resilience analysis;
- no redundancy analysis;
- no artifact generation;
- no runtime state.

## Dependency result schema

The canonical result schema is `schemas/dependency.schema.json`. It is a schema-only contract for v1 dependency result objects. It rejects unknown fields through `additionalProperties: false` and therefore excludes runtime, authority, governance, policy, proof, execution, mutation, timestamps, local paths, and random identifiers.

The required canonical fixtures live under `fixtures/dependency/` and are contract vectors only. They are not outputs from an implemented evaluator.

## Predicate equality semantics

Two dependency predicate evaluations are equivalent when the following normalized structural inputs are equivalent:

```text
normalized IR
+ candidate set
+ projected IR
+ reachability result over projected IR
```

Equivalent inputs must produce equivalent dependency results. Input ordering differences must never change dependency identity. Sets are compared after canonical set ordering and duplicate rejection/normalization at the relevant prior contract boundary.

Rationale: dependency identity must be replay-safe and structural, not dependent on source JSON object order, array order for set-like fields, host process order, or traversal scheduling.

## `dependency_result_hash` definition

`dependency_result_hash` is:

```text
sha256(canonical_utf8_json(dependency_result_without_dependency_result_hash))
```

Canonical serialization rules:

- lexicographically sorted object keys;
- canonical ordering of set-like arrays;
- compact JSON separators;
- UTF-8 encoding;
- no trailing newline inside the hash bytes;
- no timestamps;
- no machine-local paths;
- no random identifiers;
- no runtime fields;
- no authority fields;
- no governance fields;
- no proof fields;
- no execution fields.

Diagnostics are inside the hash boundary for v1 because they are deterministic structural outputs. Rationale: if diagnostics are part of the accepted result object, replay equality must detect diagnostic drift.

## Diagnostics taxonomy

Dependency diagnostics are deterministic and structural only:

- `DEPENDENCY.TRUE`: the candidate set is a structural dependency for the workload.
- `DEPENDENCY.FALSE`: the candidate set is not a structural dependency for the workload.
- `DEPENDENCY.EMPTY_REACHABILITY`: projected reachability is empty for the workload.
- `DEPENDENCY.REACHABILITY_REMAINING`: one or more reachable structural components remain after projection.
- `DEPENDENCY.INVALID_INPUT`: a required structural input is absent, malformed, inconsistent, or not associated with the projected IR identity.

Diagnostics may distinguish structural dependency from validation failure. They must not express execution eligibility, authorization, legitimacy, proof status, policy state, governance approval, or runtime effects.

## Deferred questions and v1 decisions

1. **Is dependency always evaluated per workload?** Yes in v1. Rationale: roots, target, candidate set, and projected reachability are workload-scoped.
2. **Can dependency be evaluated for multiple candidate sets simultaneously?** Not as one predicate result in v1. Rationale: result identity and hash boundaries are candidate-set-specific; batch evaluation can be a future wrapper.
3. **Can candidate sets contain duplicate components after normalization?** No. Rationale: candidate sets are mathematical sets; duplicate preservation would make ordering affect identity.
4. **Does dependency require projected IR identity?** Yes. Rationale: `Reach(W | ¬S)` is meaningful only against a specific projected graph.
5. **Does dependency require projected reachability identity?** Yes. Rationale: the predicate consumes the projected reachability result and must bind to its hash.
6. **Can diagnostics distinguish structural dependency from validation failure?** Yes. Rationale: `DEPENDENCY.TRUE` and `DEPENDENCY.FALSE` are valid predicate outcomes, while `DEPENDENCY.INVALID_INPUT` is a structural validation failure.
7. **Is `dependency_result_hash` independent of diagnostics?** No in v1. Rationale: diagnostics are deterministic outputs and therefore part of replay identity.
8. **Should dependency results contain explanatory metadata?** Only the bounded structural `dependency_reason` and diagnostics. Rationale: free-form metadata would risk hidden policy, runtime, or authority channels.
9. **Are dependency results immutable once produced?** Yes. Rationale: mutation would break replay-safe hash identity.
10. **Does the predicate ever return `UNKNOWN` in v1?** No. Rationale: valid inputs produce exactly `true` or `false`; invalid inputs are rejected instead of producing a third semantic state.

## Remaining gaps before Compiler Artifact

Before compiler artifact semantics can be frozen, the project still needs downstream contracts for:

- how dependency results are aggregated across workloads;
- how dependency results feed `VALID`, `DEGRADED`, and `NULL` classification;
- compiler artifact hash boundaries that include dependency results;
- artifact diagnostics that preserve dependency diagnostics without widening authority or runtime scope;
- fixture lineage from topology, IR, reachability, projection, dependency, and final artifact objects.
