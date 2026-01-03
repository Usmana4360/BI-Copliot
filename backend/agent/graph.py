from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    ingest_question,
    inspect_schema,
    generate_candidates,
    guardrail,
    execute_sql_node,
    rank_candidates,
    suggest_chart_node,
    explain_answer,
)

def should_retry(state: AgentState) -> str:
    """
    Decide whether to retry SQL generation or proceed.
    Returns "retry" if should retry, "proceed" otherwise.
    """
    executed_results = state.get("executed_results", [])
    any_success = any(r.get("success") for r in executed_results)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    
    # If any query succeeded, proceed
    if any_success:
        return "proceed"
    
    # If we've hit max retries, proceed anyway (fail gracefully)
    if retry_count >= max_retries:
        return "proceed"
    
    # Otherwise, retry
    return "retry"

def increment_retry(state: AgentState) -> AgentState:
    """Increment retry counter before retrying."""
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state

def build_graph(top_k: int = 3):
    builder = StateGraph(AgentState)

    # Define nodes
    builder.add_node("ingest_question", ingest_question)
    builder.add_node("inspect_schema", inspect_schema)

    def generate_candidates_node(state: AgentState) -> AgentState:
        return generate_candidates(state, top_k=top_k)

    builder.add_node("generate_candidates", generate_candidates_node)
    builder.add_node("guardrail", guardrail)
    builder.add_node("execute_sql", execute_sql_node)
    builder.add_node("increment_retry", increment_retry)
    builder.add_node("rank_candidates", rank_candidates)
    builder.add_node("suggest_chart", suggest_chart_node)
    builder.add_node("explain_answer", explain_answer)

    # Build the flow
    builder.set_entry_point("ingest_question")
    builder.add_edge("ingest_question", "inspect_schema")
    builder.add_edge("inspect_schema", "generate_candidates")
    builder.add_edge("generate_candidates", "guardrail")
    builder.add_edge("guardrail", "execute_sql")
    
    # ✨ Self-correction conditional routing
    builder.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "retry": "increment_retry",
            "proceed": "rank_candidates",
        }
    )
    
    # Retry loop back to generate_candidates
    builder.add_edge("increment_retry", "generate_candidates")
    
    # Continue normal flow after ranking
    builder.add_edge("rank_candidates", "suggest_chart")
    builder.add_edge("suggest_chart", "explain_answer")
    builder.add_edge("explain_answer", END)

    return builder.compile()