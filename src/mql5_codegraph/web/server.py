"""Loopback HTTP server for the local MQL5 CodeGraph dashboard."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
import json
import mimetypes
from pathlib import Path
import socket
from threading import BoundedSemaphore, Timer
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse
import webbrowser

from ..analysis_budget import AnalysisBudget
from ..graph import CodeGraph
from ..intelligence import IntelligenceError
from ..version import __version__
from .api import ApiError, DashboardApi
from .state import DashboardState

MAX_BODY_BYTES = 64 * 1024


class DashboardThreadingHTTPServer(ThreadingHTTPServer):
    """Loopback server with a finite listener queue and request-thread budget."""

    request_queue_size = 64
    max_request_threads = 32
    request_read_timeout_seconds = 2.0
    request_read_deadline_seconds = 10.0
    daemon_threads = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.max_request_threads = type(self).max_request_threads
        self.request_read_timeout_seconds = type(self).request_read_timeout_seconds
        self.request_read_deadline_seconds = type(self).request_read_deadline_seconds
        self._request_slots = BoundedSemaphore(self.max_request_threads)
        super().__init__(*args, **kwargs)

    def process_request(self, request: Any, client_address: Any) -> None:
        self._request_slots.acquire()
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._request_slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    server_version = f"MQL5CodeGraph/{__version__}"

    def __init__(self, *args: Any, api: DashboardApi, static_root: Path, **kwargs: Any) -> None:
        self.api = api
        self.static_root = static_root.resolve()
        super().__init__(*args, directory=str(self.static_root), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def handle_one_request(self) -> None:
        self.connection.settimeout(self.server.request_read_timeout_seconds)
        self._request_read_timer = Timer(
            self.server.request_read_deadline_seconds,
            self._expire_request_read,
        )
        self._request_read_timer.daemon = True
        self._request_read_timer.start()
        try:
            super().handle_one_request()
        except (ConnectionError, OSError):
            self.close_connection = True
        finally:
            self._finish_request_read()

    def _expire_request_read(self) -> None:
        try:
            self.connection.shutdown(socket.SHUT_RD)
        except OSError:
            pass

    def _finish_request_read(self) -> None:
        timer = getattr(self, "_request_read_timer", None)
        if timer is not None:
            timer.cancel()
            self._request_read_timer = None
        self.connection.settimeout(None)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                         "img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; "
                         "base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def _json(self, status: int, value: object) -> None:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _dispatch_error(self, error: Exception) -> None:
        if isinstance(error, IntelligenceError):
            statuses = {
                "invalid_request": 400,
                "invalid_parameter": 400,
                "missing_target": 400,
                "unsupported_operation": 409,
                "unsupported_contract_version": 409,
                "unsupported_graph_schema": 409,
                "graph_not_ready": 409,
                "graph_identity_mismatch": 409,
                "graph_integrity_error": 422,
            }
            self._json(
                statuses.get(error.code, 500),
                {"error": error.to_dict()},
            )
        elif isinstance(error, ApiError):
            self._json(error.status, error.to_dict())
        else:
            self._json(500, {"error": {"code": "internal_error", "message": "Unexpected server error"}})

    def _validate_request_origin(self) -> None:
        host = self.headers.get("Host")
        if host is None:
            raise ApiError(400, "host_required", "Host header is required")
        try:
            parsed_host = urlparse(f"//{host}")
            host_port = parsed_host.port
        except ValueError as error:
            raise ApiError(400, "invalid_host", "Host header is invalid") from error
        if not parsed_host.hostname or not _is_loopback_host(parsed_host.hostname):
            self.close_connection = True
            raise ApiError(421, "host_not_allowed", "Dashboard requests must target loopback")
        if host_port is not None and host_port != self.server.server_port:
            self.close_connection = True
            raise ApiError(421, "host_not_allowed", "Host port does not match the dashboard")

        origin = self.headers.get("Origin")
        if origin is None:
            return
        try:
            parsed_origin = urlparse(origin)
            origin_port = parsed_origin.port or 80
        except ValueError as error:
            raise ApiError(403, "origin_not_allowed", "Origin header is invalid") from error
        if (
            parsed_origin.scheme != "http"
            or not parsed_origin.hostname
            or not _is_loopback_host(parsed_origin.hostname)
            or origin_port != self.server.server_port
        ):
            self.close_connection = True
            raise ApiError(403, "origin_not_allowed", "Cross-origin dashboard requests are denied")

    def do_GET(self) -> None:
        self._finish_request_read()
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query, keep_blank_values=True)
        try:
            self._validate_request_origin()
            if parsed.path == "/api/health":
                return self._json(200, self.api.health())
            if parsed.path == "/api/status":
                return self._json(200, self.api.status())
            if parsed.path.startswith("/api/jobs/"):
                return self._json(200, self.api.job(unquote(parsed.path.removeprefix("/api/jobs/"))))
            if parsed.path == "/api/graph":
                return self._json(200, self.api.graph(params))
            if parsed.path == "/api/query":
                return self._json(200, self.api.query(params))
            if parsed.path == "/api/context":
                return self._json(200, self.api.context(params))
            if parsed.path == "/api/impact":
                return self._json(200, self.api.impact(params))
            if parsed.path == "/api/diagnostics":
                return self._json(200, self.api.diagnostics(params))
            if parsed.path == "/api/source":
                return self._json(200, self.api.source(params))
            if parsed.path.startswith("/api/"):
                raise ApiError(404, "endpoint_not_found", "API endpoint was not found")
            return self._serve_static(parsed.path)
        except Exception as error:
            self._dispatch_error(error)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            self._validate_request_origin()
            intelligence_prefix = "/api/v1/intelligence/"
            is_intelligence = parsed.path.startswith(intelligence_prefix)
            if parsed.path != "/api/analyze" and not is_intelligence:
                raise ApiError(404, "endpoint_not_found", "API endpoint was not found")
            length_value = self.headers.get("Content-Length")
            if length_value is None:
                raise ApiError(411, "length_required", "Content-Length is required")
            try:
                length = int(length_value)
            except ValueError as error:
                raise ApiError(400, "invalid_length", "Content-Length must be an integer") from error
            if length < 0 or length > MAX_BODY_BYTES:
                raise ApiError(413, "body_too_large", "Request body exceeds 64 KiB")
            try:
                raw_body = self.rfile.read(length)
            finally:
                self._finish_request_read()
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ApiError(400, "invalid_json", "Request body must contain valid UTF-8 JSON") from error
            if parsed.path == "/api/analyze":
                status, response = self.api.analyze(payload)
                return self._json(status, response)
            route_operation = parsed.path.removeprefix(intelligence_prefix)
            operations = {
                "query": "query",
                "context": "context",
                "impact": "impact",
                "diagnostics": "diagnostics",
                "path": "path",
                "context-package": "context_package",
            }
            operation = operations.get(route_operation)
            if operation is None:
                raise ApiError(404, "endpoint_not_found", "API endpoint was not found")
            self._json(200, self.api.intelligence(operation, payload))
        except TimeoutError:
            raise
        except Exception as error:
            self._dispatch_error(error)

    def _serve_static(self, request_path: str) -> None:
        relative = unquote(request_path).lstrip("/") or "index.html"
        candidate = (self.static_root / relative).resolve()
        try:
            candidate.relative_to(self.static_root)
        except ValueError:
            candidate = self.static_root / "index.html"
        if not candidate.is_file():
            candidate = self.static_root / "index.html"
        if not candidate.is_file():
            raise ApiError(503, "frontend_missing", "Dashboard frontend is not built")
        payload = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache" if candidate.name == "index.html" else "public, max-age=31536000, immutable")
        self.end_headers()
        self.wfile.write(payload)


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().strip("[]").casefold()
    if normalized == "localhost":
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def create_server(
    state: DashboardState, host: str = "127.0.0.1", port: int = 0,
    static_root: str | Path | None = None,
) -> ThreadingHTTPServer:
    if not _is_loopback_host(host):
        raise ValueError("Dashboard host must be a loopback address")
    root = Path(static_root) if static_root else Path(__file__).resolve().parent.parent / "web_static"
    api = DashboardApi(state)
    handler = partial(DashboardRequestHandler, api=api, static_root=root)
    return DashboardThreadingHTTPServer((host, port), handler)


def serve_dashboard(
    host: str = "127.0.0.1", port: int = 8765, root: str | Path | None = None,
    graph_path: str | Path | None = None, include_roots: list[str] | None = None,
    max_work: int | None = None,
    open_browser: bool = True,
) -> None:
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    AnalysisBudget(max_work)
    state = DashboardState()
    if graph_path:
        graph = CodeGraph.load(graph_path)
        state.load_graph(graph, root)
    if root and not graph_path:
        state.start_analysis(root, include_roots or [], max_work=max_work)
    server = create_server(state, host, port)
    actual_host, actual_port = server.server_address[:2]
    display_host = f"[{actual_host}]" if ":" in actual_host else actual_host
    url = f"http://{display_host}:{actual_port}/"
    print(f"MQL5 CodeGraph dashboard: {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("Stopping dashboard")
    finally:
        server.server_close()
