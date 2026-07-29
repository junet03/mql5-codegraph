from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from hashlib import sha256
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from threading import Barrier, Event, Lock, Thread
from time import monotonic, sleep
from unittest import TestCase
from unittest.mock import patch

from mql5_codegraph.graph import SourceLocation
from mql5_codegraph.indexer import analyze_repository
from mql5_codegraph.intelligence import IntelligenceError
from mql5_codegraph.intelligence import paths as path_module
from mql5_codegraph.web.api import ApiError, DashboardApi
from mql5_codegraph.web.server import (
    DashboardThreadingHTTPServer,
    create_server,
    serve_dashboard,
)
from mql5_codegraph.web.state import DashboardState
from tests.intelligence.helpers import build_graph, make_edge, make_node


FIXTURE = Path(__file__).parent / "fixtures" / "basic_ea"


def ready_state() -> DashboardState:
    state = DashboardState()
    job = state.start_analysis(FIXTURE)
    deadline = monotonic() + 3
    while monotonic() < deadline:
        current = state.get_job(job.id)
        if current and current.status == "completed":
            return state
        sleep(0.01)
    raise AssertionError("fixture analysis timed out")


class DashboardApiTests(TestCase):
    def setUp(self) -> None:
        self.state = ready_state()
        self.api = DashboardApi(self.state)

    def test_health_status_and_bounded_projection(self) -> None:
        self.assertTrue(self.api.health()["ready"])
        projection = self.api.graph({"limit": ["5"]})
        self.assertLessEqual(projection["visible_nodes"], 5)
        self.assertEqual(16, projection["total_nodes"])
        self.assertIn("event_handler", projection["available_kinds"])

    def test_query_context_and_impact_contracts(self) -> None:
        query = self.api.query({"q": ["CalculateLots"]})
        self.assertEqual("CRiskManager::CalculateLots", query["results"][0]["qualified_name"])
        node_id = query["results"][0]["id"]
        context = self.api.context({"symbol": [node_id], "depth": ["1"]})
        self.assertTrue(context["nodes"])
        impact = self.api.impact({"symbol": [node_id], "depth": ["3"]})
        self.assertTrue(any(item["node"]["name"] == "OnTick" for item in impact["results"]))

    def test_diagnostics_and_safe_source_evidence(self) -> None:
        diagnostics = self.api.diagnostics({"severity": ["warning"]})
        self.assertGreaterEqual(diagnostics["matched"], 1)
        source = self.api.source({"file": ["BasicEA.mq5"], "line": ["12"]})
        self.assertIn("void OnTick", source["content"])
        self.assertEqual(12, source["highlight_line"])
        with self.assertRaises(ApiError) as outside:
            self.api.source({"file": ["../outside.mq5"]})
        self.assertEqual(403, outside.exception.status)
        with self.assertRaises(ApiError) as denied:
            self.api.source({"file": ["BasicEA.txt"]})
        self.assertIn(denied.exception.status, {403, 404})

    def test_saved_graph_without_explicit_root_disables_source_viewer(self) -> None:
        graph, _, _ = self.state.snapshot()
        state = DashboardState()
        state.load_graph(graph)

        with self.assertRaises(ApiError) as unavailable:
            DashboardApi(state).source({"file": ["BasicEA.mq5"]})

        self.assertEqual(409, unavailable.exception.status)
        self.assertEqual("root_not_ready", unavailable.exception.code)

    def test_invalid_parameters_are_structured_errors(self) -> None:
        with self.assertRaises(ApiError) as missing:
            self.api.query({})
        self.assertEqual("missing_query", missing.exception.code)
        with self.assertRaises(ApiError) as depth:
            self.api.context({"symbol": ["OnTick"], "depth": ["99"]})
        self.assertEqual("invalid_parameter", depth.exception.code)

    def test_analyze_rejects_invalid_work_budget(self) -> None:
        with self.assertRaises(ApiError) as raised:
            self.api.analyze({"root": str(FIXTURE), "max_work": 0})

        self.assertEqual(400, raised.exception.status)
        self.assertEqual("invalid_max_work", raised.exception.code)

    def test_normalized_path_projects_defaults_and_evidence(self) -> None:
        source = make_node("OnTick", node_id="node:on-tick")
        target = make_node("CalculateLots", node_id="node:calculate-lots")
        edge = make_edge(
            source,
            target,
            edge_id="edge:on-tick-calculate-lots",
            origin="runtime",
            confidence=0.8,
            location=SourceLocation("Expert.mq5", 12, 5),
        )
        graph = build_graph([target, source], [edge])
        state = DashboardState()
        state.load_graph(graph, Path.cwd())

        payload = DashboardApi(state).intelligence(
            "path",
            {
                "contract_version": "1.0.0",
                "targets": [
                    {"value": source.id, "kind": None},
                    {"value": target.id, "kind": None},
                ],
            },
        )

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
        self.assertEqual("runtime", hop["evidence"]["origin"])
        self.assertEqual(0.8, hop["evidence"]["confidence"])
        self.assertEqual(
            {"file": "Expert.mq5", "line": 12, "column": 5},
            hop["evidence"]["location"],
        )

    def test_normalized_path_preserves_stable_validation_errors(self) -> None:
        graph = build_graph([make_node("Source"), make_node("Target")])
        state = DashboardState()
        state.load_graph(graph, Path.cwd())
        api = DashboardApi(state)
        base = {
            "contract_version": "1.0.0",
            "targets": [
                {"value": "Source", "kind": None},
                {"value": "Target", "kind": None},
            ],
        }
        cases = (
            (
                {**base, "contract_version": "2.0.0"},
                "unsupported_contract_version",
                "contract_version",
            ),
            (
                {**base, "bounds": {"max_paths": 0}},
                "invalid_parameter",
                "bounds.max_paths",
            ),
            (
                {**base, "bounds": []},
                "invalid_parameter",
                "bounds",
            ),
            (
                {**base, "operation": "query"},
                "invalid_request",
                None,
            ),
        )

        for request, code, field in cases:
            with self.subTest(code=code, field=field):
                with self.assertRaises(IntelligenceError) as raised:
                    api.intelligence("path", request)
                self.assertEqual(code, raised.exception.code)
                self.assertEqual(field, raised.exception.field)


