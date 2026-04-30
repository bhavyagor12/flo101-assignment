"""LangGraph wiring for the Critic.

  safety_input ─┬─► load_spec ─► capability_runner ─► rubric_critique
                │                                       │
                │                                       ▼
                │                                safety_disposition
                │                                       │
                └────────────────────────────────► assemble ─► END
"""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from flo101_api.critic.nodes import (
    assemble_node,
    capability_runner_node,
    load_spec_node,
    rubric_critique_node,
    safety_disposition_node,
    safety_input_node,
)
from flo101_api.critic.state import CriticState


def _route_after_safety(state: CriticState) -> str:
    return "load_spec" if state.get("safety_input_allow") else "assemble"


def build_critic_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    g: StateGraph[CriticState] = StateGraph(CriticState)
    g.add_node("safety_input", safety_input_node)
    g.add_node("load_spec", load_spec_node)
    g.add_node("capability_runner", capability_runner_node)
    g.add_node("rubric_critique", rubric_critique_node)
    g.add_node("safety_disposition", safety_disposition_node)
    g.add_node("assemble", assemble_node)

    g.set_entry_point("safety_input")
    g.add_conditional_edges(
        "safety_input",
        _route_after_safety,
        {"load_spec": "load_spec", "assemble": "assemble"},
    )
    g.add_edge("load_spec", "capability_runner")
    g.add_edge("capability_runner", "rubric_critique")
    g.add_edge("rubric_critique", "safety_disposition")
    g.add_edge("safety_disposition", "assemble")
    g.add_edge("assemble", END)

    return g.compile()


@lru_cache(maxsize=1)
def get_critic_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    return build_critic_graph()
