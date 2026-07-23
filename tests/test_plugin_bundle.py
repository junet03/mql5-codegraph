from __future__ import annotations

import json
from pathlib import Path
import struct
import tomllib
import unittest


ROOT = Path(__file__).parents[1]
PLUGIN = ROOT / "plugins" / "mql5-codegraph-intelligence"
EXPECTED_SKILLS = {
    "mql5-architecture",
    "mql5-change-impact",
    "mql5-project-onboarding",
    "mql5-release-gate",
}


class PluginBundleTests(unittest.TestCase):
    def test_marketplace_points_to_the_versioned_plugin(self) -> None:
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual("mql5-codegraph-internal", marketplace["name"])
        self.assertEqual(1, len(marketplace["plugins"]))
        entry = marketplace["plugins"][0]
        self.assertEqual("mql5-codegraph-intelligence", entry["name"])
        source = entry["source"]
        self.assertEqual("local", source["source"])
        self.assertEqual(
            PLUGIN.resolve(),
            (ROOT / source["path"]).resolve(),
        )

    def test_manifest_and_mcp_entry_point_are_consistent(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        mcp = json.loads((PLUGIN / ".mcp.json").read_text(encoding="utf-8"))
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual("mql5-codegraph-intelligence", manifest["name"])
        self.assertEqual("MIT", manifest["license"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertEqual("./.mcp.json", manifest["mcpServers"])
        server = mcp["mcpServers"]["mql5-codegraph"]
        self.assertEqual("mql5-codegraph-mcp", server["command"])
        self.assertEqual([], server["args"])
        self.assertEqual(
            "mql5_codegraph.mcp.server:main",
            pyproject["project"]["scripts"]["mql5-codegraph-mcp"],
        )
        self.assertIn("mcp>=1.28.1,<2", pyproject["project"]["optional-dependencies"]["mcp"])

    def test_all_declared_skills_have_complete_frontmatter(self) -> None:
        skill_root = PLUGIN / "skills"
        actual = {path.name for path in skill_root.iterdir() if path.is_dir()}
        self.assertEqual(EXPECTED_SKILLS, actual)

        for name in sorted(actual):
            content = (skill_root / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---\n"), name)
            frontmatter = content.split("---\n", 2)[1]
            self.assertIn(f"name: {name}\n", frontmatter)
            self.assertIn("description: ", frontmatter)

    def test_repository_contains_the_declared_mit_license(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertEqual("MIT", pyproject["project"]["license"])
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 junet03", license_text)

    def test_social_preview_asset_meets_github_constraints(self) -> None:
        preview = ROOT / "docs" / "assets" / "mql5-codegraph-hero.png"
        data = preview.read_bytes()

        self.assertLess(len(data), 1_000_000)
        self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((1280, 640), (width, height))


if __name__ == "__main__":
    unittest.main()