class DashboardHttpTests(TestCase):
    def test_dashboard_startup_rejects_an_invalid_work_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_work must be an integer"):
            serve_dashboard(max_work=0, open_browser=False)

    def test_server_rejects_non_loopback_bind_and_request_authorities(self) -> None:
        state = DashboardState()
        with self.assertRaisesRegex(ValueError, "loopback"):
            create_server(state, host="0.0.0.0", port=0)

        server = create_server(state, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def get(headers: dict[str, str]) -> tuple[int, dict[str, object]]:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
            connection.putrequest("GET", "/api/health", skip_host=True)
            for name, value in headers.items():
                connection.putheader(name, value)
            connection.endheaders()
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
            connection.close()
            return result

        try:
            status, payload = get({"Host": "example.test"})
            self.assertEqual(421, status)
            self.assertEqual("host_not_allowed", payload["error"]["code"])

            status, payload = get({
                "Host": f"127.0.0.1:{server.server_port}",
                "Origin": "https://example.test",
            })
            self.assertEqual(403, status)
            self.assertEqual("origin_not_allowed", payload["error"]["code"])

            status, payload = get({
                "Host": f"127.0.0.1:{server.server_port}",
                "Origin": f"http://127.0.0.1:{server.server_port}",
            })
            self.assertEqual(200, status)
            self.assertTrue(payload["ok"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_health_static_and_malformed_json(self) -> None:
        state = ready_state()
        with TemporaryDirectory() as directory:
            static_root = Path(directory)
            (static_root / "index.html").write_text("<!doctype html><title>dashboard</title>", encoding="utf-8")
            server = create_server(state, port=0, static_root=static_root)
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                connection.request("GET", "/api/health")
                response = connection.getresponse()
                payload = json.loads(response.read())
                self.assertEqual(200, response.status)
                self.assertTrue(payload["ok"])
                self.assertEqual("nosniff", response.getheader("X-Content-Type-Options"))

                connection.request("GET", "/does-not-exist")
                response = connection.getresponse()
                self.assertEqual(200, response.status)
                self.assertIn(b"dashboard", response.read())

                connection.request("POST", "/api/analyze", body=b"{bad",
                                   headers={"Content-Type": "application/json", "Content-Length": "4"})
                response = connection.getresponse()
                payload = json.loads(response.read())
                self.assertEqual(400, response.status)
                self.assertEqual("invalid_json", payload["error"]["code"])
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_concurrent_path_requests_share_one_distance_build(self) -> None:
        source = make_node("Source", node_id="node:source")
        middle = make_node("Middle", node_id="node:middle")
        target = make_node("Target", node_id="node:target")
        state = DashboardState()
        state.load_graph(
            build_graph(
                [source, middle, target],
                (
                    make_edge(source, middle, edge_id="edge:source-middle"),
                    make_edge(middle, target, edge_id="edge:middle-target"),
                ),
            ),
            Path.cwd(),
        )
        server = create_server(state, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        api = server.RequestHandlerClass.keywords["api"]
        payload = {
            "contract_version": "1.0.0",
            "targets": [
                {"value": source.id, "kind": None},
                {"value": target.id, "kind": None},
            ],
            "bounds": {
                "max_depth": 2,
                "max_items": 30,
                "max_paths": 3,
                "max_expansions": 100,
                "context_units": 100,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        workers = 6
        handler_start = Barrier(workers)
        builder_started = Event()
        release_builder = Event()
        original_builder = path_module._minimum_hops_to_targets
        original_intelligence = api.intelligence

        def delayed_builder(*args, **kwargs):
            builder_started.set()
            if not release_builder.wait(2):
                raise TimeoutError("distance builder release timed out")
            return original_builder(*args, **kwargs)

        def synchronized_intelligence(operation, request):
            handler_start.wait(timeout=3)
            return original_intelligence(operation, request)

        def post() -> tuple[int, str | None, bytes]:
            connection = HTTPConnection(
                "127.0.0.1",
                server.server_port,
                timeout=3,
            )
            connection.request(
                "POST",
                "/api/v1/intelligence/path",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            response = connection.getresponse()
            result = (
                response.status,
                response.getheader("Content-Type"),
                response.read(),
            )
            connection.close()
            return result

        try:
            with patch.object(
                path_module,
                "_minimum_hops_to_targets",
                side_effect=delayed_builder,
            ) as distance_builder:
                with patch.object(
                    api,
                    "intelligence",
                    side_effect=synchronized_intelligence,
                ):
                    with ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = [executor.submit(post) for _ in range(workers)]
                        try:
                            self.assertTrue(builder_started.wait(2))
                            sleep(0.05)
                            self.assertEqual(1, distance_builder.call_count)
                        finally:
                            release_builder.set()
                        results = [future.result(timeout=3) for future in futures]

            self.assertEqual(1, distance_builder.call_count)
            self.assertEqual({200}, {status for status, _, _ in results})
            self.assertEqual(
                {"application/json; charset=utf-8"},
                {content_type for _, content_type, _ in results},
            )
            self.assertEqual(1, len({sha256(item[2]).hexdigest() for item in results}))
            response_payload = json.loads(results[0][2])
            self.assertEqual("complete", response_payload["completion"]["reason"])
            self.assertEqual(
                [source.id, middle.id, target.id],
                response_payload["paths"][0]["node_ids"],
            )
        finally:
            release_builder.set()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_server_bounds_listener_queue_and_request_threads(self) -> None:
        source = make_node("Source", node_id="node:source")
        target = make_node("Target", node_id="node:target")
        state = DashboardState()
        state.load_graph(
            build_graph(
                [source, target],
                (make_edge(source, target, edge_id="edge:source-target"),),
            ),
            Path.cwd(),
        )
        with patch.object(DashboardThreadingHTTPServer, "max_request_threads", 2):
            server = create_server(state, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        api = server.RequestHandlerClass.keywords["api"]
        payload = {
            "contract_version": "1.0.0",
            "targets": [
                {"value": source.id, "kind": None},
                {"value": target.id, "kind": None},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        entered_two = Event()
        release_handlers = Event()
        active_lock = Lock()
        active_handlers = 0
        peak_handlers = 0
        original_intelligence = api.intelligence

        def blocked_intelligence(operation, request):
            nonlocal active_handlers, peak_handlers
            with active_lock:
                active_handlers += 1
                peak_handlers = max(peak_handlers, active_handlers)
                if active_handlers == 2:
                    entered_two.set()
            try:
                if not release_handlers.wait(2):
                    raise TimeoutError("request handler release timed out")
                return original_intelligence(operation, request)
            finally:
                with active_lock:
                    active_handlers -= 1

        def post() -> tuple[int, str | None, bytes]:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            connection.request(
                "POST",
                "/api/v1/intelligence/path",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            response = connection.getresponse()
            result = (
                response.status,
                response.getheader("Content-Type"),
                response.read(),
            )
            connection.close()
            return result

        try:
            self.assertEqual(64, server.request_queue_size)
            self.assertEqual(2, server.max_request_threads)
            with patch.object(
                api,
                "intelligence",
                side_effect=blocked_intelligence,
            ) as intelligence:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(post) for _ in range(5)]
                    try:
                        self.assertTrue(entered_two.wait(2))
                        sleep(0.05)
                        self.assertEqual(2, intelligence.call_count)
                        self.assertEqual(2, peak_handlers)
                    finally:
                        release_handlers.set()
                    results = [future.result(timeout=3) for future in futures]
                self.assertEqual(5, intelligence.call_count)
            self.assertEqual({200}, {status for status, _, _ in results})
            self.assertEqual(
                {"application/json; charset=utf-8"},
                {content_type for _, content_type, _ in results},
            )
            self.assertEqual(1, len({sha256(item[2]).hexdigest() for item in results}))
            self.assertEqual(2, peak_handlers)
        finally:
            release_handlers.set()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_server_read_deadline_releases_idle_clients_and_shutdown(self) -> None:
        state = DashboardState()
        with (
            patch.object(DashboardThreadingHTTPServer, "max_request_threads", 2),
            patch.object(
                DashboardThreadingHTTPServer,
                "request_read_timeout_seconds",
                0.2,
            ),
        ):
            server = create_server(state, port=0)
        waiting_for_slot = Event()
        shutdown_done = Event()
        original_process_request = server.process_request

        def observed_process_request(request, client_address):
            if server._request_slots._value == 0:
                waiting_for_slot.set()
            return original_process_request(request, client_address)

        server.process_request = observed_process_request
        thread = Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        thread.start()
        slow_header = socket.create_connection(
            ("127.0.0.1", server.server_port),
            timeout=1,
        )
        partial_body = socket.create_connection(
            ("127.0.0.1", server.server_port),
            timeout=1,
        )
        probe_result: dict[str, object] = {}
        probe_done = Event()

        def health_request() -> None:
            connection = HTTPConnection(
                "127.0.0.1",
                server.server_port,
                timeout=2,
            )
            try:
                connection.request("GET", "/api/health")
                response = connection.getresponse()
                probe_result.update(
                    status=response.status,
                    content_type=response.getheader("Content-Type"),
                    body=response.read(),
                )
            except Exception as error:
                probe_result["error"] = error
            finally:
                connection.close()
                probe_done.set()

        def stop_server() -> None:
            server.shutdown()
            shutdown_done.set()

        probe_thread = Thread(target=health_request, daemon=True)
        shutdown_thread = Thread(target=stop_server, daemon=True)
        try:
            slow_header.sendall(
                b"POST /api/v1/intelligence/path HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: 64\r\n"
            )
            partial_body.sendall(
                b"POST /api/v1/intelligence/path HTTP/1.1\r\n"
                b"Host: 127.0.0.1\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: 64\r\n\r\n"
                b"{"
            )
            slots_deadline = monotonic() + 1
            while server._request_slots._value and monotonic() < slots_deadline:
                sleep(0.005)
            self.assertEqual(0, server._request_slots._value)

            probe_thread.start()
            self.assertTrue(waiting_for_slot.wait(1))
            self.assertFalse(probe_done.wait(0.05))

            shutdown_started = monotonic()
            shutdown_thread.start()
            self.assertFalse(shutdown_done.wait(0.05))
            self.assertTrue(shutdown_done.wait(1))
            self.assertLess(monotonic() - shutdown_started, 1)
            self.assertTrue(probe_done.wait(1))
            self.assertNotIn("error", probe_result)
            self.assertEqual(200, probe_result["status"])
            self.assertEqual(
                "application/json; charset=utf-8",
                probe_result["content_type"],
            )

            for client in (slow_header, partial_body):
                client.settimeout(1)
                self.assertEqual(b"", client.recv(1))
            slots_deadline = monotonic() + 1
            while server._request_slots._value != 2 and monotonic() < slots_deadline:
                sleep(0.005)
            self.assertEqual(2, server._request_slots._value)
        finally:
            for client in (slow_header, partial_body):
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                client.close()
            if shutdown_thread.is_alive():
                shutdown_done.wait(2)
            elif not shutdown_done.is_set():
                server.shutdown()
            probe_thread.join(timeout=2)
            shutdown_thread.join(timeout=2)
            server.server_close()
            thread.join(timeout=2)

    def test_absolute_read_deadline_releases_slow_drip_clients(self) -> None:
        state = DashboardState()
        with (
            patch.object(DashboardThreadingHTTPServer, "max_request_threads", 2),
            patch.object(
                DashboardThreadingHTTPServer,
                "request_read_timeout_seconds",
                0.2,
            ),
            patch.object(
                DashboardThreadingHTTPServer,
                "request_read_deadline_seconds",
                0.5,
            ),
        ):
            server = create_server(state, port=0)
        thread = Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        )
        thread.start()
        clients = [
            socket.create_connection(("127.0.0.1", server.server_port), timeout=1)
            for _ in range(2)
        ]
        stop_drip = Event()

        def drip(client: socket.socket) -> None:
            while not stop_drip.wait(0.05):
                try:
                    client.sendall(b"x")
                except OSError:
                    return

        drippers = [Thread(target=drip, args=(client,), daemon=True) for client in clients]
        for dripper in drippers:
            dripper.start()
        try:
            slots_deadline = monotonic() + 1
            while server._request_slots._value and monotonic() < slots_deadline:
                sleep(0.005)
            self.assertEqual(0, server._request_slots._value)

            started = monotonic()
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=2)
            connection.request("GET", "/api/health")
            response = connection.getresponse()
            elapsed = monotonic() - started
            payload = json.loads(response.read())
            connection.close()

            self.assertEqual(200, response.status)
            self.assertTrue(payload["ok"])
            self.assertGreater(elapsed, 0.25)
            self.assertLess(elapsed, 1.5)
        finally:
            stop_drip.set()
            for client in clients:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                client.close()
            for dripper in drippers:
                dripper.join(timeout=1)
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_normalized_path_route_status_mapping_and_content_type(self) -> None:
        state = ready_state()
        server = create_server(state, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        api = server.RequestHandlerClass.keywords["api"]
        base = {
            "contract_version": "1.0.0",
            "targets": [
                {"value": "OnTick", "kind": None},
                {"value": "CalculateLots", "kind": None},
            ],
        }

        def post(payload: dict[str, object]) -> tuple[int, str | None, dict[str, object]]:
            body = json.dumps(payload).encode("utf-8")
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            connection.request(
                "POST",
                "/api/v1/intelligence/path",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            response = connection.getresponse()
            result = (
                response.status,
                response.getheader("Content-Type"),
                json.loads(response.read()),
            )
            connection.close()
            return result

        try:
            status, content_type, payload = post(base)
            self.assertEqual(200, status)
            self.assertEqual("application/json; charset=utf-8", content_type)
            self.assertEqual("path", payload["operation"])
            self.assertEqual("complete", payload["completion"]["reason"])
            self.assertEqual(1, len(payload["paths"]))

            request_errors = (
                ({**base, "operation": "query"}, 400, "invalid_request"),
                ({**base, "bounds": {"max_paths": 0}}, 400, "invalid_parameter"),
                ({**base, "targets": base["targets"][:1]}, 400, "missing_target"),
                (
                    {**base, "contract_version": "2.0.0"},
                    409,
                    "unsupported_contract_version",
                ),
                (
                    {**base, "expected_source_fingerprint": "different"},
                    409,
                    "graph_identity_mismatch",
                ),
            )
            for request, expected_status, expected_code in request_errors:
                with self.subTest(code=expected_code):
                    status, content_type, payload = post(request)
                    self.assertEqual(expected_status, status)
                    self.assertEqual("application/json; charset=utf-8", content_type)
                    self.assertEqual(expected_code, payload["error"]["code"])

            projected_errors = (
                (IntelligenceError.unsupported_operation("path"), 409),
                (IntelligenceError.unsupported_graph_schema("2.0.0"), 409),
                (
                    IntelligenceError(
                        "state",
                        "graph_not_ready",
                        "Graph snapshot is not ready",
                        retryable=True,
                    ),
                    409,
                ),
                (
                    IntelligenceError(
                        "integrity",
                        "graph_integrity_error",
                        "Graph integrity check failed",
                    ),
                    422,
                ),
                (
                    IntelligenceError(
                        "internal",
                        "unexpected_intelligence_error",
                        "Unexpected intelligence failure",
                    ),
                    500,
                ),
            )
            for error, expected_status in projected_errors:
                with self.subTest(code=error.code):
                    with patch.object(api, "intelligence", side_effect=error):
                        status, content_type, payload = post(base)
                    self.assertEqual(expected_status, status)
                    self.assertEqual("application/json; charset=utf-8", content_type)
                    self.assertEqual(error.code, payload["error"]["code"])

            with patch.object(api, "intelligence", side_effect=RuntimeError("boom")):
                status, content_type, payload = post(base)
            self.assertEqual(500, status)
            self.assertEqual("application/json; charset=utf-8", content_type)
            self.assertEqual("internal_error", payload["error"]["code"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_legacy_http_contract_golden_bytes(self) -> None:
        contract = json.loads(
            (Path(__file__).parent / "fixtures" / "contracts" / "legacy_http.json").read_text(
                encoding="utf-8"
            )
        )
        state = DashboardState()
        state.load_graph(analyze_repository(FIXTURE), FIXTURE)
        server = create_server(state, port=0)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            for case in contract["cases"]:
                with self.subTest(path=case["path"]):
                    connection.request(case["method"], case["path"])
                    response = connection.getresponse()
                    body = response.read()
                    self.assertEqual(case["status"], response.status)
                    self.assertEqual(case["content_type"], response.getheader("Content-Type"))
                    self.assertEqual(
                        case["body_sha256"], sha256(body).hexdigest()
                    )
                    self.assertEqual(case["body_json"], json.loads(body))
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
