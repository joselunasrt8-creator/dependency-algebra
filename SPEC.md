# Dependency Algebra Specification

## Product identity

Dependency Algebra is a deterministic structural compiler specification. It describes how topology JSON will be parsed, normalized, analyzed, and serialized into dependency-analysis artifacts.

It is not an application runtime, policy engine, governance validator, runtime proof system, or execution authorizer.

## Core predicate

The canonical dependency predicate is:

```text
Dependency(S, W) ⇔ Reach(W | ¬S) = ∅
```

A candidate component set `S` is a structural dependency of workload `W` when removing `S` eliminates every structurally valid reachable path to `W`.

## Terms

### W — workload

`W` is a named workload requirement declared in topology JSON. In v1, each workload has:

- a deterministic workload identifier
- one or more root component identifiers
- one target component identifier
- one candidate component set `S`
- an expected structural classification

### S — candidate component set

`S` is a finite set of component identifiers declared by a workload. In v1, `S` contains components only. Edge candidates, group candidates, and empty candidate sets are deferred.

### ¬S — complement projection

`¬S` is the topology induced by removing every component in `S` and every incident relationship from the normalized IR. Unknown component identifiers are validation errors and must not silently enter analysis.

### Reach

`Reach(W)` is a deterministic existence check from workload roots to the workload target over directed edges in normalized IR. The canonical v1 semantics are frozen in `REACHABILITY_CONTRACT.md`: reachability is path existence only, full paths are not enumerated, multiple roots are evaluated per workload with existential success, unreachable targets emit `reachable: false`, cycles terminate by visited-component tracking, self-loops are traversable, disconnected components are preserved but ignored unless reached, and result hashes cover the semantically normalized canonical result payload excluding only `reachability_result_hash`.

### Structurally valid path

A structurally valid path is a directed path that satisfies the topology schema and normalized IR rules. It is not an authorized execution path and does not imply governance legitimacy.

## Structural classifications

`VALID`, `DEGRADED`, and `NULL` are structural-only classifications:

- `VALID`: required workload reachability remains structurally intact and no declared candidate dependency collapse is observed.
- `DEGRADED`: at least one valid structural path remains, but redundancy or declared reachability is reduced.
- `NULL`: no valid structural path remains for the workload after applying declared structural conditions.

Invalid input is rejected with diagnostics; it is not classified as `NULL`.

## Validation layers

JSON Schema validation and custom semantic validation are separate contract layers. JSON Schema defines document shape, field types, allowed structural classifications, schema versions, hash formats, and closed artifact fields. Semantic validation handles graph-integrity rules that require cross-reference knowledge, including duplicate identifiers, unknown edge endpoints, unknown workload roots, unknown workload targets, and unknown candidate components. A topology can satisfy JSON Schema shape and still fail semantic validation.

## Deferred compiler outputs

The compiler artifact schema reserves deterministic fields for:

- dependency lattice
- reachability graph
- failure surface
- redundancy map
- k-of-n resilience profile
- annihilation conditions

For v1 schema stabilization, these fields are schema-defined but may be empty arrays or objects until the compiler core is implemented.

## Non-goals

The compiler never authorizes execution, emits runtime proof, mutates external state, requires authority tokens, or determines ContinuityOS governance legitimacy.
