import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_MODULES = [
    ROOT / "dependency_algebra" / name
    for name in ("projection.py", "reachability.py", "predicate.py", "classification.py", "engine.py")
]


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_analysis_modules_do_not_call_sha256_digest(self):
        offenders = []
        for path in ANALYSIS_MODULES:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sha256_digest":
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "sha256_digest":
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
        self.assertEqual(offenders, [])

    def test_analysis_wrappers_delegate_serialization_boundary(self):
        expectations = {
            "projection.py": "projected_ir_to_dict",
            "reachability.py": "reachability_result_to_dict",
            "predicate.py": "dependency_result_to_dict",
            "engine.py": "analysis_result_to_dict",
        }
        for filename, serializer in expectations.items():
            with self.subTest(filename=filename):
                text = (ROOT / "dependency_algebra" / filename).read_text(encoding="utf-8")
                self.assertIn(serializer, text)

    def test_projected_ir_serialization_uses_canonical_removed_list(self):
        from dependency_algebra.ir import ProjectedIR
        from dependency_algebra.serialization import canonical_json_text, projected_ir_to_dict

        document = projected_ir_to_dict(ProjectedIR(removed=frozenset({"b", "a"}), adjacency={}, roots=()))
        self.assertEqual(document["removed"], ["a", "b"])
        self.assertEqual(canonical_json_text(document), '{"adjacency":{},"removed":["a","b"],"roots":[]}')


if __name__ == "__main__":
    unittest.main()
