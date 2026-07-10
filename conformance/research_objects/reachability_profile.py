"""Reachability Profile research object projection."""

from __future__ import annotations

from conformance.research_objects.registry import register

RESEARCH_OBJECT_ID = "concept.structural-observation.reachability-profile"


def reachability_profile_projection(artifact):
    context = artifact["canonical_context"]
    nodes = tuple(sorted(context["nodes"]))
    relations = tuple(sorted((item["from"], item["to"]) for item in context["relations"]))
    roots = tuple(sorted(context["roots"]))
    targets = tuple(sorted(context["targets"]))

    _validate_references(nodes, roots, targets)
    adjacency = {node: [] for node in nodes}
    for source, target in relations:
        adjacency[source].append(target)
    for outgoing in adjacency.values():
        outgoing.sort()

    reachable_pairs = []
    unreachable_pairs = []
    for root in roots:
        visited = _reachable_from(root, adjacency)
        for target in targets:
            pair = {"root": root, "target": target}
            if target in visited:
                reachable_pairs.append(pair)
            else:
                unreachable_pairs.append(pair)

    root_coverage = [
        {
            "root": root,
            "reachable_target_count": sum(1 for pair in reachable_pairs if pair["root"] == root),
            "unreachable_target_count": sum(1 for pair in unreachable_pairs if pair["root"] == root),
            "target_count": len(targets),
        }
        for root in roots
    ]
    target_coverage = [
        {
            "target": target,
            "reachable_root_count": sum(1 for pair in reachable_pairs if pair["target"] == target),
            "unreachable_root_count": sum(1 for pair in unreachable_pairs if pair["target"] == target),
            "root_count": len(roots),
        }
        for target in targets
    ]
    pair_count = len(roots) * len(targets)
    density = len(reachable_pairs) / pair_count if pair_count else 0.0
    invariants = _verify_invariants(roots, targets, reachable_pairs, unreachable_pairs, root_coverage, target_coverage, density)

    canonical_outputs = {
        "nodes": list(nodes),
        "relations": [{"from": source, "to": target} for source, target in relations],
        "roots": list(roots),
        "targets": list(targets),
        "reachable_pairs": reachable_pairs,
        "unreachable_pairs": unreachable_pairs,
        "root_coverage": root_coverage,
        "target_coverage": target_coverage,
        "reachability_density": density,
    }
    return {
        "canonical_outputs": canonical_outputs,
        "structural_metrics": {
            "node_count": len(nodes),
            "relation_count": len(relations),
            "root_count": len(roots),
            "target_count": len(targets),
            "pair_count": pair_count,
            "reachable_pair_count": len(reachable_pairs),
            "unreachable_pair_count": len(unreachable_pairs),
            "reachability_density": density,
        },
        "structural_invariants": invariants,
        "required_diagnostics": [
            {"code": "REACHABILITY_PROFILE_EVALUATED", "level": "info"},
            {"code": "REACHABILITY_INVARIANTS_VERIFIED", "level": "info"},
            {"code": "CANONICAL_ORDERING_CONFIRMED", "level": "info"},
        ],
    }


def _validate_references(nodes, roots, targets):
    node_set = set(nodes)
    missing_roots = sorted(root for root in roots if root not in node_set)
    missing_targets = sorted(target for target in targets if target not in node_set)
    if missing_roots or missing_targets:
        details = []
        if missing_roots:
            details.append("roots=" + ",".join(missing_roots))
        if missing_targets:
            details.append("targets=" + ",".join(missing_targets))
        raise ValueError("Unresolved reachability profile references: " + "; ".join(details))


def _reachable_from(root, adjacency):
    visited = set()
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for target in adjacency.get(node, ()):  # adjacency is already canonical ordered
            if target not in visited:
                queue.append(target)
        queue.sort()
    return visited


def _verify_invariants(roots, targets, reachable_pairs, unreachable_pairs, root_coverage, target_coverage, density):
    reachable = {(pair["root"], pair["target"]) for pair in reachable_pairs}
    unreachable = {(pair["root"], pair["target"]) for pair in unreachable_pairs}
    universe = {(root, target) for root in roots for target in targets}
    pair_count = len(universe)
    invariants = {
        "every_root_target_pair_classified": (reachable | unreachable) == universe,
        "reachable_unreachable_disjoint": not (reachable & unreachable),
        "classified_union_equals_roots_cross_targets": (reachable | unreachable) == universe,
        "root_coverage_counts_correct": all(
            item["reachable_target_count"] == sum(1 for root, _target in reachable if root == item["root"])
            and item["unreachable_target_count"] == sum(1 for root, _target in unreachable if root == item["root"])
            and item["target_count"] == len(targets)
            for item in root_coverage
        ),
        "target_coverage_counts_correct": all(
            item["reachable_root_count"] == sum(1 for _root, target in reachable if target == item["target"])
            and item["unreachable_root_count"] == sum(1 for _root, target in unreachable if target == item["target"])
            and item["root_count"] == len(roots)
            for item in target_coverage
        ),
        "pair_counts_consistent": len(reachable_pairs) + len(unreachable_pairs) == pair_count,
        "density_consistent": density == (len(reachable_pairs) / pair_count if pair_count else 0.0),
    }
    if not all(invariants.values()):
        failed = sorted(key for key, value in invariants.items() if not value)
        raise ValueError("Reachability profile invariant verification failed: " + ",".join(failed))
    return invariants


register(RESEARCH_OBJECT_ID, reachability_profile_projection)
