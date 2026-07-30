"""Composable command-line interface for MQL5 CodeGraph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Sequence

from .analysis_budget import AnalysisBudget, AnalysisBudgetExceeded
from .compiler_evidence import (
    CompilerEvidenceError,
    correlate_compiler_log,
    correlation_result,
)
from .exporters.graphml import export_graphml
from .graph import CodeGraph
from .indexer import analyze_repository
from .intelligence import (
    IntelligenceError,
    IntelligenceKernel,
)
from .intelligence.models import GraphIdentity
from .reference import (
    BuildRequest,
    GraphifyRequest,
    ReferenceCorpus,
    ReferenceError,
    build_graphify_overlay,
    build_reference_corpus,
)


def _emit(value: Any, as_json: bool, human: str | None = None) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    elif human is not None:
        print(human)
    else:
        print(value)


def _emit_error(value: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(
            json.dumps({"error": value}, ensure_ascii=False, indent=2, sort_keys=True),
            file=sys.stderr,
        )
    else:
        print(f"error: {value['message']}", file=sys.stderr)


def _matches(graph: CodeGraph, symbol: str) -> list[str]:
    exact = [node.id for node in graph.nodes.values()
             if node.name.casefold() == symbol.casefold()
             or node.qualified_name.casefold() == symbol.casefold()]
    return sorted(exact or [node.id for node in graph.find_nodes(symbol)])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mql5-codegraph", description="MQL5 static code graph indexer")
    parser.add_argument("--version", action="version", version="%(prog)s 0.2.0")
    subcommands = parser.add_subparsers(dest="command", required=True)

    analyze = subcommands.add_parser("analyze", help="Analyze an MQL5 source tree")
    analyze.add_argument("root")
    analyze.add_argument("--output", "-o", required=True)
    analyze.add_argument("--include-root", action="append", default=[])
    analyze.add_argument("--exclude", action="append", default=[])
    analyze.add_argument("--max-work", type=int)
    analyze.add_argument("--json", action="store_true")

    status = subcommands.add_parser("status", help="Show saved graph metadata")
    status.add_argument("graph")
    status.add_argument("--json", action="store_true")

    query = subcommands.add_parser("query", help="Find graph nodes")
    query.add_argument("graph")
    query.add_argument("text")
    query.add_argument("--kind")
    query.add_argument("--json", action="store_true")

    context = subcommands.add_parser("context", help="Inspect a symbol neighborhood")
    context.add_argument("graph")
    context.add_argument("symbol")
    context.add_argument("--depth", type=int, default=1)
    context.add_argument("--json", action="store_true")

    impact = subcommands.add_parser("impact", help="Traverse upstream graph impact")
    impact.add_argument("graph")
    impact.add_argument("symbol")
    impact.add_argument("--depth", type=int, default=3)
    impact.add_argument("--json", action="store_true")

    intelligence = subcommands.add_parser(
        "intelligence", help="Run normalized versioned intelligence operations"
    )
    intelligence_operations = intelligence.add_subparsers(
        dest="intelligence_operation", required=True
    )
    defaults = {
        "query": (1, 30, "both"),
        "context": (1, 900, "both"),
        "impact": (3, 2000, "incoming"),
        "diagnostics": (1, 250, "both"),
    }
    for operation, (depth, items, direction) in defaults.items():
        operation_parser = intelligence_operations.add_parser(operation)
        operation_parser.add_argument("graph")
        if operation != "diagnostics":
            operation_parser.add_argument("target")
        operation_parser.add_argument("--contract-version", default="1")
        operation_parser.add_argument("--max-depth", type=int, default=depth)
        operation_parser.add_argument("--max-items", type=int, default=items)
        operation_parser.add_argument(
            "--direction",
            choices=["incoming", "outgoing", "both"],
            default=direction,
        )
        operation_parser.add_argument(
            "--relationship-type", action="append", default=[]
        )
        operation_parser.add_argument("--json", action="store_true")

    path = intelligence_operations.add_parser("path")
    path.add_argument("graph")
    path.add_argument("source")
    path.add_argument("target")
    path.add_argument("--contract-version", default="1")
    path.add_argument("--max-depth", type=int, default=5)
    path.add_argument("--max-paths", type=int, default=3)
    path.add_argument("--max-expansions", type=int, default=10_000)
    path.add_argument(
        "--direction",
        choices=["incoming", "outgoing", "both"],
        default="outgoing",
    )
    path.add_argument("--relationship-type", action="append", default=[])
    path.add_argument("--json", action="store_true")

    context_package = intelligence_operations.add_parser("context-package")
    context_package.set_defaults(intelligence_operation="context_package")
    context_package.add_argument("graph")
    context_package.add_argument("target")
    context_package.add_argument("--contract-version", default="1")
    context_package.add_argument("--max-depth", type=int, default=2)
    context_package.add_argument("--context-units", type=int, default=100)
    context_package.add_argument("--max-expansions", type=int, default=10_000)
    context_package.add_argument(
        "--direction",
        choices=["incoming", "outgoing", "both"],
        default="both",
    )
    context_package.add_argument(
        "--relationship-type", action="append", default=[]
    )
    context_package.add_argument("--node-kind", action="append", default=[])
    context_package.add_argument("--json", action="store_true")

    export = subcommands.add_parser("export", help="Export a saved graph")
    export.add_argument("graph")
    export.add_argument("--format", choices=["graphml"], required=True)
    export.add_argument("--output", "-o", required=True)
    export.add_argument("--json", action="store_true")

    compiler_evidence = subcommands.add_parser(
        "compiler-evidence",
        help="Correlate an operator-supplied MetaEditor log with a saved graph",
    )
    compiler_evidence.add_argument("graph")
    compiler_evidence.add_argument("--entry", required=True)
    compiler_evidence.add_argument("--log", required=True)
    compiler_evidence.add_argument("--exclude", action="append", default=[])
    compiler_evidence.add_argument("--json", action="store_true")

    reference = subcommands.add_parser(
        "reference",
        help="Build and query a local page-aware reference corpus",
    )
    reference_operations = reference.add_subparsers(
        dest="reference_operation",
        required=True,
    )
    reference_build = reference_operations.add_parser(
        "build",
        help="Build an immutable corpus from local PDF files",
    )
    reference_build.add_argument("input_dir")
    reference_build.add_argument("--output", "-o", required=True)
    reference_build.add_argument("--sources")
    reference_build.add_argument(
        "--max-pdf-bytes",
        type=int,
        default=512 * 1024 * 1024,
    )
    reference_build.add_argument(
        "--max-pages-per-source",
        type=int,
        default=20_000,
    )
    reference_build.add_argument(
        "--max-pages-per-section",
        type=int,
        default=32,
    )
    reference_build.add_argument("--json", action="store_true")

    reference_status = reference_operations.add_parser(
        "status",
        help="Validate and describe the current corpus snapshot",
    )
    reference_status.add_argument("corpus_root")
    reference_status.add_argument("--json", action="store_true")

    reference_search = reference_operations.add_parser(
        "search",
        help="Search cited reference evidence",
    )
    reference_search.add_argument("corpus_root")
    reference_search.add_argument("query")
    reference_search.add_argument("--limit", type=int, default=20)
    reference_search.add_argument("--max-excerpt-chars", type=int, default=1_200)
    reference_search.add_argument("--json", action="store_true")

    reference_excerpt = reference_operations.add_parser(
        "excerpt",
        help="Read a bounded exact section excerpt",
    )
    reference_excerpt.add_argument("corpus_root")
    reference_excerpt.add_argument("section_id")
    reference_excerpt.add_argument("--start", type=int, default=0)
    reference_excerpt.add_argument("--max-chars", type=int, default=1_200)
    reference_excerpt.add_argument("--json", action="store_true")

    reference_graphify = reference_operations.add_parser(
        "graphify",
        help="Build a separate non-normative Graphify semantic overlay",
    )
    reference_graphify.add_argument("corpus_root")
    reference_graphify.add_argument("--output", "-o", required=True)
    reference_graphify.add_argument("--graphify", required=True)
    reference_graphify.add_argument(
        "--backend",
        choices=["gemini", "kimi", "claude", "openai", "deepseek", "ollama"],
        required=True,
    )
    reference_graphify.add_argument(
        "--processing-boundary",
        choices=["local", "remote"],
        required=True,
    )
    reference_graphify.add_argument("--model")
    reference_graphify.add_argument("--allow-remote", action="store_true")
    reference_graphify.add_argument("--timeout-seconds", type=int, default=3_600)
    reference_graphify.add_argument("--max-concurrency", type=int, default=1)
    reference_graphify.add_argument("--json", action="store_true")

    serve = subcommands.add_parser("serve", help="Start the local interactive dashboard")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--root", help="Repository to analyze when the dashboard starts")
    serve.add_argument("--graph", help="Load an existing canonical graph JSON")
    serve.add_argument("--include-root", action="append", default=[])
    serve.add_argument("--max-work", type=int)
    serve.add_argument("--no-browser", action="store_true")
    return parser


def run(arguments: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(arguments)
    if args.command == "reference":
        try:
            if args.reference_operation == "build":
                result = build_reference_corpus(
                    BuildRequest(
                        input_dir=Path(args.input_dir),
                        output_dir=Path(args.output),
                        sources_path=Path(args.sources) if args.sources else None,
                        max_pdf_bytes=args.max_pdf_bytes,
                        max_pages_per_source=args.max_pages_per_source,
                        max_pages_per_section=args.max_pages_per_section,
                    )
                )
                human = (
                    f"Built reference corpus {result['corpus_fingerprint'][:12]}: "
                    f"{result['counts']['documents']} documents, "
                    f"{result['counts']['pages']} pages, "
                    f"{result['counts']['sections']} sections"
                )
            elif args.reference_operation == "graphify":
                may_leave_machine = args.processing_boundary == "remote"
                print(
                    "reference graphify: "
                    f"processing_boundary={args.processing_boundary} "
                    f"backend={args.backend} "
                    f"corpus_content_may_leave_machine={str(may_leave_machine).lower()}",
                    file=sys.stderr,
                )
                result = build_graphify_overlay(
                    GraphifyRequest(
                        corpus_root=Path(args.corpus_root),
                        output_dir=Path(args.output),
                        executable=args.graphify,
                        backend=args.backend,
                        processing_boundary=args.processing_boundary,
                        model=args.model,
                        allow_remote=args.allow_remote,
                        timeout_seconds=args.timeout_seconds,
                        max_concurrency=args.max_concurrency,
                    )
                )
                human = (
                    f"Built Graphify overlay {result['overlay_fingerprint'][:12]} "
                    f"for corpus {result['corpus_fingerprint'][:12]} "
                    f"({result['processing_boundary']})"
                )
            else:
                corpus = ReferenceCorpus.open(args.corpus_root)
                if args.reference_operation == "status":
                    result = corpus.status()
                    human = (
                        f"Reference corpus {result['corpus_fingerprint'][:12]}: "
                        f"{result['counts']['documents']} documents, "
                        f"{result['counts']['pages']} pages, "
                        f"{result['counts']['sections']} sections"
                    )
                elif args.reference_operation == "search":
                    result = corpus.search(
                        args.query,
                        limit=args.limit,
                        max_excerpt_chars=args.max_excerpt_chars,
                    )
                    human = "\n".join(
                        f"{item['source']['title']} "
                        f"p.{item['citation']['physical_page_start']}"
                        f"–{item['citation']['physical_page_end']}: "
                        f"{item['section']['title']}"
                        for item in result["results"]
                    ) or "No reference matches"
                else:
                    result = corpus.excerpt(
                        args.section_id,
                        start=args.start,
                        max_chars=args.max_chars,
                    )
                    human = result["excerpt"]
        except ReferenceError as error:
            _emit_error(error.to_dict(), args.json)
            return 1
        _emit(result, args.json, human)
        return 0
    if args.command == "serve":
        try:
            AnalysisBudget(args.max_work)
        except ValueError as error:
            _emit_error(
                {
                    "code": "invalid_parameter",
                    "message": str(error),
                    "field": "max_work",
                },
                False,
            )
            return 1
        from .web import serve_dashboard

        serve_dashboard(
            host=args.host, port=args.port, root=args.root, graph_path=args.graph,
            include_roots=args.include_root, max_work=args.max_work,
            open_browser=not args.no_browser,
        )
        return 0
    if args.command == "analyze":
        try:
            AnalysisBudget(args.max_work)
        except ValueError as error:
            _emit_error(
                {
                    "code": "invalid_parameter",
                    "message": str(error),
                    "field": "max_work",
                },
                args.json,
            )
            return 1
        try:
            graph = analyze_repository(
                args.root,
                args.include_root,
                args.exclude,
                max_work=args.max_work,
            )
        except AnalysisBudgetExceeded as error:
            _emit_error(error.to_dict(), args.json)
            return 1
        graph.save(args.output)
        summary = {
            "output": str(Path(args.output).resolve()),
            "files": graph.metadata["file_count"],
            "nodes": len(graph.nodes), "edges": len(graph.edges),
            "diagnostics": len(graph.diagnostics),
            "source_fingerprint": graph.metadata["source_fingerprint"],
        }
        _emit(summary, args.json,
              f"Indexed {summary['files']} files: {summary['nodes']} nodes, "
              f"{summary['edges']} edges, {summary['diagnostics']} diagnostics -> {args.output}")
        return 0

    if args.command == "compiler-evidence":
        try:
            graph = CodeGraph.load(args.graph)
            root = graph.metadata.get("root")
            if not isinstance(root, str) or not root:
                raise CompilerEvidenceError(
                    "compiler_correlation_failed",
                    "Graph is missing the project root required for compiler correlation",
                )
            report = correlate_compiler_log(
                graph,
                root,
                args.log,
                args.entry,
                excluded=args.exclude,
            )
            result = correlation_result(
                report,
                GraphIdentity(
                    graph.schema_version,
                    graph.metadata.get("source_fingerprint"),
                ),
            )
        except CompilerEvidenceError as error:
            _emit_error({"code": error.code, "message": error.message}, args.json)
            return 1
        except (OSError, ValueError, json.JSONDecodeError):
            _emit_error(
                {
                    "code": "compiler_correlation_failed",
                    "message": "Compiler evidence correlation failed",
                },
                args.json,
            )
            return 1
        _emit(
            result,
            args.json,
            f"Compiler evidence is {report.evidence_state}: {report.outcome}",
        )
        return 0

    if args.command == "intelligence":
        graph = CodeGraph.load(args.graph)
        requested_version = (
            "1.0.0" if args.contract_version == "1" else args.contract_version
        )
        if args.intelligence_operation == "diagnostics":
            targets = []
        elif args.intelligence_operation == "path":
            targets = [
                {"value": args.source, "kind": None},
                {"value": args.target, "kind": None},
            ]
        else:
            targets = [{"value": args.target, "kind": None}]
        try:
            request = {
                "contract_version": requested_version,
                "operation": args.intelligence_operation,
                "targets": targets,
                "direction": args.direction,
                "relationship_types": sorted(set(args.relationship_type)),
                "node_kinds": sorted(set(getattr(args, "node_kind", []))),
                "bounds": {
                    "max_depth": args.max_depth,
                    "max_items": getattr(args, "max_items", 30),
                    "max_paths": getattr(args, "max_paths", 3),
                    "max_expansions": getattr(args, "max_expansions", 10_000),
                    "context_units": getattr(args, "context_units", 100),
                },
                "expected_source_fingerprint": None,
                "client_request_id": None,
            }
            result = IntelligenceKernel(graph).execute(request)
        except (ValueError, IntelligenceError) as error:
            normalized = (
                error
                if isinstance(error, IntelligenceError)
                else IntelligenceError.invalid_request(str(error))
            )
            payload = {"error": normalized.to_dict()}
            if args.json:
                print(
                    json.dumps(
                        payload, ensure_ascii=False, indent=2, sort_keys=True
                    ),
                    file=sys.stderr,
                )
            else:
                print(f"error: {normalized.message}", file=sys.stderr)
            return 1
        _emit(result.to_dict(), args.json, result.to_json().rstrip())
        return 0

    graph = CodeGraph.load(args.graph)
    if args.command == "status":
        severities: dict[str, int] = {}
        for diagnostic in graph.diagnostics:
            severities[diagnostic.severity] = severities.get(diagnostic.severity, 0) + 1
        result = {
            "schema_version": graph.schema_version,
            "files": graph.metadata.get("file_count", 0),
            "nodes": len(graph.nodes), "edges": len(graph.edges),
            "diagnostics": severities,
            "source_fingerprint": graph.metadata.get("source_fingerprint"),
        }
        _emit(result, args.json,
              f"Schema {result['schema_version']}: {result['files']} files, "
              f"{result['nodes']} nodes, {result['edges']} edges")
        return 0

    if args.command == "query":
        nodes = [node.to_dict() for node in graph.find_nodes(args.text, args.kind)]
        _emit(nodes, args.json, "\n".join(f"{item['kind']}: {item['qualified_name']}" for item in nodes)
              or "No matches")
        return 0

    if args.command in {"context", "impact"}:
        seeds = _matches(graph, args.symbol)
        if not seeds:
            print(f"No symbol matches {args.symbol!r}", file=sys.stderr)
            return 2
        if args.command == "context":
            value = graph.neighborhood(seeds, max(0, args.depth))
            human = f"{len(value['nodes'])} nodes, {len(value['edges'])} edges"
        else:
            value = graph.upstream_impact(seeds, max(0, args.depth))
            human = "\n".join(
                f"d={item['distance']} {item['node']['kind']}: {item['node']['qualified_name']}"
                for item in value
            ) or "No upstream impact found"
        _emit(value, args.json, human)
        return 0

    if args.command == "export":
        export_graphml(graph, args.output)
        value = {"format": args.format, "output": str(Path(args.output).resolve()),
                 "nodes": len(graph.nodes), "edges": len(graph.edges)}
        _emit(value, args.json, f"Exported {args.format} -> {args.output}")
        return 0
    return 2


def main() -> int:
    try:
        return run()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
