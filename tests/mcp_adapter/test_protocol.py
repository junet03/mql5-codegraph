from __future__ import annotations

import asyncio
from pathlib import Path
import shutil
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "basic_ea"
EXPECTED_TOOLS = {
    "find_paths",
    "get_context",
    "get_context_package",
    "get_diagnostics",
    "get_impact",
    "index_project",
    "project_status",
    "query_symbols",
}


def _server_parameters() -> StdioServerParameters:
    entry_point = shutil.which("mql5-codegraph-mcp")
    if entry_point:
        return StdioServerParameters(command=entry_point, args=[])
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mql5_codegraph.mcp.server"],
    )


async def _exercise_protocol() -> None:
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

            indexed = await client.call_tool(
                "index_project",
                {"root": str(FIXTURE_ROOT.resolve())},
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


class McpProtocolTests(unittest.TestCase):
    def test_official_client_can_use_the_stdio_server(self) -> None:
        asyncio.run(_exercise_protocol())

    def test_adapter_error_is_a_tool_error_not_a_server_crash(self) -> None:
        asyncio.run(_exercise_tool_error())


if __name__ == "__main__":
    unittest.main()
