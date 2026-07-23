import contextlib
from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from xml.etree import ElementTree as ET

from mql5_codegraph.cli import run
from mql5_codegraph.graph import SourceLocation

from tests.intelligence.helpers import build_graph, make_edge, make_node


FIXTURE = Path(__file__).parent / "fixtures" / "basic_ea"


class CliTests(TestCase):
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
