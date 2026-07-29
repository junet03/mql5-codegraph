"""MQL5 terminal event and trading lifecycle enrichment."""

from __future__ import annotations

from .analysis_budget import AnalysisBudget
from .graph import CodeGraph, GraphNode, stable_id


def enrich_runtime(
    graph: CodeGraph,
    *,
    budget: AnalysisBudget | None = None,
) -> None:
    active_budget = budget or AnalysisBudget()
    active_budget.consume("runtime_enrichment")
    terminal = graph.add_node(GraphNode(
        id=stable_id("runtime", "MetaTrader5Terminal"), kind="runtime",
        name="MetaTrader 5 Terminal", qualified_name="runtime::MetaTrader5Terminal",
        attributes={"platform": "MetaTrader 5"},
    ))
    handlers: dict[str, list[GraphNode]] = {}
    for node in list(graph.nodes.values()):
        active_budget.consume("runtime_enrichment")
        if node.kind != "event_handler":
            continue
        handlers.setdefault(node.name, []).append(node)
        graph.add_edge(terminal.id, node.id, "runtime_dispatches", "runtime", 1.0,
                       node.location, {"event": node.name})

    transaction_handlers = handlers.get("OnTradeTransaction", [])
    if transaction_handlers:
        send_nodes: list[GraphNode] = []
        for node in graph.nodes.values():
            active_budget.consume("runtime_enrichment")
            if node.kind == "external_function" and node.name in {"OrderSend", "OrderSendAsync"}:
                send_nodes.append(node)
        for send_node in send_nodes:
            active_budget.consume("runtime_enrichment")
            for handler in transaction_handlers:
                active_budget.consume("runtime_enrichment")
                graph.add_edge(send_node.id, handler.id, "may_trigger_event", "runtime", 0.9,
                               attributes={"runtime_rule": "trade request processing"})

    timer_handlers = handlers.get("OnTimer", [])
    timer_nodes: list[GraphNode] = []
    for node in graph.nodes.values():
        active_budget.consume("runtime_enrichment")
        if node.kind == "external_function" and node.name in {"EventSetTimer", "EventSetMillisecondTimer"}:
            timer_nodes.append(node)
    for timer_node in timer_nodes:
        active_budget.consume("runtime_enrichment")
        for handler in timer_handlers:
            active_budget.consume("runtime_enrichment")
            graph.add_edge(timer_node.id, handler.id, "may_trigger_event", "runtime", 0.95,
                           attributes={"runtime_rule": "timer registration"})
