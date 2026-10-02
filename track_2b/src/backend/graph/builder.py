from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from graph.nodes.build_context import build_context
from graph.nodes.npc_orchestrator import generate_npcs
from graph.nodes.parse_policy import parse_policy
from graph.nodes.run_round import run_round
from models.state import SimState


def should_continue(state: SimState) -> str:
    if state["current_round"] < state["max_rounds"]:
        return "run_round"
    return END


def build_graph() -> CompiledStateGraph[Any, Any, Any, Any]:  # type: ignore[type-arg]
    graph = StateGraph(SimState)
    graph.add_node("build_context", build_context)
    graph.add_node("parse_policy", parse_policy)
    graph.add_node("generate_npcs", generate_npcs)
    graph.add_node("run_round", run_round)

    graph.add_edge(START, "build_context")
    graph.add_edge("build_context", "parse_policy")
    graph.add_edge("parse_policy", "generate_npcs")
    graph.add_edge("generate_npcs", "run_round")
    graph.add_conditional_edges("run_round", should_continue)

    return graph.compile()
