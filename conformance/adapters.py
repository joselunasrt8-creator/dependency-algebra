"""Adapter registry loading for the canonical conformance harness."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from conformance.jsonutil import load_json

DEFAULT_ADAPTER_REGISTRY = Path(__file__).resolve().parent / "adapters.json"


@dataclass(frozen=True)
class Adapter:
    adapter_id: str
    command: tuple[str, ...]


def discover_adapters(path: Path = DEFAULT_ADAPTER_REGISTRY) -> tuple[Adapter, ...]:
    if not path.exists():
        return ()
    data = load_json(path)
    adapters = []
    for item in sorted(data.get("adapters", []), key=lambda value: value["adapter_id"]):
        command = tuple(sys.executable if token == "{python}" else token for token in item["command"])
        adapters.append(Adapter(adapter_id=item["adapter_id"], command=command))
    return tuple(adapters)
