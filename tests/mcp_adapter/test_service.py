from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from mql5_codegraph.indexer import analyze_repository
from mql5_codegraph.intelligence import IntelligenceKernel
from mql5_codegraph.mcp.service import AdapterError, ProjectSession


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "basic_ea"


def _fixture_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class ProjectSessionTests(unittest.TestCase):
    def test_status_does_not_index_implicitly(self) -> None:
        session = ProjectSession()

        self.assertEqual(
            {"status": "not_indexed", "revision": 0},
            session.project_status(),
        )

    def test_query_requires_an_active_project(self) -> None:
        session = ProjectSession()

        with self.assertRaises(AdapterError) as raised:
            session.query_symbols("OnTick")

        self.assertEqual("project_not_indexed", raised.exception.code)

    def test_index_project_is_read_only_and_reports_identity(self) -> None:
        before = _fixture_hashes(FIXTURE_ROOT)
        session = ProjectSession()

        result = session.index_project(str(FIXTURE_ROOT))

        self.assertEqual("indexed", result["status"])
        self.assertEqual(1, result["revision"])
        self.assertEqual(str(FIXTURE_ROOT.resolve()), result["root"])
        self.assertGreater(result["counts"]["files"], 0)
        self.assertGreater(result["counts"]["nodes"], 0)
        self.assertGreater(result["counts"]["edges"], 0)
        self.assertTrue(result["graph_identity"]["source_fingerprint"])
        self.assertEqual(before, _fixture_hashes(FIXTURE_ROOT))

    def test_unchanged_project_reuses_the_published_revision(self) -> None:
        session = ProjectSession()
        first = session.index_project(str(FIXTURE_ROOT))

        second = session.index_project(str(FIXTURE_ROOT))

        self.assertEqual(first["revision"], second["revision"])
        self.assertTrue(second["reused"])

    def test_failed_reindex_keeps_the_last_valid_snapshot(self) -> None:
        session = ProjectSession()
        indexed = session.index_project(str(FIXTURE_ROOT))

        with self.assertRaises(AdapterError) as raised:
            session.index_project(str(FIXTURE_ROOT / "missing"))

        self.assertEqual("invalid_project_root", raised.exception.code)
        self.assertEqual(indexed["revision"], session.project_status()["revision"])
        self.assertEqual(indexed["graph_identity"], session.project_status()["graph_identity"])

    def test_changed_project_publishes_a_new_revision(self) -> None:
        session = ProjectSession()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "Example.mq5"
            source.write_text("void OnTick() {}\n", encoding="utf-8")
            first = session.index_project(str(root))
            source.write_text("void Helper() {}\nvoid OnTick() { Helper(); }\n", encoding="utf-8")

            second = session.index_project(str(root))

        self.assertEqual(first["revision"] + 1, second["revision"])
        self.assertNotEqual(
            first["graph_identity"]["source_fingerprint"],
            second["graph_identity"]["source_fingerprint"],
        )

    def test_query_result_conforms_to_direct_kernel_result(self) -> None:
        session = ProjectSession()
        session.index_project(str(FIXTURE_ROOT))
        request = {
            "contract_version": "1.0.0",
            "operation": "query",
            "targets": [{"value": "OnTick", "kind": None}],
            "direction": "both",
            "relationship_types": [],
            "node_kinds": [],
            "bounds": {
                "max_depth": 1,
                "max_items": 30,
                "max_paths": 3,
                "max_expansions": 10_000,
                "context_units": 100,
            },
            "expected_source_fingerprint": None,
            "client_request_id": None,
        }
        expected = IntelligenceKernel(
            analyze_repository(FIXTURE_ROOT),
            snapshot_revision=1,
        ).execute(request)

        actual = session.query_symbols("OnTick")

        self.assertEqual(expected.to_dict(), actual)


if __name__ == "__main__":
    unittest.main()
