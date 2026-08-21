from __future__ import annotations

import hashlib
import os
from pathlib import Path
from shutil import copy2, copytree
import tempfile
import unittest

from mql5_codegraph.indexer import analyze_repository
from mql5_codegraph.intelligence import IntelligenceKernel
from mql5_codegraph.mcp.service import AdapterError, ProjectSession, ReferenceSession
from mql5_codegraph.reference import BuildRequest, ReferenceCorpus, build_reference_corpus
from tests.reference_corpus.helpers import make_pdf


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

    def test_budget_exhaustion_keeps_the_last_valid_snapshot(self) -> None:
        session = ProjectSession()
        indexed = session.index_project(str(FIXTURE_ROOT))
        before_query = session.query_symbols("OnTick")

        with self.assertRaises(AdapterError) as raised:
            session.index_project(str(FIXTURE_ROOT), max_work=1)

        self.assertEqual("analysis_budget_exceeded", raised.exception.code)
        self.assertEqual("source_discovery", raised.exception.details["phase"])
        self.assertEqual(
            "analyzer_work_units",
            raised.exception.details["budget_kind"],
        )
        self.assertIs(True, raised.exception.details["not_model_token_limit"])
        self.assertEqual(
            [
                "narrow_project_root",
                "narrow_include_roots",
                "increase_max_work",
            ],
            raised.exception.details["recommended_actions"],
        )
        self.assertEqual(
            10_000_000,
            raised.exception.details["maximum_max_work"],
        )
        expected_status = dict(indexed)
        expected_status.pop("reused")
        self.assertEqual(expected_status, session.project_status())
        self.assertEqual(before_query, session.query_symbols("OnTick"))

    def test_initial_budget_exhaustion_leaves_session_unindexed(self) -> None:
        session = ProjectSession()

        with self.assertRaises(AdapterError) as raised:
            session.index_project(str(FIXTURE_ROOT), max_work=1)

        self.assertEqual("analysis_budget_exceeded", raised.exception.code)
        self.assertEqual({"status": "not_indexed", "revision": 0}, session.project_status())

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

    def test_compiler_evidence_requires_snapshot_and_preserves_it(self) -> None:
        session = ProjectSession()
        with self.assertRaises(AdapterError) as missing:
            session.correlate_compiler_log("compiler.log", "BasicEA.mq5")
        self.assertEqual("project_not_indexed", missing.exception.code)

        compiler_log = Path(__file__).parents[1] / "fixtures" / "compiler_logs" / "basic-success.log"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "basic_ea"
            copytree(FIXTURE_ROOT, root)
            log_path = root / "compiler.log"
            copy2(compiler_log, log_path)
            for source in root.rglob("*"):
                if source.suffix.lower() in {".mq5", ".mqh"}:
                    os.utime(source, ns=(1_000_000_000, 1_000_000_000))
            os.utime(log_path, ns=(2_000_000_000, 2_000_000_000))
            indexed = session.index_project(str(root))
            before = _fixture_hashes(root)

            result = session.correlate_compiler_log("compiler.log", "BasicEA.mq5")

            self.assertEqual("current", result["compiler_evidence"]["evidence_state"])
            self.assertEqual(indexed["revision"], session.project_status()["revision"])
            self.assertEqual(before, _fixture_hashes(root))


class ReferenceSessionTests(unittest.TestCase):
    def _build_corpus(self, root: Path) -> Path:
        inputs = root / "pdfs"
        corpus = root / "corpus"
        inputs.mkdir()
        make_pdf(
            inputs / "mql5.pdf",
            ["MQL5 Reference", "OrderSend sends a trade request."],
            [("Reference", 0, None), ("OrderSend", 1, 0)],
        )
        build_reference_corpus(BuildRequest(inputs, corpus))
        return corpus

    def test_status_does_not_discover_or_load_implicitly(self) -> None:
        session = ReferenceSession()
        self.assertEqual(
            {"status": "not_loaded", "revision": 0},
            session.reference_status(),
        )
        with self.assertRaises(AdapterError) as raised:
            session.search_reference("OrderSend")
        self.assertEqual("reference_not_loaded", raised.exception.code)
        with self.assertRaises(AdapterError) as relative:
            session.load_reference_corpus("relative-corpus")
        self.assertEqual("invalid_tool_arguments", relative.exception.code)

    def test_load_search_and_excerpt_conform_to_the_reference_core(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus_root = self._build_corpus(Path(directory))
            core = ReferenceCorpus.open(corpus_root)
            session = ReferenceSession()

            loaded = session.load_reference_corpus(str(corpus_root))
            actual = session.search_reference("OrderSend")
            expected = core.search("OrderSend")
            section_id = actual["results"][0]["section"]["section_id"]
            excerpt = session.get_reference_excerpt(section_id, max_chars=80)

            self.assertEqual(1, loaded["revision"])
            self.assertEqual(core.corpus_fingerprint, loaded["corpus_fingerprint"])
            self.assertEqual(expected, {k: v for k, v in actual.items() if k != "snapshot_revision"})
            self.assertEqual(1, actual["snapshot_revision"])
            self.assertEqual("reference_document", excerpt["evidence_class"])
            self.assertTrue(session.load_reference_corpus(str(corpus_root))["reused"])

    def test_failed_or_stale_load_preserves_the_active_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus_root = self._build_corpus(Path(directory))
            session = ReferenceSession()
            loaded = session.load_reference_corpus(str(corpus_root))

            with self.assertRaises(AdapterError) as missing:
                session.load_reference_corpus(str(Path(directory) / "missing"))
            self.assertEqual("invalid_reference_root", missing.exception.code)
            self.assertEqual(loaded["revision"], session.reference_status()["revision"])

            with self.assertRaises(AdapterError) as stale:
                session.search_reference(
                    "OrderSend",
                    expected_corpus_fingerprint="0" * 64,
                )
            self.assertEqual("reference_snapshot_stale", stale.exception.code)
            self.assertEqual(
                loaded["corpus_fingerprint"],
                session.reference_status()["corpus_fingerprint"],
            )


if __name__ == "__main__":
    unittest.main()
