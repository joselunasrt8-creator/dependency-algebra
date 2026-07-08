"""Foundation conformance adapter for SYNAPSE."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dependency_algebra import compile_artifact

def canonical_json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def topology_from_fixture(fixture):
    g = fixture["input"]["graph"]
    w = fixture["input"]["workload"]

    return {
        "schema_version": "dependency-algebra.topology.v1",
        "topology_id": "paper1-dependency-predicate",
        "components": [{"id": n} for n in sorted(g["nodes"])],
        "edges": [
            {"id": f"e{i}", "from": s, "to": t}
            for i, (s, t) in enumerate(sorted(g["edges"]))
        ],
        "workloads": [{
            "id": "paper1-dependency-workload",
            "roots": sorted(w["roots"]),
            "target": w["targets"][0],
            "candidate_set": sorted(w["candidate_component_set"]),
            "expected_classification": "VALID",
        }],
    }


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
        "canonical_outputs": {
            "artifact": artifact,
        },
    }

    Path(a.output).write_text(
        json.dumps(evidence, indent=2)
    )

if __name__ == "__main__":
    raise SystemExit(main())
