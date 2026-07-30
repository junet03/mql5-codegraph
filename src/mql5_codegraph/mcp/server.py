"""Official-SDK MCP stdio projection for MQL5 CodeGraph."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import json
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from .service import AdapterError, ProjectSession, ReferenceSession


SERVER_NAME = "mql5-codegraph-intelligence"
LIFECYCLE_PREFIX = "mql5-codegraph-mcp.lifecycle "
SERVER_INSTRUCTIONS = (
    "Local, read-only MQL5 project and reference intelligence. Call project_status "
    "and reference_status first. "
    "Call index_project only for a trusted absolute local project root, then "
    "use bounded intelligence tools. Call load_reference_corpus only for an "
    "operator-selected complete local corpus. Preserve ambiguity, evidence class, "
    "origin, completion, truncation, graph fingerprint, and corpus fingerprint in "
    "every claim. Re-index after source changes. This experimental server never "
    "edits source, builds corpora, writes indexes, invokes Graphify, or accesses "
    "the network."
)
READ_ONLY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def _distribution_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "source"
    except Exception:
        return "unknown"


def _emit_lifecycle(event: str, **details: object) -> None:
    payload = {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event,
        "server": SERVER_NAME,
        "transport": "stdio",
        "pid": os.getpid(),
        "parent_pid": os.getppid(),
        "package_version": _distribution_version("mql5-codegraph"),
        "mcp_sdk_version": _distribution_version("mcp"),
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        **details,
    }
    try:
        sys.stderr.write(
            LIFECYCLE_PREFIX
            + json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        sys.stderr.flush()
    except (OSError, ValueError):
        # Telemetry must never become a new failure mode for the MCP transport.
        pass


def _call(method, /, *args, **kwargs) -> dict[str, Any]:
    try:
        return method(*args, **kwargs)
    except AdapterError as error:
        raise ToolError(error.to_json()) from error


def create_server(
    session: ProjectSession | None = None,
    reference_session: ReferenceSession | None = None,
) -> FastMCP:
    """Create one MCP server bound to independent project/reference sessions."""

    project = session or ProjectSession()
    references = reference_session or ReferenceSession()
    server = FastMCP(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        log_level="ERROR",
    )

    @server.tool(
        name="project_status",
        description=(
            "Report the active in-memory MQL5 project snapshot without scanning "
            "or changing the filesystem."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def project_status() -> dict[str, Any]:
        return _call(project.project_status)

    @server.tool(
        name="reference_status",
        description=(
            "Report the active immutable reference-corpus snapshot without "
            "discovering, building, or changing local files."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def reference_status() -> dict[str, Any]:
        return _call(references.reference_status)

    @server.tool(
        name="load_reference_corpus",
        description=(
            "Attach an operator-selected complete absolute local reference corpus for "
            "bounded read-only evidence queries. This never builds or repairs it."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def load_reference_corpus(corpus_root: str) -> dict[str, Any]:
        return _call(references.load_reference_corpus, corpus_root)

    @server.tool(
        name="search_reference",
        description=(
            "Search deterministic page-cited reference-document evidence with "
            "authority and explicit completion metadata."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def search_reference(
        query: str,
        limit: int = 20,
        max_excerpt_chars: int = 1_200,
        expected_corpus_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            references.search_reference,
            query,
            limit=limit,
            max_excerpt_chars=max_excerpt_chars,
            expected_corpus_fingerprint=expected_corpus_fingerprint,
        )

    @server.tool(
        name="get_reference_excerpt",
        description=(
            "Return a bounded exact section excerpt with source hash, authority, "
            "physical PDF pages, and character bounds."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def get_reference_excerpt(
        section_id: str,
        start: int = 0,
        max_chars: int = 1_200,
        expected_corpus_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            references.get_reference_excerpt,
            section_id,
            start=start,
            max_chars=max_chars,
            expected_corpus_fingerprint=expected_corpus_fingerprint,
        )

    @server.tool(
        name="index_project",
        description=(
            "Read a trusted local MQL5 project into an in-memory graph snapshot. "
            "This does not modify source or persist an index."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def index_project(
        root: str,
        include_roots: list[str] | None = None,
        excluded: list[str] | None = None,
        max_work: int | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.index_project,
            root,
            include_roots or (),
            excluded or (),
            max_work=max_work,
        )

    @server.tool(
        name="correlate_compiler_log",
        description=(
            "Correlate an explicitly supplied bounded local MetaEditor compiler log "
            "with the active project snapshot without launching MetaEditor or writing files."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def correlate_compiler_log(
        log_path: str,
        entry_file: str,
    ) -> dict[str, Any]:
        return _call(project.correlate_compiler_log, log_path, entry_file)

    @server.tool(
        name="query_symbols",
        description=(
            "Resolve an MQL5 symbol while preserving exact, normalized, "
            "ambiguous, or no-match status."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def query_symbols(
        target: str,
        kind: str | None = None,
        max_items: int = 30,
        expected_source_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.query_symbols,
            target,
            kind=kind,
            max_items=max_items,
            expected_source_fingerprint=expected_source_fingerprint,
        )

    @server.tool(
        name="get_context",
        description=(
            "Return bounded incoming, outgoing, or bidirectional relationship "
            "context with evidence and completion metadata."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def get_context(
        target: str,
        direction: str = "both",
        relationship_types: list[str] | None = None,
        max_depth: int = 1,
        max_items: int = 900,
        expected_source_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.get_context,
            target,
            direction=direction,
            relationship_types=relationship_types,
            max_depth=max_depth,
            max_items=max_items,
            expected_source_fingerprint=expected_source_fingerprint,
        )

    @server.tool(
        name="get_impact",
        description=(
            "Return bounded upstream impact for a symbol with relationship "
            "evidence and truncation metadata."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def get_impact(
        target: str,
        relationship_types: list[str] | None = None,
        max_depth: int = 3,
        max_items: int = 2000,
        expected_source_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.get_impact,
            target,
            relationship_types=relationship_types,
            max_depth=max_depth,
            max_items=max_items,
            expected_source_fingerprint=expected_source_fingerprint,
        )

    @server.tool(
        name="find_paths",
        description=(
            "Find bounded directed paths between two MQL5 symbols with evidence "
            "for every hop and explicit incomplete-search reporting."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def find_paths(
        source: str,
        target: str,
        direction: str = "outgoing",
        relationship_types: list[str] | None = None,
        max_depth: int = 5,
        max_paths: int = 3,
        max_expansions: int = 10_000,
        expected_source_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.find_paths,
            source,
            target,
            direction=direction,
            relationship_types=relationship_types,
            max_depth=max_depth,
            max_paths=max_paths,
            max_expansions=max_expansions,
            expected_source_fingerprint=expected_source_fingerprint,
        )

    @server.tool(
        name="get_context_package",
        description=(
            "Build a deterministic bounded context package for AI review while "
            "preserving evidence, ambiguity, and omission reasons."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def get_context_package(
        target: str,
        direction: str = "both",
        relationship_types: list[str] | None = None,
        node_kinds: list[str] | None = None,
        max_depth: int = 2,
        max_expansions: int = 10_000,
        context_units: int = 100,
        expected_source_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.get_context_package,
            target,
            direction=direction,
            relationship_types=relationship_types,
            node_kinds=node_kinds,
            max_depth=max_depth,
            max_expansions=max_expansions,
            context_units=context_units,
            expected_source_fingerprint=expected_source_fingerprint,
        )

    @server.tool(
        name="get_diagnostics",
        description=(
            "Return bounded graph diagnostics from the active project snapshot."
        ),
        annotations=READ_ONLY_ANNOTATIONS,
        structured_output=True,
    )
    def get_diagnostics(
        max_items: int = 250,
        expected_source_fingerprint: str | None = None,
    ) -> dict[str, Any]:
        return _call(
            project.get_diagnostics,
            max_items=max_items,
            expected_source_fingerprint=expected_source_fingerprint,
        )

    return server


def main() -> None:
    """Run the bundled local server over MCP stdio."""

    _emit_lifecycle("starting")
    try:
        create_server().run(transport="stdio")
    except KeyboardInterrupt:
        _emit_lifecycle(
            "stopped",
            reason="keyboard_interrupt",
            exit_code=130,
        )
        raise
    except SystemExit as error:
        exit_code = error.code if isinstance(error.code, int) else 1
        _emit_lifecycle(
            "stopped" if exit_code == 0 else "crashed",
            reason="system_exit",
            exit_code=exit_code,
        )
        raise
    except BaseException as error:
        _emit_lifecycle(
            "crashed",
            reason="unhandled_exception",
            exception_type=type(error).__name__,
            exit_code=1,
        )
        raise
    else:
        _emit_lifecycle(
            "stopped",
            reason="stdio_eof",
            exit_code=0,
        )


if __name__ == "__main__":
    main()
