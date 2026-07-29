from pathlib import Path
from unittest import TestCase

from mql5_codegraph.analysis_budget import (
    DEFAULT_MAX_WORK,
    MAX_MAX_WORK,
    AnalysisBudget,
    AnalysisBudgetExceeded,
)
from mql5_codegraph.indexer import analyze_repository
from mql5_codegraph.lexer import tokenize
from mql5_codegraph.parser import parse_source
from mql5_codegraph.resolver import ParsedUnit, build_graph
from mql5_codegraph.runtime import enrich_runtime
from mql5_codegraph.graph import CodeGraph


FIXTURE = Path(__file__).parent / "fixtures" / "basic_ea"


class AnalysisBudgetTests(TestCase):
    def test_default_and_explicit_limits_are_validated(self) -> None:
        self.assertEqual(1_000_000, DEFAULT_MAX_WORK)
        self.assertEqual(10_000_000, MAX_MAX_WORK)
        self.assertEqual(DEFAULT_MAX_WORK, AnalysisBudget().work_limit)
        self.assertEqual(7, AnalysisBudget(7).work_limit)
        for value in (0, -1, MAX_MAX_WORK + 1, True, 1.5, "7"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AnalysisBudget(value)

    def test_consumption_is_deterministic_and_never_overshoots(self) -> None:
        budget = AnalysisBudget(2)
        budget.consume("parsing")
        budget.consume("resolution")

        with self.assertRaises(AnalysisBudgetExceeded) as raised:
            budget.consume("runtime_enrichment")

        error = raised.exception
        self.assertEqual("analysis_budget_exceeded", error.code)
        self.assertEqual("runtime_enrichment", error.phase)
        self.assertEqual(2, error.work_used)
        self.assertEqual(2, error.work_limit)
        self.assertEqual(
            {
                "code": "analysis_budget_exceeded",
                "message": "Analysis work budget exhausted",
                "details": {
                    "phase": "runtime_enrichment",
                    "work_used": 2,
                    "work_limit": 2,
                },
            },
            error.to_dict(),
        )

    def test_source_discovery_exhaustion_returns_no_graph(self) -> None:
        with self.assertRaises(AnalysisBudgetExceeded) as raised:
            analyze_repository(FIXTURE, max_work=1)

        self.assertEqual("source_discovery", raised.exception.phase)
        self.assertLessEqual(
            raised.exception.work_used,
            raised.exception.work_limit,
        )

    def test_lexing_and_parsing_are_accounted_separately(self) -> None:
        source = "void OnTick() { Print(1); }\n"
        lex_budget = AnalysisBudget(MAX_MAX_WORK)
        tokenize(source, "Budget.mq5", budget=lex_budget)

        with self.assertRaises(AnalysisBudgetExceeded) as lexing:
            tokenize(source, "Budget.mq5", budget=AnalysisBudget(1))
        self.assertEqual("lexing", lexing.exception.phase)

        with self.assertRaises(AnalysisBudgetExceeded) as parsing:
            parse_source(
                source,
                "Budget.mq5",
                budget=AnalysisBudget(lex_budget.work_used + 1),
            )
        self.assertEqual("parsing", parsing.exception.phase)

    def test_resolution_and_runtime_enrichment_are_accounted(self) -> None:
        root = Path("D:/budget-fixture")
        unit = ParsedUnit(
            root / "Budget.mq5",
            "Budget.mq5",
            parse_source("void OnTick() {}", "Budget.mq5"),
        )
        with self.assertRaises(AnalysisBudgetExceeded) as resolution:
            build_graph(
                [unit],
                root,
                [],
                "fingerprint",
                budget=AnalysisBudget(1),
            )
        self.assertEqual("resolution", resolution.exception.phase)

        with self.assertRaises(AnalysisBudgetExceeded) as runtime:
            enrich_runtime(CodeGraph(), budget=AnalysisBudget(1))
        self.assertEqual("runtime_enrichment", runtime.exception.phase)
