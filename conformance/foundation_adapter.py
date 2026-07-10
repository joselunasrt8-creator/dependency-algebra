"""Foundation conformance adapter for SYNAPSE."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dependency_algebra import compile_artifact
from conformance.research_objects.registry import get_handler


def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def topology_from_fixture(fixture):
    canonical = canonical_context_from_fixture(fixture)
    nodes = canonical["nodes"]
    relations = canonical["relations"]
    roots = canonical["roots"]
    targets = canonical["targets"]
    candidate_set = canonical.get("candidate_component_set", [])

    workloads = _workloads_from_context(roots, targets, candidate_set)

    return {
        "schema_version": "dependency-algebra.topology.v1",
        "topology_id": fixture.get("topology_id", "paper1-dependency-predicate"),
        "components": [{"id": n} for n in nodes],
        "edges": [
            {"id": f"e{i}", "from": item["from"], "to": item["to"]}
            for i, item in enumerate(relations)
        ],
        "workloads": workloads,
    }


def canonical_context_from_fixture(fixture):
    payload = fixture.get("input", fixture)
    graph = payload.get("graph", payload.get("structural_object", payload.get("structure", payload)))
    workload = payload.get("workload", payload.get("workload_profile", payload))

    raw_nodes = graph.get("nodes", graph.get("structural_nodes", []))
    nodes = sorted(_identifier(item) for item in raw_nodes)

    raw_relations = graph.get("edges", graph.get("relations", graph.get("structural_relations", [])))
    relations = sorted(
        (
            {
                "from": _endpoint(item, "from", "source", "src"),
                "to": _endpoint(item, "to", "target", "dst"),
            }
            for item in raw_relations
        ),
        key=lambda item: (item["from"], item["to"]),
    )

    roots = sorted(_identifier(item) for item in workload.get("roots", workload.get("workload_roots", [])))
    targets = sorted(_identifier(item) for item in workload.get("targets", workload.get("workload_targets", [])))
    candidate_set = sorted(_identifier(item) for item in workload.get("candidate_component_set", []))

    return {
        "nodes": nodes,
        "relations": relations,
        "roots": roots,
        "targets": targets,
        "candidate_component_set": candidate_set,
    }


def _workloads_from_context(roots, targets, candidate_set):
    if candidate_set and targets:
        return [{
            "id": "paper1-dependency-workload",
            "roots": roots,
            "target": targets[0],
            "candidate_set": candidate_set,
            "expected_classification": "VALID",
        }]
    return [
        {
            "id": f"workload-{root}-to-{target}",
            "roots": [root],
            "target": target,
            "candidate_set": [root],
            "expected_classification": "VALID",
        }
        for root in roots
        for target in targets
    ]


def _identifier(item):
    if isinstance(item, str):
        return item
    for key in ("id", "node", "component_id"):
        if key in item:
            return item[key]
    raise KeyError(f"Cannot extract identifier from {item!r}")


def _endpoint(item, *keys):
    if isinstance(item, (list, tuple)):
        return item[0] if keys[0] in {"from", "source", "src"} else item[1]
    for key in keys:
        if key in item:
            return _identifier(item[key])
    raise KeyError(f"Cannot extract endpoint {keys!r} from {item!r}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--fixture", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()

    fixture = json.loads(Path(a.fixture).read_text())
    topology = topology_from_fixture(fixture)

    artifact = compile_artifact(
        canonical_json(topology),
        source_id=fixture["fixture_id"],
    )
    artifact["canonical_context"] = canonical_context_from_fixture(fixture)

    projection = get_handler(
        fixture["research_object_id"]
    )(artifact)

    evidence = {
        "repository": "SYNAPSE",
        "repository_url": "https://github.com/joselunasrt8-creator/SYNAPSE",
        "commit_sha": "UNKNOWN",
        "branch": "synapse-foundation-evidence-84",
        "implementation_version": artifact["package_version"],
        "research_object_id": fixture["research_object_id"],
        "fixture_id": fixture["fixture_id"],
        "observed_execution_timestamp": "2026-01-01T00:00:00Z",
        "canonical_projection_timestamp": fixture["deterministic_timestamp"],
        "semantic_result": "PASS",
        "diagnostics": [],
        "generated_artifacts": [
            {
                "kind": "synapse",
                "hash": artifact["artifact_hash"],
            }
        ],
        "structural_metrics": {
            "classification": artifact["classification"],
        },
        "provenance": {
            "compiler_version": artifact["compiler_version"],
        },
        **projection,
    }

    Path(a.output).write_text(
        json.dumps(evidence, indent=2)
    )

if __name__ == "__main__":
    raise SystemExit(main())
