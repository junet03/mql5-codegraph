from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).parents[1]


class PackagingPolicyTests(unittest.TestCase):
    def test_reference_extra_and_public_navigation_are_declared(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

        self.assertIn(
            "pypdf>=6.10,<7",
            pyproject["project"]["optional-dependencies"]["reference"],
        )
        self.assertIn(
            "pypdfium2>=5.7.1,<6",
            pyproject["project"]["optional-dependencies"]["reference"],
        )
        self.assertIn("docs/reference-corpus.md", readme)
        self.assertIn("ReferenceCorpus", architecture)
        self.assertIn("semantic_overlay_inference", architecture)

    def test_repository_contains_no_pdf_and_ignores_local_corpus_outputs(self) -> None:
        self.assertEqual([], list(ROOT.rglob("*.pdf")))
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/reference-corpus/", ignore)
        self.assertIn("/reference-overlays/", ignore)
        self.assertIn("/local-references/", ignore)

    def test_acknowledgements_credit_tools_without_endorsement(self) -> None:
        acknowledgements = (ROOT / "ACKNOWLEDGEMENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(acknowledgements.split())
        self.assertIn("Safi Shamsi", acknowledgements)
        self.assertIn("Graphify contributors", acknowledgements)
        self.assertIn("OpenAI Codex", acknowledgements)
        self.assertIn("vibe coding", acknowledgements)
        self.assertIn("do not imply affiliation, sponsorship", normalized)


if __name__ == "__main__":
    unittest.main()
