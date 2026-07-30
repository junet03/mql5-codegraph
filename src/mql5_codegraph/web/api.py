"""Pure local-dashboard API operations shared by HTTP handlers and tests."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..analysis_budget import AnalysisBudget
from ..intelligence import IntelligenceError
from ..version import __version__
from .state import DashboardState


_PATH_BOUNDS_DEFAULTS = {
    "max_depth": 5,
    "max_items": 30,
    "max_paths": 3,
    "max_expansions": 10_000,
    "context_units": 100,
}

_CONTEXT_PACKAGE_BOUNDS_DEFAULTS = {
    "max_depth": 2,
    "max_items": 30,
    "max_paths": 3,
    "max_expansions": 10_000,
    "context_units": 100,
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, object]:
        return {"error": {"code": self.code, "message": self.message}}


def _single(params: Mapping[str, Sequence[str]], name: str, default: str | None = None) -> str | None:
    values = params.get(name)
    return values[-1] if values else default


def _bounded_int(value: str | None, default: int, minimum: int, maximum: int, name: str) -> int:
    try:
        parsed = default if value is None else int(value)
    except ValueError as error:
        raise ApiError(400, "invalid_parameter", f"{name} must be an integer") from error
    if not minimum <= parsed <= maximum:
        raise ApiError(400, "invalid_parameter", f"{name} must be between {minimum} and {maximum}")
    return parsed


def _normalize_path_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body.setdefault("direction", "outgoing")
    if "bounds" not in body:
        supplied_bounds: Mapping[str, Any] = {}
    elif not isinstance(body["bounds"], Mapping):
        raise IntelligenceError.invalid_parameter(
            "bounds", "must be an object"
        )
    else:
        supplied_bounds = body["bounds"]
    body["bounds"] = {**_PATH_BOUNDS_DEFAULTS, **dict(supplied_bounds)}
    return body


def _normalize_context_package_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    body = dict(payload)
    body.setdefault("direction", "both")
    if "bounds" not in body:
        supplied_bounds: Mapping[str, Any] = {}
    elif not isinstance(body["bounds"], Mapping):
        raise IntelligenceError.invalid_parameter(
            "bounds", "must be an object"
        )
    else:
        supplied_bounds = body["bounds"]
    body["bounds"] = {
        **_CONTEXT_PACKAGE_BOUNDS_DEFAULTS,
        **dict(supplied_bounds),
    }
    return body


class DashboardApi:
    def __init__(self, state: DashboardState) -> None:
        self.state = state

    def health(self) -> dict[str, object]:
        status = self.state.status()
        return {
            "service": "mql5-codegraph", "version": __version__, "ok": True,
            "ready": status["ready"], "graph_version": status["graph_version"],
            "active_job_id": (status["active_job"] or {}).get("id") if status["active_job"] else None,
        }

    def status(self) -> dict[str, object]:
        return self.state.status()

    def analyze(self, payload: Any) -> tuple[int, dict[str, object]]:
        if not isinstance(payload, dict):
            raise ApiError(400, "invalid_body", "Request body must be a JSON object")
        root = payload.get("root")
        include_roots = payload.get("include_roots", [])
        max_work = payload.get("max_work")
        if not isinstance(root, str) or not root.strip():
            raise ApiError(400, "invalid_root", "root must be a non-empty directory path")
        if not isinstance(include_roots, list) or not all(isinstance(path, str) for path in include_roots):
            raise ApiError(400, "invalid_include_roots", "include_roots must be an array of paths")
        try:
            AnalysisBudget(max_work)
        except ValueError as error:
            raise ApiError(400, "invalid_max_work", str(error)) from error
        try:
            job = self.state.start_analysis(
                root.strip(),
                include_roots,
                max_work=max_work,
            )
        except ValueError as error:
            raise ApiError(400, "invalid_root", str(error)) from error
        except RuntimeError as error:
            raise ApiError(409, "analysis_running", str(error)) from error
        return 202, {"job": job.to_dict()}

    def job(self, job_id: str) -> dict[str, object]:
        job = self.state.get_job(job_id)
        if job is None:
            raise ApiError(404, "job_not_found", f"Analysis job {job_id!r} was not found")
        return {"job": job.to_dict()}

    def _graph(self):
        graph, _, root, version = self.state.intelligence_snapshot()
        if graph is None:
            raise ApiError(409, "graph_not_ready", "Analyze a repository before using this endpoint")
        return graph, root, version

    def _graph_and_kernel(self):
        graph, kernel, root, version = self.state.intelligence_snapshot()
        if graph is None or kernel is None:
            raise ApiError(
                409,
                "graph_not_ready",
                "Analyze a repository before using this endpoint",
            )
        return graph, kernel, root, version

    def graph(self, params: Mapping[str, Sequence[str]]) -> dict[str, object]:
        graph, _, version = self._graph()
        limit = _bounded_int(_single(params, "limit"), 900, 1, 2000, "limit")
        kinds = set(params.get("kind", []))
        relationships = set(params.get("relationship", []))
        query = (_single(params, "q", "") or "").casefold().strip()
        candidates = sorted(graph.nodes.values(), key=lambda node: (node.kind, node.qualified_name.casefold(), node.id))
        if kinds:
            candidates = [node for node in candidates if node.kind in kinds]
        if query:
            candidates = [node for node in candidates
                          if query in node.name.casefold() or query in node.qualified_name.casefold()]
        selected = candidates[:limit]
        selected_ids = {node.id for node in selected}
        edges = [edge for edge in sorted(graph.edges.values(), key=lambda edge: edge.id)
                 if edge.source in selected_ids and edge.target in selected_ids
                 and (not relationships or edge.relationship in relationships)]
        return {
            "version": version,
            "nodes": [node.to_dict() for node in selected],
            "edges": [edge.to_dict() for edge in edges],
            "total_nodes": len(graph.nodes), "total_edges": len(graph.edges),
            "visible_nodes": len(selected), "visible_edges": len(edges),
            "truncated": len(candidates) > limit,
            "filters": {"kinds": sorted(kinds), "relationships": sorted(relationships),
                        "q": query, "limit": limit},
            "available_kinds": dict(sorted(Counter(node.kind for node in graph.nodes.values()).items())),
            "available_relationships": dict(sorted(Counter(edge.relationship for edge in graph.edges.values()).items())),
        }

    def query(self, params: Mapping[str, Sequence[str]]) -> dict[str, object]:
        _, kernel, _, version = self._graph_and_kernel()
        query = (_single(params, "q", "") or "").strip()
        if not query:
            raise ApiError(400, "missing_query", "q is required")
        kind = _single(params, "kind")
        limit = _bounded_int(_single(params, "limit"), 30, 1, 100, "limit")
        matches = kernel.legacy_find_nodes(query, kind)[:limit]
        return {"version": version, "query": query, "results": [node.to_dict() for node in matches]}

    def context(self, params: Mapping[str, Sequence[str]]) -> dict[str, object]:
        graph, kernel, _, version = self._graph_and_kernel()
        symbol = (_single(params, "symbol", "") or "").strip()
        if not symbol:
            raise ApiError(400, "missing_symbol", "symbol is required")
        depth = _bounded_int(_single(params, "depth"), 1, 0, 5, "depth")
        seeds = self._resolve_symbols(graph, symbol)
        return {"version": version, "symbol": symbol, "depth": depth,
                **kernel.legacy_neighborhood(seeds, depth)}

    def impact(self, params: Mapping[str, Sequence[str]]) -> dict[str, object]:
        graph, kernel, _, version = self._graph_and_kernel()
        symbol = (_single(params, "symbol", "") or "").strip()
        if not symbol:
            raise ApiError(400, "missing_symbol", "symbol is required")
        depth = _bounded_int(_single(params, "depth"), 3, 0, 5, "depth")
        seeds = self._resolve_symbols(graph, symbol)
        return {"version": version, "symbol": symbol, "depth": depth,
                "results": kernel.legacy_upstream_impact(seeds, depth)}

    @staticmethod
    def _resolve_symbols(graph, symbol: str) -> list[str]:
        exact = [node.id for node in graph.nodes.values()
                 if node.id == symbol or node.name.casefold() == symbol.casefold()
                 or node.qualified_name.casefold() == symbol.casefold()]
        matches = exact or [node.id for node in graph.find_nodes(symbol)]
        if not matches:
            raise ApiError(404, "symbol_not_found", f"No symbol matches {symbol!r}")
        return sorted(matches)

    def diagnostics(self, params: Mapping[str, Sequence[str]]) -> dict[str, object]:
        graph, kernel, _, version = self._graph_and_kernel()
        severity = _single(params, "severity")
        code = _single(params, "code")
        limit = _bounded_int(_single(params, "limit"), 250, 1, 1000, "limit")
        all_items = list(kernel.index.diagnostics)
        filtered = [item for item in all_items
                    if (not severity or item.severity == severity) and (not code or item.code == code)]
        return {
            "version": version, "total": len(all_items), "matched": len(filtered),
            "truncated": len(filtered) > limit,
            "items": [item.to_dict() for item in filtered[:limit]],
            "by_severity": dict(sorted(Counter(item.severity for item in all_items).items())),
            "by_code": dict(sorted(Counter(item.code for item in all_items).items())),
        }

    def intelligence(self, operation: str, payload: Any) -> dict[str, object]:
        if not isinstance(payload, dict):
            raise IntelligenceError.invalid_request(
                "Intelligence request must be an object"
            )
        graph, kernel, _, _ = self.state.intelligence_snapshot()
        if graph is None or kernel is None:
            raise IntelligenceError(
                "state",
                "graph_not_ready",
                "Analyze a repository before using this endpoint",
                retryable=True,
            )
        body = dict(payload)
        supplied_operation = body.get("operation")
        if supplied_operation is not None and supplied_operation != operation:
            raise IntelligenceError.invalid_request(
                "Request operation does not match the route"
            )
        if operation == "path":
            body = _normalize_path_payload(body)
        elif operation == "context_package":
            body = _normalize_context_package_payload(body)
        body["operation"] = operation
        return kernel.execute(body).to_dict()

    def source(self, params: Mapping[str, Sequence[str]]) -> dict[str, object]:
        _, root, version = self._graph()
        if root is None:
            raise ApiError(409, "root_not_ready", "Active repository root is unavailable")
        relative = (_single(params, "file", "") or "").strip().replace("\\", "/")
        if not relative:
            raise ApiError(400, "missing_file", "file is required")
        line = _bounded_int(_single(params, "line"), 1, 1, 10_000_000, "line")
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError as error:
            raise ApiError(403, "source_outside_root", "Source path is outside the active repository") from error
        if candidate.suffix.lower() not in {".mq5", ".mqh"}:
            raise ApiError(403, "source_type_denied", "Only .mq5 and .mqh source files may be read")
        if not candidate.is_file():
            raise ApiError(404, "source_not_found", f"Source file {relative!r} was not found")
        size = candidate.stat().st_size
        if size > 2 * 1024 * 1024:
            raise ApiError(413, "source_too_large", "Source file exceeds the 2 MiB viewer limit")
        text = candidate.read_text(encoding="utf-8-sig", errors="replace")
        return {"version": version, "file": candidate.relative_to(root).as_posix(),
                "content": text, "line_count": text.count("\n") + 1,
                "highlight_line": min(line, text.count("\n") + 1), "language": "mql5"}
