from __future__ import annotations

import io
import json
from unittest import TestCase
from unittest.mock import patch

from mql5_codegraph.mcp.server import LIFECYCLE_PREFIX, main


class _CrashingServer:
    def run(self, *, transport: str) -> None:
        raise RuntimeError(f"{transport} failed")


def _events(raw: str) -> list[dict[str, object]]:
    return [
        json.loads(line.removeprefix(LIFECYCLE_PREFIX))
        for line in raw.splitlines()
        if line.startswith(LIFECYCLE_PREFIX)
    ]


class McpLifecycleTests(TestCase):
    def test_unhandled_server_failure_is_reported_before_reraise(self) -> None:
        stderr = io.StringIO()

        with (
            patch("mql5_codegraph.mcp.server.create_server", return_value=_CrashingServer()),
            patch("mql5_codegraph.mcp.server.sys.stderr", stderr),
            self.assertRaisesRegex(RuntimeError, "stdio failed"),
        ):
            main()

        events = _events(stderr.getvalue())
        self.assertEqual(["starting", "crashed"], [event["event"] for event in events])
        self.assertEqual("unhandled_exception", events[-1]["reason"])
        self.assertEqual("RuntimeError", events[-1]["exception_type"])
        self.assertEqual(1, events[-1]["exit_code"])
