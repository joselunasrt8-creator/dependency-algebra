import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATH_TERMS = {"authority", "proof", "execution", "runtime", "policy", "governance", "continuityos"}


class BoundaryTests(unittest.TestCase):
    def test_no_forbidden_implementation_surface_exists(self):
        paths = [p for p in ROOT.rglob("*") if ".git" not in p.parts]
        offenders = []
        for path in paths:
            relative = path.relative_to(ROOT)
            lowered_parts = {part.lower() for part in relative.parts}
            if lowered_parts & FORBIDDEN_PATH_TERMS:
                offenders.append(str(relative))
        self.assertEqual(offenders, [])

    def test_boundary_document_declares_structural_only_classification(self):
        text = (ROOT / "BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("structural classifications only", text)
        self.assertIn("do not represent execution eligibility", text)
        self.assertIn("runtime authorization", text)

    def test_readme_excludes_runtime_and_governance_surfaces(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("structural compiler facade, analysis engine, canonical serialization utilities, and a thin CLI harness", text)
        self.assertIn("proof system, authority module, runtime hook, governance surface", text)


if __name__ == "__main__":
    unittest.main()
