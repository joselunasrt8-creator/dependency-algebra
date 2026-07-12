"""Canonical conformance orchestration."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from conformance.adapters import Adapter, discover_adapters
from conformance.compare import compare
from conformance.evidence import validate_evidence
from conformance.fixtures import CanonicalFixture, discover_fixtures, load_fixture, validate_fixture
from conformance.jsonutil import load_json, sha256_file, sha256_value
from conformance.status import BLOCKED, DRIFT, FAIL, NOT_APPLICABLE, PASS, UNOBSERVED

REPORT_SCHEMA_VERSION = "structural-analysis-foundations.conformance-report.v1"
DEFAULT_REPORT_PATH = Path("conformance_artifacts/report.json")


def run(fixture_paths: tuple[Path, ...] = (), report_path: Path = DEFAULT_REPORT_PATH) -> dict[str, Any]:
    fixtures = tuple(load_fixture(path) for path in fixture_paths) if fixture_paths else discover_fixtures()
    adapters = discover_adapters()
    results = []
    for fixture in fixtures:
        fixture_errors = validate_fixture(fixture)
        if fixture_errors:
            results.append(_blocked_fixture_result(fixture, fixture_errors))
            continue
        if not adapters:
            results.append(_unobserved_fixture_result(fixture))
            continue
        for adapter in adapters:
            results.append(_run_adapter_fixture(adapter, fixture))
    report = _report(results)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _run_adapter_fixture(adapter: Adapter, fixture: CanonicalFixture) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "evidence.json"
        command = list(adapter.command) + ["--fixture", str(fixture.path), "--output", str(output), "--adapter-id", adapter.adapter_id]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            return _result(fixture, adapter.adapter_id, FAIL, blockers=[{
                "path": "adapter.returncode",
                "message": "adapter execution failed",
                "returncode": completed.returncode,
                "stderr": completed.stderr,
            }])
        if not output.exists():
            return _result(fixture, adapter.adapter_id, FAIL, blockers=[{"path": "adapter.output", "message": "adapter did not write evidence"}])
        try:
            evidence = load_json(output)
        except Exception as exc:
            return _result(fixture, adapter.adapter_id, FAIL, blockers=[{"path": "adapter.output", "message": f"malformed evidence: {exc}"}])
        validation_errors = validate_evidence(evidence, fixture_id=fixture.fixture_id, research_object_id=fixture.research_object_id, adapter_id=adapter.adapter_id)
        if validation_errors:
            return _result(fixture, adapter.adapter_id, FAIL, blockers=validation_errors, evidence=evidence)
        if evidence.get("semantic_result") in {"BLOCKED", "NOT_APPLICABLE", "UNOBSERVED"}:
            return _result(fixture, adapter.adapter_id, evidence["semantic_result"], blockers=evidence.get("diagnostics", []), evidence=evidence)
        matched, mismatches = compare(fixture.document["expected_evidence"], evidence)
        replay = _replay(adapter, fixture, evidence)
        status = PASS if matched and replay["status"] == PASS else DRIFT
        return _result(fixture, adapter.adapter_id, status, mismatches=mismatches, evidence=evidence, replay=replay)


def _replay(adapter: Adapter, fixture: CanonicalFixture, first_evidence: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "evidence.json"
        command = list(adapter.command) + ["--fixture", str(fixture.path), "--output", str(output), "--adapter-id", adapter.adapter_id]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0 or not output.exists():
            return {"status": FAIL, "message": "replay execution failed"}
        second = load_json(output)
    first_hash = sha256_value(first_evidence)
    second_hash = sha256_value(second)
    return {"status": PASS if first_hash == second_hash else DRIFT, "first_evidence_hash": first_hash, "second_evidence_hash": second_hash}


def _blocked_fixture_result(fixture: CanonicalFixture, errors: list[dict[str, Any]]) -> dict[str, Any]:
    return _result(fixture, "__fixture_validation__", BLOCKED, blockers=errors)


def _unobserved_fixture_result(fixture: CanonicalFixture) -> dict[str, Any]:
    return _result(fixture, "__missing_adapter__", UNOBSERVED, blockers=[{"path": "adapter", "message": "no adapters discovered"}])


def _result(fixture: CanonicalFixture, adapter_id: str, status: str, *, mismatches=(), blockers=(), evidence=None, replay=None) -> dict[str, Any]:
    evidence_hash = sha256_value(evidence) if evidence is not None else None
    return {
        "adapter_id": adapter_id,
        "research_object_id": fixture.research_object_id,
        "fixture_id": fixture.fixture_id,
        "fixture_path": str(fixture.path),
        "fixture_hash": fixture.fixture_hash,
        "status": status,
        "mismatches": list(mismatches),
        "blockers": list(blockers),
        "evidence_hash": evidence_hash,
        "replay": replay or {"status": UNOBSERVED},
    }


def _report(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {status: sum(1 for item in results if item["status"] == status) for status in sorted({item["status"] for item in results} | {PASS, DRIFT, FAIL, BLOCKED, NOT_APPLICABLE, UNOBSERVED})}
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "summary": summary,
        "per_research_object": _group_status(results, "research_object_id"),
        "per_adapter": _group_status(results, "adapter_id"),
        "comparison_matrix": results,
        "mismatches": [m for item in results for m in item["mismatches"]],
        "blockers": [b for item in results for b in item["blockers"]],
        "provenance": {"runner": "conformance.runner", "fixture_count": len({item["fixture_id"] for item in results})},
        "schema_versions": {"report": REPORT_SCHEMA_VERSION, "evidence": "structural-analysis-foundations.conformance-evidence.v1"},
    }


def _group_status(results: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = {}
    for item in results:
        bucket = grouped.setdefault(item[key], {})
        bucket[item["status"]] = bucket.get(item["status"], 0) + 1
    return {key: dict(sorted(value.items())) for key, value in sorted(grouped.items())}
