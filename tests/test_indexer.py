from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from mql5_codegraph.analysis_budget import (
    MAX_MAX_WORK,
    AnalysisBudget,
    AnalysisBudgetExceeded,
)
from mql5_codegraph.indexer import analyze_repository, discover_sources
from mql5_codegraph.parser import parse_source
from mql5_codegraph.resolver import ParsedUnit, _resolve_include, build_graph


FIXTURE = Path(__file__).parent / "fixtures" / "basic_ea"


class IndexerTests(TestCase):
    def test_include_resolution_rejects_absolute_paths_before_filesystem_probe(self) -> None:
        unit = ParsedUnit(
            Path("D:/repo/main.mq5"),
            "main.mq5",
            parse_source("", "main.mq5"),
        )

        with patch.object(Path, "is_file", side_effect=AssertionError("unexpected probe")):
            for target in (
                "C:\\outside\\Secrets.mqh",
                "\\\\server\\share\\Secrets.mqh",
                "/outside/Secrets.mqh",
            ):
                with self.subTest(target=target):
                    self.assertIsNone(
                        _resolve_include(unit, target, False, Path("D:/repo"), ())
                    )

    def test_parent_relative_include_resolves_only_inside_approved_root(self) -> None:
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            source = root / "sub" / "Main.mq5"
            include = root / "Shared.mqh"
            outside = base / "Outside.mqh"
            source.parent.mkdir(parents=True)
            source.write_text("", encoding="utf-8")
            include.write_text("", encoding="utf-8")
            outside.write_text("", encoding="utf-8")
            unit = ParsedUnit(
                source.resolve(),
                "sub/Main.mq5",
                parse_source("", "sub/Main.mq5"),
            )

            resolved = _resolve_include(unit, "../Shared.mqh", False, root, ())
            escaped = _resolve_include(unit, "../../Outside.mqh", False, root, ())

        self.assertEqual(include.resolve(), resolved)
        self.assertIsNone(escaped)

    def test_source_discovery_ignores_symlinks_that_escape_root(self) -> None:
        with TemporaryDirectory() as root_directory, TemporaryDirectory() as outside_directory:
            root = Path(root_directory)
            outside = Path(outside_directory) / "Outside.mq5"
            outside.write_text("void OnTick() {}", encoding="utf-8")
            link = root / "Linked.mq5"
            try:
                link.symlink_to(outside)
            except (NotImplementedError, OSError) as error:
                self.skipTest(f"symlink creation unavailable: {error}")

            sources = discover_sources(root)

        self.assertEqual([], sources)

    def test_builds_resolved_and_runtime_graph(self) -> None:
        graph = analyze_repository(FIXTURE)
        names = {node.qualified_name for node in graph.nodes.values()}
        relationships = {(graph.nodes[edge.source].name, edge.relationship,
                          graph.nodes[edge.target].name) for edge in graph.edges.values()}
        self.assertIn("CRiskManager::CalculateLots", names)
        self.assertIn(("BasicEA.mq5", "includes", "Risk.mqh"), relationships)
        self.assertIn(("MetaTrader 5 Terminal", "runtime_dispatches", "OnTick"), relationships)
        self.assertIn(("OrderSend", "may_trigger_event", "OnTradeTransaction"), relationships)
        self.assertTrue(any(item.code == "PARSE001" for item in graph.diagnostics))

    def test_serialization_is_deterministic(self) -> None:
        first = analyze_repository(FIXTURE).to_json()
        second = analyze_repository(FIXTURE).to_json()
        self.assertEqual(first, second)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            analyze_repository(FIXTURE).save(path)
            self.assertEqual(first, path.read_text(encoding="utf-8"))

    def test_default_analysis_is_deterministic_and_does_not_mutate_source(self) -> None:
        sources = sorted(
            path for path in FIXTURE.rglob("*") if path.suffix.lower() in {".mq5", ".mqh"}
        )
        before = {path: path.read_bytes() for path in sources}

        first = analyze_repository(FIXTURE).to_json()
        second = analyze_repository(FIXTURE).to_json()

        self.assertEqual(first, second)
        self.assertEqual(before, {path: path.read_bytes() for path in sources})

    def test_ambiguous_call_fan_out_is_bounded_during_resolution(self) -> None:
        root = Path("D:/budget-fixture")
        source = "\n".join(
            ["void OnTick() { FanOut(1); }"]
            + [f"void FanOut(CType{index} value) {{}}" for index in range(8)]
        )
        unit = ParsedUnit(root / "Budget.mq5", "Budget.mq5", parse_source(source, "Budget.mq5"))
        complete_budget = AnalysisBudget(MAX_MAX_WORK)
        graph, _ = build_graph([unit], root, [], "fingerprint", budget=complete_budget)
        call_edges = [edge for edge in graph.edges.values() if edge.relationship == "calls"]
        self.assertEqual(8, len(call_edges))

        with self.assertRaises(AnalysisBudgetExceeded) as raised:
            build_graph(
                [unit],
                root,
                [],
                "fingerprint",
                budget=AnalysisBudget(complete_budget.work_used - 1),
            )

        self.assertEqual("resolution", raised.exception.phase)
        self.assertLessEqual(
            raised.exception.work_used,
            raised.exception.work_limit,
        )

    def test_resolves_object_method_by_receiver_type_instead_of_same_scope(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Engine.mqh").write_text(
                """
class CWorker
  {
public:
   void Run()
     {
     }
  };

class CEngine
  {
private:
   CWorker m_worker;

public:
   void OnTick()
     {
      m_worker.Run();
     }
  };
""",
                encoding="utf-8",
            )
            (root / "ReceiverEA.mq5").write_text(
                """
#include "Engine.mqh"

CEngine g_engine;

void Run()
  {
  }

void OnTick()
  {
   g_engine.OnTick();
  }
""",
                encoding="utf-8",
            )

            graph = analyze_repository(root)

        global_handler = next(
            node for node in graph.nodes.values()
            if node.qualified_name == "OnTick"
        )
        engine_method = next(
            node for node in graph.nodes.values()
            if node.qualified_name == "CEngine::OnTick"
        )
        worker_method = next(
            node for node in graph.nodes.values()
            if node.qualified_name == "CWorker::Run"
        )
        global_call_edges = [
            edge for edge in graph.edges.values()
            if edge.source == global_handler.id and edge.relationship == "calls"
        ]
        member_call_edges = [
            edge for edge in graph.edges.values()
            if edge.source == engine_method.id and edge.relationship == "calls"
        ]

        self.assertEqual([engine_method.id], [edge.target for edge in global_call_edges])
        self.assertEqual(1.0, global_call_edges[0].confidence)
        self.assertEqual("g_engine", global_call_edges[0].attributes["qualifier"])
        self.assertEqual([worker_method.id], [edge.target for edge in member_call_edges])
        self.assertEqual(1.0, member_call_edges[0].confidence)
        self.assertEqual("m_worker", member_call_edges[0].attributes["qualifier"])
