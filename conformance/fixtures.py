"""Canonical conformance fixture discovery and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from conformance.jsonutil import load_json, sha256_file
from conformance.research_objects.registry import get_handler

FIXTURE_SCHEMA_VERSION = "structural-analysis-foundations.conformance-fixture.v1"
DEFAULT_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


@dataclass(frozen=True)
class CanonicalFixture:
    path: Path
    document: dict
    fixture_hash: str

    @property
    def fixture_id(self) -> str:
        return self.document["fixture_id"]

    @property
    def research_object_id(self) -> str:
        return self.document["research_object_id"]


def discover_fixtures(root: Path = DEFAULT_FIXTURE_ROOT) -> tuple[CanonicalFixture, ...]:
    if not root.exists():
        return ()
    return tuple(
        CanonicalFixture(path=path, document=load_json(path), fixture_hash=sha256_file(path))
        for path in sorted(root.glob("*.json"))
    )


def load_fixture(path: Path) -> CanonicalFixture:
    return CanonicalFixture(path=path, document=load_json(path), fixture_hash=sha256_file(path))


def validate_fixture(fixture: CanonicalFixture) -> list[dict]:
    doc = fixture.document
    errors: list[dict] = []
    _require(doc.get("schema_version") == FIXTURE_SCHEMA_VERSION, errors, "schema_version", "unsupported fixture schema version")
    for field in ("fixture_id", "research_object_id", "deterministic_timestamp", "input", "expected_evidence"):
        _require(field in doc, errors, field, "missing required field")
    if errors:
        return errors
    try:
        get_handler(doc["research_object_id"])
    except KeyError:
        errors.append(_error("research_object_id", "unsupported research object"))
    expected = doc.get("expected_evidence")
    if not isinstance(expected, dict):
        errors.append(_error("expected_evidence", "expected evidence must be an object"))
    elif "canonical_outputs" not in expected:
        errors.append(_error("expected_evidence.canonical_outputs", "missing canonical outputs"))
    return errors


def validate_fixtures(fixtures: Iterable[CanonicalFixture]) -> dict[str, list[dict]]:
    return {fixture.fixture_id: validate_fixture(fixture) for fixture in fixtures}


def _require(condition: bool, errors: list[dict], path: str, message: str) -> None:
    if not condition:
        errors.append(_error(path, message))


def _error(path: str, message: str) -> dict:
    return {"path": path, "message": message}
