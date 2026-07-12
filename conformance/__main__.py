"""Command-line entry point for the canonical conformance harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from conformance.runner import DEFAULT_REPORT_PATH, run
from conformance.status import PASS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m conformance")
    parser.add_argument("--fixture", action="append", default=[], help="Canonical fixture path. May be repeated. Defaults to all discovered fixtures.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT_PATH), help="Deterministic report output path.")
    args = parser.parse_args(argv)
    report = run(tuple(Path(item) for item in args.fixture), Path(args.report))
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if all(item["status"] == PASS for item in report["comparison_matrix"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
