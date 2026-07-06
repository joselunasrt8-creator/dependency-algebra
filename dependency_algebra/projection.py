"""Complement projection for normalized Dependency Algebra IR.

This module performs only structural projection: selecting removed candidates,
constructing projected adjacency, and filtering roots. It makes no dependency
semantic decisions, computes no hashes, and performs no classification.
"""

from __future__ import annotations

from typing import Any


def complement_projection(ir: dict[str, Any], workload: dict[str, Any]) -> dict[str, Any]:
    """Return the workload complement projection as structural traversal inputs."""

    candidates = set(workload["candidate_set"])
    adjacency = {
        component["id"]: [edge for edge in ir["adjacency"][component["id"]] if edge["component_id"] not in candidates]
        for component in ir["components"]
        if component["id"] not in candidates
    }
    roots = [root for root in workload["roots"] if root not in candidates]
    return {"removed": candidates, "adjacency": adjacency, "roots": roots}
