from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from shutil import copy2, copytree
import sys
from tempfile import TemporaryDirectory, TemporaryFile
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mql5_codegraph.mcp.server import LIFECYCLE_PREFIX


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "basic_ea"
COMPILER_LOG = Path(__file__).parents[1] / "fixtures" / "compiler_logs" / "basic-success.log"
EXPECTED_TOOLS = {
    "correlate_compiler_log",
    "find_paths",
    "get_context",
    "get_context_package",
    "get_diagnostics",
    "get_impact",
    "get_reference_excerpt",
    "index_project",
    "load_reference_corpus",
    "project_status",
    "query_symbols",
    "reference_status",
    "search_reference",
}


def _server_parameters() -> StdioServerParameters:
    project_root = Path(__file__).parents[2]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(project_root / "src")
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mql5_codegraph.mcp.server"],
        cwd=project_root,
        env=environment,
    )


def _lifecycle_events(raw: str) -> list[dict[str, object]]:
    return [
        json.loads(line.removeprefix(LIFECYCLE_PREFIX))
        for line in raw.splitlines()
        if line.startswith(LIFECYCLE_PREFIX)
    ]


async def _exercise_protocol() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory) / "basic_ea"
        copytree(FIXTURE_ROOT, root)
        log_path = root / "compiler.log"
        copy2(COMPILER_LOG, log_path)
        for source in root.rglob("*"):
            if source.suffix.lower() in {".mq5", ".mqh"}:
                os.utime(source, ns=(1_000_000_000, 1_000_000_000))
        os.utime(log_path, ns=(2_000_000_000, 2_000_000_000))

        parameters = _server_parameters()
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                listed = await client.list_tools()
                tools = {tool.name: tool for tool in listed.tools}
                if set(tools) != EXPECTED_TOOLS:
                    raise AssertionError(f"Unexpected MCP tools: {sorted(tools)}")
                for tool in tools.values():
                    annotations = tool.annotations
                    if annotations is None:
                        raise AssertionError(f"{tool.name} is missing annotations")
                    if annotations.readOnlyHint is not True:
                        raise AssertionError(f"{tool.name} is not read-only")
                    if annotations.destructiveHint is not False:
                        raise AssertionError(f"{tool.name} is marked destructive")
                    if annotations.openWorldHint is not False:
                        raise AssertionError(f"{tool.name} is marked open-world")

                empty_status = await client.call_tool("project_status", {})
                if empty_status.isError:
                    raise AssertionError("project_status unexpectedly failed")
                if empty_status.structuredContent != {
                    "status": "not_indexed",
                    "revision": 0,
                }:
                    raise AssertionError(empty_status.structuredContent)

                empty_reference = await client.call_tool("reference_status", {})
                if empty_reference.isError:
                    raise AssertionError("reference_status unexpectedly failed")
                if empty_reference.structuredContent != {
                    "status": "not_loaded",
                    "revision": 0,
                }:
                    raise AssertionError(empty_reference.structuredContent)

                indexed = await client.call_tool(
                    "index_project",
                    {"root": str(root)},
                )
                if indexed.isError:
                    raise AssertionError("index_project unexpectedly failed")
                if indexed.structuredContent["status"] != "indexed":
                    raise AssertionError(indexed.structuredContent)

                queried = await client.call_tool(
                    "query_symbols",
                    {"target": "OnTick"},
                )
                if queried.isError:
                    raise AssertionError("query_symbols unexpectedly failed")
                if queried.structuredContent["operation"] != "query":
                    raise AssertionError(queried.structuredContent)
                if not queried.structuredContent["nodes"]:
                    raise AssertionError("query_symbols returned no OnTick node")

                correlated = await client.call_tool(
                    "correlate_compiler_log",
                    {"log_path": "compiler.log", "entry_file": "BasicEA.mq5"},
                )
                if correlated.isError:
                    raise AssertionError("correlate_compiler_log unexpectedly failed")
                evidence = correlated.structuredContent["compiler_evidence"]
                if evidence["evidence_state"] != "current" or evidence["outcome"] != "success":
                    raise AssertionError(correlated.structuredContent)


async def _exercise_tool_error() -> None:
    parameters = _server_parameters()
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            await client.initialize()
            result = await client.call_tool("query_symbols", {"target": "OnTick"})
            if not result.isError:
                raise AssertionError("pre-index query unexpectedly succeeded")
            text = "\n".join(
                item.text for item in result.content if getattr(item, "type", None) == "text"
            )
            if "project_not_indexed" not in text:
                raise AssertionError(text)


async def _exercise_idle_lifecycle() -> None:
    idle_seconds = float(os.environ.get("MQL5_CODEGRAPH_MCP_IDLE_TEST_SECONDS", "0.25"))
    parameters = _server_parameters()
    with TemporaryFile(mode="w+", encoding="utf-8") as errlog:
        async with stdio_client(parameters, errlog=errlog) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                indexed = await client.call_tool(
                    "index_project",
                    {"root": str(FIXTURE_ROOT)},
                )
                if indexed.isError:
                    raise AssertionError("index_project unexpectedly failed")
                await asyncio.sleep(idle_seconds)
                status = await client.call_tool("project_status", {})
                if status.isError:
                    raise AssertionError("project_status failed after idle")
                if status.structuredContent["revision"] != indexed.structuredContent["revision"]:
                    raise AssertionError(status.structuredContent)

        errlog.seek(0)
        events = _lifecycle_events(errlog.read())

    event_names = [event["event"] for event in events]
    if event_names != ["starting", "stopped"]:
        raise AssertionError(events)
    stopped = events[-1]
    if stopped["reason"] != "stdio_eof" or stopped["exit_code"] != 0:
        raise AssertionError(stopped)


class McpProtocolTests(unittest.TestCase):
    def test_official_client_can_use_the_stdio_server(self) -> None:
        asyncio.run(_exercise_protocol())

    def test_adapter_error_is_a_tool_error_not_a_server_crash(self) -> None:
        asyncio.run(_exercise_tool_error())

    def test_idle_session_survives_and_reports_clean_stdio_eof(self) -> None:
        asyncio.run(_exercise_idle_lifecycle())


if __name__ == "__main__":
    unittest.main()
