from __future__ import annotations

import json
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
        self.assertIn("Graphify Labs", acknowledgements)
        self.assertIn("Graphify contributors", acknowledgements)
        self.assertIn("OpenAI Codex", acknowledgements)
        self.assertIn("vibe coding", acknowledgements)
        self.assertIn("do not imply affiliation, sponsorship", normalized)

    def test_public_release_metadata_and_community_links_are_consistent(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        package = json.loads((ROOT / "web" / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "web" / "package-lock.json").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        runtime_version = (
            ROOT / "src" / "mql5_codegraph" / "version.py"
        ).read_text(encoding="utf-8")

        self.assertEqual("0.3.0", pyproject["project"]["version"])
        self.assertEqual("0.3.0", package["version"])
        self.assertEqual("0.3.0", lock["version"])
        self.assertEqual("0.3.0", lock["packages"][""]["version"])
        self.assertIn('__version__ = "0.3.0"', runtime_version)
        self.assertEqual(
            ["LICENSE", "THIRD_PARTY_NOTICES.md"],
            pyproject["project"]["license-files"],
        )
        self.assertIn("Status-Public%20Beta", readme)
        self.assertIn(
            "https://github.com/junet03/mql5-codegraph/graphs/contributors",
            readme,
        )
        self.assertIn("⭐ star the repository", readme)

    def test_public_security_policy_documents_provider_scoped_tokens(self) -> None:
        policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        normalized = " ".join(policy.split())
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        self.assertIn("GITHUB_TOKEN", policy)
        self.assertIn("selected backend", normalized)
        self.assertIn("version probe receives no provider secret", policy)
        self.assertIn("Cytoscape.js 3.34.0", notice)
        self.assertIn("Lucide React 0.468.0", notice)
        self.assertIn("React 19.2.6", notice)

    def test_package_ci_builds_and_verifies_dashboard_assets(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("Build bundled dashboard", workflow)
        self.assertIn("npm --prefix web run build", workflow)
        self.assertIn("tools/verify_release_artifact.py dist/*.whl", workflow)


if __name__ == "__main__":
    unittest.main()
