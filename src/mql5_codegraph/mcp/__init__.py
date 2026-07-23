"""Experimental local MCP adapter for MQL5 CodeGraph.

The package is intentionally separate from the backend-neutral Intelligence
Kernel. Importing :mod:`mql5_codegraph.mcp.service` does not require the
optional MCP SDK; only the protocol server does.
"""

from .service import AdapterError, ProjectSession, ProjectSnapshot

__all__ = ("AdapterError", "ProjectSession", "ProjectSnapshot")
