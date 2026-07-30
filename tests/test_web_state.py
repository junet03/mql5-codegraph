from pathlib import Path
from threading import Event
from time import monotonic, sleep
from unittest import TestCase

from mql5_codegraph.graph import CodeGraph
from mql5_codegraph.intelligence import IntelligenceKernel
from mql5_codegraph.web.state import DashboardState


FIXTURE = Path(__file__).parent / "fixtures" / "basic_ea"


def wait_for_job(state: DashboardState, job_id: str, timeout: float = 3.0):
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        job = state.get_job(job_id)
        if job and job.status in {"completed", "failed"}:
            return job
        sleep(0.01)
    raise AssertionError("analysis job did not finish")


class DashboardStateTests(TestCase):
    def test_analysis_replaces_graph_atomically(self) -> None:
        state = DashboardState(authorized_root=FIXTURE)
        job = state.start_analysis()
        finished = wait_for_job(state, job.id)
        graph, root, version = state.snapshot()
        self.assertEqual("completed", finished.status)
        self.assertIsNotNone(graph)
        self.assertEqual(FIXTURE.resolve(), root)
        self.assertEqual(1, version)
        self.assertTrue(state.status()["ready"])

    def test_only_one_analysis_runs_at_a_time(self) -> None:
        release = Event()

        def slow_analyzer(root, includes):
            release.wait(2)
            return CodeGraph({"file_count": 0})

        state = DashboardState(analyzer=slow_analyzer, authorized_root=FIXTURE)
        first = state.start_analysis()
        with self.assertRaisesRegex(RuntimeError, "already running"):
            state.start_analysis()
        release.set()
        self.assertEqual("completed", wait_for_job(state, first.id).status)

    def test_failed_reindex_keeps_previous_graph(self) -> None:
        calls = 0

        def analyzer(root, includes):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise ValueError("synthetic failure")
            return CodeGraph({"file_count": 1})

        state = DashboardState(analyzer=analyzer, authorized_root=FIXTURE)
        wait_for_job(state, state.start_analysis().id)
        original, _, version = state.snapshot()
        failed = wait_for_job(state, state.start_analysis().id)
        current, _, current_version = state.snapshot()
        self.assertEqual("failed", failed.status)
        self.assertIs(original, current)
        self.assertEqual(version, current_version)
        self.assertEqual("synthetic failure", state.status()["last_error"])

    def test_budget_exhaustion_keeps_previous_graph(self) -> None:
        state = DashboardState(authorized_root=FIXTURE)
        completed = wait_for_job(state, state.start_analysis().id)
        original, _, version = state.snapshot()

        exhausted = wait_for_job(state, state.start_analysis(max_work=1).id)
        current, _, current_version = state.snapshot()

        self.assertEqual("completed", completed.status)
        self.assertEqual("failed", exhausted.status)
        self.assertEqual("analysis_budget_exceeded", exhausted.error_code)
        self.assertEqual("source_discovery", exhausted.error_details["phase"])
        self.assertIs(original, current)
        self.assertEqual(version, current_version)

    def test_graph_and_kernel_snapshots_are_published_as_one_revision(self) -> None:
        first_graph = CodeGraph({"source_fingerprint": "first"})
        second_graph = CodeGraph({"source_fingerprint": "second"})
        state = DashboardState()

        state.load_graph(first_graph, FIXTURE)
        graph, kernel, root, revision = state.intelligence_snapshot()
        self.assertIs(first_graph, graph)
        self.assertIsInstance(kernel, IntelligenceKernel)
        self.assertEqual("first", kernel.graph_identity.source_fingerprint)
        self.assertEqual(revision, kernel.graph_identity.snapshot_revision)
        self.assertEqual(FIXTURE.resolve(), root)

        state.load_graph(second_graph, FIXTURE)
        graph, kernel, _, revision = state.intelligence_snapshot()
        self.assertIs(second_graph, graph)
        self.assertEqual("second", kernel.graph_identity.source_fingerprint)
        self.assertEqual(revision, kernel.graph_identity.snapshot_revision)

    def test_saved_graph_root_is_optional_and_not_inferred(self) -> None:
        state = DashboardState()
        graph = CodeGraph({"root": "D:/untrusted/metadata"})

        state.load_graph(graph)

        loaded, _, root, revision = state.intelligence_snapshot()
        self.assertIs(graph, loaded)
        self.assertIsNone(root)
        self.assertEqual(1, revision)

    def test_failed_reload_retains_matching_graph_and_kernel_pair(self) -> None:
        calls = 0

        def analyzer(root, includes):
            nonlocal calls
            calls += 1
            if calls > 1:
                raise ValueError("reload failed")
            return CodeGraph({"source_fingerprint": "stable"})

        state = DashboardState(analyzer=analyzer, authorized_root=FIXTURE)
        wait_for_job(state, state.start_analysis().id)
        before = state.intelligence_snapshot()
        wait_for_job(state, state.start_analysis().id)
        after = state.intelligence_snapshot()
        self.assertIs(before[0], after[0])
        self.assertIs(before[1], after[1])
        self.assertEqual(before[3], after[3])

    def test_analysis_requires_an_operator_authorized_root(self) -> None:
        state = DashboardState()

        with self.assertRaisesRegex(PermissionError, "--root"):
            state.start_analysis()
