import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "fixtures" / "valid" / "minimal-valid.json"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "dependency_algebra.cli", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CompilerCliIntegrationTests(unittest.TestCase):
    def test_valid_topology_stdout_success(self):
        result = run_cli("--input", str(VALID))
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["schema_version"], "dependency-algebra.hash-receipt.v1")
        self.assertEqual(receipt["classification"], "VALID")
        self.assertEqual(result.stderr, "")

    def test_malformed_json_exit_code_one(self):
        result = run_cli("--input", str(ROOT / "fixtures" / "invalid" / "malformed-json.json"))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        self.assertEqual(diagnostic["diagnostics"][0]["code"], "PARSER.INVALID_JSON")
        self.assertEqual(result.stdout, "")

    def test_unresolved_endpoint_exit_code_one(self):
        result = run_cli("--input", str(ROOT / "fixtures" / "invalid" / "unknown-node-reference.json"))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        codes = [item["code"] for item in diagnostic["diagnostics"]]
        self.assertIn("NORMALIZE.UNRESOLVED_EDGE_TO", codes)

    def test_duplicate_component_exit_code_one(self):
        result = run_cli("--input", str(ROOT / "fixtures" / "invalid" / "duplicate-identifiers.json"))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        codes = [item["code"] for item in diagnostic["diagnostics"]]
        self.assertIn("NORMALIZE.DUPLICATE_COMPONENT_ID", codes)

    def test_missing_ingress_exit_code_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing-ingress.json"
            doc = json.loads(VALID.read_text(encoding="utf-8"))
            doc["workloads"][0]["roots"] = []
            path.write_text(json.dumps(doc), encoding="utf-8")
            result = run_cli("--input", str(path))
        self.assertEqual(result.returncode, 1)
        diagnostic = json.loads(result.stderr)
        self.assertIn("AST.EMPTY_WORKLOAD_ROOTS", [item["code"] for item in diagnostic["diagnostics"]])

    def test_deterministic_repeated_execution(self):
        first = run_cli("--input", str(VALID))
        second = run_cli("--input", str(VALID))
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)

    def test_output_file_writing_suppresses_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "receipt.json"
            result = run_cli("--input", str(VALID), "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            receipt = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema_version"], "dependency-algebra.hash-receipt.v1")

    def test_unexpected_internal_errors_exit_code_two_without_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "not-a-file"
            out_dir.mkdir()
            result = run_cli("--input", str(VALID), "--output", str(out_dir))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertEqual(json.loads(result.stderr)["schema_version"], "dependency-algebra.internal-error.v1")


if __name__ == "__main__":
    unittest.main()
