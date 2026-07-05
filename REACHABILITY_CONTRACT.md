# Reachability Semantics Contract

## Executive assessment

This contract freezes the canonical meaning of `Reach(W)` for normalized Dependency Algebra IR before any traversal engine, complement projection, dependency predicate evaluation, artifact emitter, CLI, runtime integration, authority surface, proof surface, policy surface, governance surface, execution surface, or mutation surface is implemented.

Reachability is a structural graph question only. It answers whether a workload target is reachable from one or more workload roots by following directed edges in normalized IR. It does not enumerate authorized execution paths, prove legitimacy, mutate topology, evaluate dependencies, classify governance status, or emit runtime artifacts.

## Boundary confirmation

In scope:

- traversal roots and workload targets
- directed-edge traversal over normalized IR adjacency
- path-existence semantics
- cycle termination
- disconnected graph behavior
- multi-root behavior
- self-loop behavior
- deterministic visited-node and diagnostic ordering
- reachability result schema and fixtures

Out of scope:

- reachability engine implementation
- complement projection
- dependency predicate evaluation
- compiler artifact emission
- CLI behavior
- runtime behavior
- authority, proof, policy, governance, execution, or mutation behavior

## Reachability definition

For a normalized IR workload `W`, `Reach(W)` is a deterministic structural path-existence result over the normalized directed graph.

```text
Reach(W) = reachable iff ∃ root r ∈ W.roots such that a directed path exists from r to W.target.
```

A directed path may have length zero. Therefore, if any workload root equals the workload target, the target is reachable even when no edge is traversed.

Required decisions:

1. Reachability means path existence only.
2. Full paths are not enumerated in v1.
3. Multiple roots are evaluated as an ordered union with existential success: the workload is reachable if any root reaches the target.
4. When the target is unreachable, the result emits `reachable: false`, `reached_by: []`, deterministic `visited_nodes`, and deterministic diagnostics explaining that no root reached the target.
5. Cycles terminate by tracking visited components and never revisiting an already visited component for traversal expansion.
6. Self-loops are traversable edges, but a self-loop does not cause repeated expansion of an already visited component.
7. Disconnected components remain present in normalized IR but are ignored unless visited from a workload root.
8. Reachability is evaluated per workload. Each workload produces an independent result object.
9. Deterministic ordering is lexical by normalized identifiers unless an existing normalized IR array already defines a canonical lexical order; workload results, roots, reached roots, visited nodes, traversal edges, and diagnostics must be normalized before hashing and emitted in deterministic lexical order.
10. The reachability result hash boundary includes the canonical JSON result payload after semantic-array normalization, excluding `reachability_result_hash` itself and excluding no other result fields.

## Traversal semantics

Traversal consumes normalized IR, not source topology JSON or AST. The traversal graph is the normalized IR component set plus normalized directed edges and adjacency.

For each workload:

- roots are `workload.roots` from normalized IR after set normalization;
- the target is `workload.target` from normalized IR;
- traversal follows only outgoing adjacency entries from each current component;
- an edge from `A` to `B` permits traversal from `A` to `B` only;
- reverse adjacency is not used to discover forward reachability;
- traversal does not remove candidate components; complement projection is a later contract;
- traversal does not evaluate `expected_classification` or dependency predicates.

## Cycle semantics

Cycles are valid normalized IR topology. Traversal must terminate by keeping a visited component set for each workload result. Once a component has been visited, it must not be expanded again for that workload traversal.

Cycle detection is not an error. A cycle may appear in diagnostics only as informational contract evidence in fixtures; v1 reachability result shape does not require a cycle list.

## Multi-root semantics

A workload with multiple roots is evaluated as the union of deterministic root traversals. The result is reachable if at least one root can reach the target.

`reached_by` contains every root from which the target is reachable, sorted lexically by root identifier. Root traversal order must not affect the emitted result.

## Self-loop semantics

A self-loop edge is structurally traversable. If a component has an outgoing edge to itself, traversal observes the edge, records it in deterministic traversal evidence when evidence is emitted, and does not repeatedly expand the component after it is already visited.

If a root equals the target, reachability succeeds by the zero-length path regardless of whether a self-loop exists.

## Disconnected graph semantics

Disconnected components are preserved in normalized IR. They are not errors. Components in disconnected components that are not reachable from any workload root are omitted from `visited_nodes` for that workload result.

## Result shape

Reachability results are schema-only contract objects in `schemas/reachability.schema.json`. A result document contains:

- `schema_version`: `dependency-algebra.reachability.v1`
- `topology_id`
- `normalized_ir_hash`
- optional `reachability_result_hash`
- `results`: one result object per workload

Each workload result contains:

- `workload_id`
- `roots`
- `target`
- `reachable`
- `reached_by`
- `visited_nodes`
- `traversal_edges`
- `diagnostics`

`traversal_edges` is deterministic evidence, not full path enumeration. It records traversed directed edges as `{ edge_id, from, to }` entries sorted lexically by `edge_id`, then `from`, then `to`.

Diagnostics are deterministic structural messages scoped to reachability only. The canonical unreachable diagnostic code is `REACHABILITY.UNREACHABLE_TARGET`. Diagnostics are sorted by `code`, subject `kind`, subject `id`, and `message`.

## Determinism and hash boundary

Reachability result documents must be normalized before hashing. Canonical object formation is:

1. Deep-copy the result document.
2. Sort `results` by `workload_id`, then `target`.
3. For each workload result, sort `roots`, `reached_by`, and `visited_nodes` lexicographically.
4. Sort `traversal_edges` by `edge_id`, then `from`, then `to`.
5. Sort `diagnostics` by `code`, subject `kind`, subject `id`, and `message`.
6. Remove `reachability_result_hash` from the copied document if it is present.
7. Serialize the normalized copy as canonical UTF-8 JSON bytes with sorted object keys, compact separators, and no trailing newline.
8. Compute SHA-256 over those bytes and attach the final value as `reachability_result_hash`.

If two reachability documents carry the same dependency-algebra meaning, including equivalent arrays in different input orders, they must normalize to the same canonical result bytes and therefore the same `reachability_result_hash`.

No timestamp, absolute path, host environment, random value, authority token, proof token, governance field, policy field, execution field, or mutation field is inside the hash boundary because none is allowed in the schema.

## Fixtures and tests

Canonical reachability fixtures live under `fixtures/reachability/`:

- reachable single-root path
- unreachable target in a disconnected graph
- multi-root workload with partial root success
- cycle termination
- self-loop reachability

The tests validate fixture shape, deterministic ordering, forbidden-field exclusion, required fixture coverage, and canonical hash stability. They do not implement or expose a reachability engine.

## Remaining gaps before complement projection

Before complement projection can be specified or implemented, the project must still define:

- induced-subgraph construction for `¬S`
- candidate-removal hash boundaries
- how reachability results before and after projection are paired
- dependency predicate diagnostics
- classification transition rules from base reachability to projected reachability
