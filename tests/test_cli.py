import contextlib
from hashlib import sha256
import io
import json
import os
from pathlib import Path
from shutil import copy2, copytree
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from xml.etree import ElementTree as ET

from mql5_codegraph.analysis_budget import AnalysisBudgetExceeded
from mql5_codegraph.cli import run
from mql5_codegraph.graph import SourceLocation

from tests.intelligence.helpers import build_graph, make_edge, make_node
from tests.reference_corpus.helpers import make_pdf


FIXTURE = Path(__file__).parent / "fixtures" / "basic_ea"


class CliTests(TestCase):
    def test_reference_graphify_discloses_processing_boundary_before_adapter(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        expected = {
            "contract_version": "1.0.0",
            "corpus_fingerprint": "a" * 64,
            "counts": {"nodes": 1, "edges": 0},
            "evidence_class": "semantic_overlay_inference",
            "manifest_sha256": "b" * 64,
            "overlay_fingerprint": "c" * 64,
            "processing_boundary": "remote",
            "producer": {"name": "graphify", "version": "0.9.27"},
            "reused": False,
            "snapshot_path": "snapshots/" + "c" * 64,
            "warnings": [],
        }
        with patch(
            "mql5_codegraph.cli.build_graphify_overlay",
            return_value=expected,
        ) as adapter:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = run(
                    [
                        "reference",
                        "graphify",
                        "D:\\corpus",
                        "--output",
                        "D:\\overlay",
                        "--graphify",
                        "graphify",
                        "--backend",
                        "openai",
                        "--processing-boundary",
                        "remote",
                        "--allow-remote",
                        "--json",
                    ]
                )
        self.assertEqual(0, exit_code)
        self.assertEqual(expected, json.loads(stdout.getvalue()))
        self.assertIn("corpus_content_may_leave_machine=true", stderr.getvalue())
        request = adapter.call_args.args[0]
        self.assertEqual("remote", request.processing_boundary)
        self.assertTrue(request.allow_remote)

    def test_reference_build_status_search_and_excerpt_share_one_contract(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = root / "pdfs"
            corpus = root / "corpus"
            inputs.mkdir()
            make_pdf(
                inputs / "mql5.pdf",
                ["MQL5 Reference", "OrderSend sends a trade request."],
                [("Reference", 0, None), ("OrderSend", 1, 0)],
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                build_exit = run(
                    [
                        "reference",
                        "build",
                        str(inputs),
                        "--output",
                        str(corpus),
                        "--json",
                    ]
                )
            self.assertEqual(0, build_exit)
            self.assertEqual("", stderr.getvalue())
            built = json.loads(stdout.getvalue())

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status_exit = run(
                    ["reference", "status", str(corpus), "--json"]
                )
            self.assertEqual(0, status_exit)
            status = json.loads(stdout.getvalue())
            self.assertEqual(
                built["corpus_fingerprint"],
                status["corpus_fingerprint"],
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                search_exit = run(
                    [
                        "reference",
                        "search",
                        str(corpus),
                        "OrderSend",
                        "--json",
                    ]
                )
            self.assertEqual(0, search_exit)
            search = json.loads(stdout.getvalue())
            section_id = search["results"][0]["section"]["section_id"]

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                excerpt_exit = run(
                    [
                        "reference",
                        "excerpt",
                        str(corpus),
                        section_id,
                        "--max-chars",
                        "80",
                        "--json",
                    ]
                )
            self.assertEqual(0, excerpt_exit)
            excerpt = json.loads(stdout.getvalue())
            self.assertEqual(
                search["results"][0]["section"]["content_sha256"],
                excerpt["section"]["content_sha256"],
            )

    def test_reference_errors_are_structured_on_stderr(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = run(
                [
                    "reference",
                    "status",
                    "not-a-real-corpus",
                    "--json",
                ]
            )
        self.assertEqual(1, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertEqual(
            "invalid_reference_root",
            json.loads(stderr.getvalue())["error"]["code"],
        )

    def test_normalized_path_uses_outgoing_defaults_and_emits_evidence(self) -> None:
        source = make_node("OnTick", node_id="node:on-tick")
        target = make_node("CalculateLots", node_id="node:calculate-lots")
        edge = make_edge(
            source,
            target,
            edge_id="edge:on-tick-calculate-lots",
            origin="resolved",
            confidence=0.9,
            location=SourceLocation("Expert.mq5", 12, 5),
        )
        graph = build_graph([target, source], [edge])

        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graph.save(graph_path)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = run(
                    [
                        "intelligence",
                        "path",
                        str(graph_path),
                        source.id,
                        target.id,
                        "--json",
                    ]
                )

        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertEqual("path", payload["operation"])
        self.assertEqual("outgoing", payload["request"]["direction"])
        self.assertEqual(
            {
                "context_units": 100,
                "max_depth": 5,
                "max_expansions": 10_000,
                "max_items": 30,
                "max_paths": 3,
            },
            payload["limits_applied"],
        )
        self.assertEqual(
            [source.id, target.id],
            payload["paths"][0]["node_ids"],
        )
        hop = payload["paths"][0]["hops"][0]
        self.assertEqual("forward", hop["direction"])
        self.assertEqual("resolved", hop["evidence"]["origin"])
        self.assertEqual(0.9, hop["evidence"]["confidence"])
        self.assertEqual(
            {"file": "Expert.mq5", "line": 12, "column": 5},
            hop["evidence"]["location"],
        )

    def test_normalized_path_accepts_explicit_bounds_and_filters(self) -> None:
        source = make_node("Source")
        target = make_node("Target")
        graph = build_graph(
            [source, target],
            [make_edge(source, target, relationship="calls")],
        )

        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graph.save(graph_path)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = run(
                    [
                        "intelligence",
                        "path",
                        str(graph_path),
                        source.id,
                        target.id,
                        "--direction",
                        "both",
                        "--max-depth",
                        "2",
                        "--max-paths",
                        "1",
                        "--max-expansions",
                        "25",
                        "--relationship-type",
                        "calls",
                        "--relationship-type",
                        "calls",
                        "--json",
                    ]
                )

        self.assertEqual(0, exit_code)
        payload = json.loads(stdout.getvalue())
        self.assertEqual("both", payload["request"]["direction"])
        self.assertEqual(["calls"], payload["request"]["relationship_types"])
        self.assertEqual(2, payload["limits_applied"]["max_depth"])
        self.assertEqual(1, payload["limits_applied"]["max_paths"])
        self.assertEqual(25, payload["limits_applied"]["max_expansions"])

    def test_normalized_path_preserves_stable_validation_errors(self) -> None:
        graph = build_graph([make_node("Source"), make_node("Target")])
        cases = (
            (["--contract-version", "2.0.0"], "unsupported_contract_version", "contract_version"),
            (["--max-depth", "-1"], "invalid_parameter", "bounds.max_depth"),
            (["--max-depth", "6"], "invalid_parameter", "bounds.max_depth"),
            (["--max-paths", "0"], "invalid_parameter", "bounds.max_paths"),
            (["--max-paths", "21"], "invalid_parameter", "bounds.max_paths"),
            (["--max-expansions", "0"], "invalid_parameter", "bounds.max_expansions"),
            (["--max-expansions", "100001"], "invalid_parameter", "bounds.max_expansions"),
        )

        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graph.save(graph_path)
            for options, error_code, field in cases:
                stdout = io.StringIO()
                stderr = io.StringIO()
                with self.subTest(options=options):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        exit_code = run(
                            [
                                "intelligence",
                                "path",
                                str(graph_path),
                                "Source",
                                "Target",
                                *options,
                                "--json",
                            ]
                        )
                    self.assertEqual(1, exit_code)
                    self.assertEqual("", stdout.getvalue())
                    error = json.loads(stderr.getvalue())["error"]
                    self.assertEqual(error_code, error["code"])
                    self.assertEqual(field, error["field"])

    def test_analyze_query_impact_and_export(self) -> None:
        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graphml_path = Path(directory) / "graph.graphml"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, run(["analyze", str(FIXTURE), "--output", str(graph_path), "--json"]))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, run(["query", str(graph_path), "OnTick", "--json"]))
            matches = json.loads(output.getvalue())
            self.assertEqual("OnTick", matches[0]["name"])

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(0, run(["impact", str(graph_path), "CalculateLots", "--json"]))
            impacted = json.loads(output.getvalue())
            self.assertTrue(any(item["node"]["name"] == "OnTick" for item in impacted))

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, run(["export", str(graph_path), "--format", "graphml",
                                         "--output", str(graphml_path), "--json"]))
            root = ET.parse(graphml_path).getroot()
            self.assertTrue(root.tag.endswith("graphml"))
            canonical_ids = {item["id"] for item in json.loads(graph_path.read_text(encoding="utf-8"))["nodes"]}
            graphml_ids = {element.attrib["id"] for element in root.iter() if element.tag.endswith("node")}
            self.assertEqual(canonical_ids, graphml_ids)

    def test_analyze_reports_budget_exhaustion_without_writing_output(self) -> None:
        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "budget-exhausted.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = run(
                    [
                        "analyze",
                        str(FIXTURE),
                        "--output",
                        str(graph_path),
                        "--max-work",
                        "1",
                        "--json",
                    ]
                )

            self.assertEqual(1, exit_code)
            self.assertEqual("", stdout.getvalue())
            self.assertFalse(graph_path.exists())
            error = json.loads(stderr.getvalue())["error"]
            self.assertEqual(AnalysisBudgetExceeded.code, error["code"])
            self.assertEqual("source_discovery", error["details"]["phase"])

    def test_analyze_rejects_an_invalid_max_work_before_indexing(self) -> None:
        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "invalid-budget.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = run(
                    [
                        "analyze",
                        str(FIXTURE),
                        "--output",
                        str(graph_path),
                        "--max-work",
                        "0",
                        "--json",
                    ]
                )

            self.assertEqual(1, exit_code)
            self.assertFalse(graph_path.exists())
            error = json.loads(stderr.getvalue())["error"]
            self.assertEqual("invalid_parameter", error["code"])
            self.assertEqual("max_work", error["field"])

    def test_serve_rejects_an_invalid_max_work_before_starting(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            exit_code = run(["serve", "--max-work", "0", "--no-browser"])

        self.assertEqual(1, exit_code)
        self.assertIn("max_work must be an integer", stderr.getvalue())

    def test_compiler_evidence_reports_current_log_without_mutating_inputs(self) -> None:
        compiler_log = Path(__file__).parent / "fixtures" / "compiler_logs" / "basic-success.log"
        with TemporaryDirectory() as directory:
            root = Path(directory) / "basic_ea"
            copytree(FIXTURE, root)
            log_path = root / "compiler.log"
            copy2(compiler_log, log_path)
            for source in root.rglob("*"):
                if source.suffix.lower() in {".mq5", ".mqh"}:
                    os.utime(source, ns=(1_000_000_000, 1_000_000_000))
            os.utime(log_path, ns=(2_000_000_000, 2_000_000_000))
            graph_path = Path(directory) / "graph.json"
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, run(["analyze", str(root), "--output", str(graph_path), "--json"]))
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = run(
                    [
                        "compiler-evidence",
                        str(graph_path),
                        "--entry",
                        "BasicEA.mq5",
                        "--log",
                        "compiler.log",
                        "--json",
                    ]
                )

            self.assertEqual(0, exit_code)
            result = json.loads(stdout.getvalue())
            self.assertEqual("current", result["compiler_evidence"]["evidence_state"])
            self.assertEqual("success", result["compiler_evidence"]["outcome"])
            outside_log = Path(directory) / "outside.log"
            outside_log.write_text("Result: 0 errors, 0 warnings", encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                invalid_exit = run(
                    [
                        "compiler-evidence",
                        str(graph_path),
                        "--entry",
                        "BasicEA.mq5",
                        "--log",
                        str(outside_log),
                        "--json",
                    ]
                )
            self.assertEqual(1, invalid_exit)
            self.assertEqual(
                "compiler_log_outside_root",
                json.loads(stderr.getvalue())["error"]["code"],
            )
            self.assertEqual(
                before,
                {
                    path.relative_to(root).as_posix(): path.read_bytes()
                    for path in root.rglob("*")
                    if path.is_file()
                },
            )

    def test_legacy_contract_golden_bytes(self) -> None:
        contract = json.loads(
            (Path(__file__).parent / "fixtures" / "contracts" / "legacy_cli.json").read_text(
                encoding="utf-8"
            )
        )
        if contract.get("newline") == "LF":
            for source_path in FIXTURE.rglob("*"):
                if source_path.suffix.lower() in {".mq5", ".mqh"}:
                    self.assertNotIn(
                        b"\r",
                        source_path.read_bytes(),
                        f"{source_path.name} must preserve the contract's LF newlines",
                    )
        with TemporaryDirectory() as directory:
            graph_path = Path(directory) / "graph.json"
            graphml_path = Path(directory) / "graph.graphml"
            replacements = {
                "<SOURCE>": str(FIXTURE.resolve()),
                "<GRAPH>": str(graph_path),
                "<GRAPHML>": str(graphml_path),
            }
            for case in contract["cases"]:
                arguments = [
                    replacements.get(argument, argument)
                    for argument in case["arguments"]
                ]
                stdout = io.StringIO()
                stderr = io.StringIO()
                with self.subTest(case=case["name"]):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        exit_code = run(arguments)
                    actual = stdout.getvalue()
                    if "stdout_json" in case:
                        value = json.loads(actual)
                        if "output" in value:
                            value["output"] = (
                                "<GRAPHML>"
                                if case["name"].startswith("export")
                                else "<GRAPH>"
                            )
                        actual = (
                            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
                            + "\n"
                        )
                        self.assertEqual(case["stdout_json"], value)
                    else:
                        actual = actual.replace(str(graph_path), "<GRAPH>").replace(
                            str(graphml_path), "<GRAPHML>"
                        )
                        self.assertEqual(case["stdout"], actual)
                    self.assertEqual(case["exit_code"], exit_code)
                    self.assertEqual(case["stderr"], stderr.getvalue())
                    self.assertEqual(
                        case["stdout_sha256"],
                        sha256(actual.encode(contract["encoding"])).hexdigest(),
                    )
