"""LangGraph recommendation agent: compiles the graph."""

import uuid
from functools import partial

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.nodes import (
    execute_search,
    format_output,
    gather_context,
    plan_search,
    rank_and_filter,
)
from src.agent.state import AgentState
from langsmith import traceable

def build_graph(db: AsyncSession) -> StateGraph:
    """Build and compile the recommendation agent graph.

    The DB session is injected into nodes that need it via functools.partial.
    """
    graph = StateGraph(AgentState)

    # Add nodes — inject db session where needed
    graph.add_node("gather_context", partial(gather_context, db=db))
    graph.add_node("plan_search", plan_search)
    graph.add_node("execute_search", partial(execute_search, db=db))
    graph.add_node("rank_and_filter", rank_and_filter)
    graph.add_node("format_output", partial(format_output, db=db))

    # Linear flow
    graph.set_entry_point("gather_context")
    graph.add_edge("gather_context", "plan_search")
    graph.add_edge("plan_search", "execute_search")
    graph.add_edge("execute_search", "rank_and_filter")
    graph.add_edge("rank_and_filter", "format_output")
    graph.add_edge("format_output", END)

    return graph.compile()

@traceable
async def run_agent(
    db: AsyncSession,
    user_id: str,
    *,
    occasion: str | None = None,
    mood: str | None = None,
) -> dict:
    ' graph.py run_agent function '
    """Run the recommendation agent and return results."""
    agent = build_graph(db)
    run_id = str(uuid.uuid4())

    initial_state: AgentState = {
        "user_id": user_id,
        "occasion": occasion,
        "mood": mood,
        "user_profile": {},
        "weather": None,
        "trends": [],
        "search_queries": [],
        "candidate_products": [],
        "recommendations": [],
        "agent_run_id": run_id,
    }

    result = await agent.ainvoke(initial_state)
    return result
