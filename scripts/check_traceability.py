#!/usr/bin/env python3
"""Validate SYNAPSE specification-to-implementation traceability metadata."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "registry" / "traceability.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ALLOWED_STATUSES = {
    "VERIFIED",
    "PARTIAL",
    "MISSING_IMPLEMENTATION",
    "MISSING_SPECIFICATION",
    "MISSING_TEST",
    "AMBIGUOUS",
    "SUPERSEDED",
}
REQUIRED_ENTRY_FIELDS = (
    "spec_ref",
    "requirement",
    "implementation_path",
    "implementation_symbol",
    "test_path",
    "artifact_or_output",
    "status",
    "evidence",
    "exact_gap",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Traceability manifest path.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable validation report.")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    errors, warnings = validate_manifest(manifest_path)
    report = {
        "schema_version": "synapse.traceability-check.v1",
        "manifest": str(manifest_path.relative_to(ROOT) if manifest_path.is_relative_to(ROOT) else manifest_path),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }
    if args.json or errors:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    elif warnings:
        for warning in warnings:
            print(f"WARNING: {warning}")
        print("traceability validation passed")
    else:
        print("traceability validation passed")
    return 0 if not errors else 1


def validate_manifest(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # deterministic validation surface, not an import guard
        return [f"manifest unreadable: {exc}"], warnings

    if manifest.get("schema_version") != "synapse.traceability.v1":
        errors.append("manifest schema_version must be synapse.traceability.v1")
    statuses = set(manifest.get("statuses", []))
    if statuses != ALLOWED_STATUSES:
        errors.append("manifest statuses must exactly match allowed traceability statuses")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("manifest entries must be a non-empty array")
        return errors, warnings

    spec_refs_seen: set[str] = set()
    entry_keys_seen: set[tuple[str, str, str, str, str]] = set()
    for index, entry in enumerate(entries):
        prefix = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in REQUIRED_ENTRY_FIELDS:
            if field not in entry:
                errors.append(f"{prefix}.{field} is required")
        if missing := [field for field in REQUIRED_ENTRY_FIELDS if not entry.get(field) and field != "exact_gap"]:
            errors.append(f"{prefix} has empty required fields: {', '.join(missing)}")
        status = entry.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{prefix}.status {status!r} is not allowed")
        if status in {"PARTIAL", "MISSING_IMPLEMENTATION", "MISSING_SPECIFICATION", "MISSING_TEST", "AMBIGUOUS"} and not entry.get("exact_gap"):
            errors.append(f"{prefix}.exact_gap is required for non-verified/non-superseded status")
        entry_key = (entry.get("spec_ref", ""), entry.get("requirement", ""), entry.get("implementation_path", ""), entry.get("implementation_symbol", ""), entry.get("test_path", ""))
        if entry_key in entry_keys_seen:
            errors.append(f"{prefix} duplicates an existing traceability mapping")
        entry_keys_seen.add(entry_key)
        _validate_spec_ref(entry.get("spec_ref", ""), prefix, errors)
        spec_refs_seen.add(entry.get("spec_ref", ""))
        _validate_existing_file(entry.get("implementation_path", ""), f"{prefix}.implementation_path", errors)
        _validate_existing_file(entry.get("test_path", ""), f"{prefix}.test_path", errors)
        for optional_path_field in ("schema_path", "fixture_path"):
            optional_path = entry.get(optional_path_field, "")
            if optional_path:
                _validate_existing_file(optional_path, f"{prefix}.{optional_path_field}", errors)
        _validate_symbol(entry.get("implementation_path", ""), entry.get("implementation_symbol", ""), prefix, errors)

    if not any(ref.startswith("SPEC.md#7-frozen-contract-index") for ref in spec_refs_seen):
        errors.append("SPEC.md frozen contract index must have an explicit traceability entry")
    for behavior_index, behavior in enumerate(manifest.get("unspecified_public_behaviors", [])):
        prefix = f"unspecified_public_behaviors[{behavior_index}]"
        if behavior.get("status") != "MISSING_SPECIFICATION":
            warnings.append(f"{prefix} should use MISSING_SPECIFICATION status")
        _validate_existing_file(behavior.get("implementation_path", ""), f"{prefix}.implementation_path", errors)
        _validate_symbol(behavior.get("implementation_path", ""), behavior.get("implementation_symbol", ""), prefix, errors)
    return errors, warnings


def _validate_spec_ref(spec_ref: str, prefix: str, errors: list[str]) -> None:
    if "#" not in spec_ref:
        errors.append(f"{prefix}.spec_ref must include a section anchor")
        return
    file_name, anchor = spec_ref.split("#", 1)
    path = ROOT / file_name
    if not path.is_file():
        errors.append(f"{prefix}.spec_ref file does not exist: {file_name}")
        return
    headings = _markdown_anchors(path.read_text(encoding="utf-8"))
    if anchor not in headings:
        errors.append(f"{prefix}.spec_ref anchor not found: {spec_ref}")


def _markdown_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        if not title:
            continue
        anchor = re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")
        anchors.add(anchor)
    return anchors


def _validate_existing_file(path_text: str, field: str, errors: list[str]) -> None:
    if not path_text:
        return
    if not (ROOT / path_text).is_file():
        errors.append(f"{field} does not exist: {path_text}")


def _validate_symbol(path_text: str, symbol: str, prefix: str, errors: list[str]) -> None:
    if not path_text or not symbol or not path_text.endswith(".py") or not (ROOT / path_text).is_file():
        return
    module_name = path_text[:-3].replace("/", ".")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # deterministic validation surface, not an import guard
        errors.append(f"{prefix}.implementation_path could not be imported: {module_name}: {exc}")
        return
    if not hasattr(module, symbol):
        errors.append(f"{prefix}.implementation_symbol not found: {module_name}.{symbol}")


if __name__ == "__main__":
    raise SystemExit(main())
