"""Argparse CLI adapter for the compiler facade."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from dependency_algebra import CompilerDiagnosticException, compile
from dependency_algebra.serialization import canonical_json_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dependency-algebra")
    parser.add_argument("--input", required=True, help="Path to UTF-8 topology JSON input.")
    parser.add_argument("--output", help="Optional path for canonical UTF-8 hash receipt JSON.")
    parser.add_argument("--max-depth", type=int, default=None, help="Optional reachability traversal depth limit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        input_path = Path(args.input)
        source = input_path.read_bytes()
        receipt = compile(source, source_id=input_path.stem, max_depth=args.max_depth)
        output = canonical_json_text(receipt)
        if args.output:
            _write_output_atomically(Path(args.output), output)
        else:
            print(output)
        return 0
    except CompilerDiagnosticException as exc:
        print(canonical_json_text(exc.diagnostic), file=sys.stderr)
        return 1
    except Exception:
        print(canonical_json_text({"schema_version": "dependency-algebra.internal-error.v1", "error": "internal compiler error"}), file=sys.stderr)
        return 2


def _write_output_atomically(path: Path, output: str) -> None:
    directory = path.parent if path.parent != Path("") else Path(".")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as handle:
        temp_name = handle.name
        try:
            handle.write(output)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise
    try:
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
