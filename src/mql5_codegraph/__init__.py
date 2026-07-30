"""MQL5-aware static code graph indexing."""

from .version import __version__
from .graph import CodeGraph, GraphEdge, GraphNode, SourceLocation
from .indexer import analyze_repository

__all__ = [
    "CodeGraph",
    "GraphEdge",
    "GraphNode",
    "SourceLocation",
    "__version__",
    "analyze_repository",
]
