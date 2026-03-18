"""
graph.py — LangGraph flow for Manufacturing BI Copilot.

Pipeline:
  ingest_question → fast_path_sql → guardrail → execute_sql
                                                     ↓ (success)
                                               suggest_chart → explain_answer → END
                                                     ↓ (fail, retry_count == 0)
                                               retry_sql → execute_sql
                                                     ↓ (success or fail)
                                               suggest_chart → explain_answer → END
"""

from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    ingest_question,
    fast_path_sql,
    guardrail,
    execute_sql_node,
    retry_sql,              # ✅ new import
    suggest_chart_node,
    explain_answer,
)


def _route_after_execute(state: AgentState) -> str:
    """
    Conditional router after execute_sql.

    - If execution succeeded     → proceed to suggest_chart
    - If failed AND no retry yet → go to retry_sql (one chance to self-correct)
    - If failed AND already tried → proceed to suggest_chart (surface the error)
    """
    executed    = state.get("executed_results", [])
    retry_count = state.get("retry_count", 0)
    any_success = any(r.get("success") for r in executed)

    if not any_success and retry_count == 0:
        return "retry_sql"
    return "suggest_chart"


def build_graph() -> StateGraph:
    """
    Build and compile the agent graph with lightweight retry.

    Flow:
        ingest_question
            ↓
        fast_path_sql   (single SQL, schema from cache)
            ↓
        guardrail       (block dangerous DML/DDL)
            ↓
        execute_sql     (run the query)
            ↓ [conditional]
          fail + no retry → retry_sql → execute_sql
          success / 2nd attempt → suggest_chart
            ↓
        explain_answer
            ↓
           END
    """
    builder = StateGraph(AgentState)

    # Register all nodes
    builder.add_node("ingest_question", ingest_question)
    builder.add_node("fast_path_sql",   fast_path_sql)
    builder.add_node("guardrail",       guardrail)
    builder.add_node("execute_sql",     execute_sql_node)
    builder.add_node("retry_sql",       retry_sql)       # ✅ new node
    builder.add_node("suggest_chart",   suggest_chart_node)
    builder.add_node("explain_answer",  explain_answer)

    # Straight edges
    builder.set_entry_point("ingest_question")
    builder.add_edge("ingest_question", "fast_path_sql")
    builder.add_edge("fast_path_sql",   "guardrail")
    builder.add_edge("guardrail",       "execute_sql")

    # ✅ Conditional edge: retry once on failure
    builder.add_conditional_edges(
        "execute_sql",
        _route_after_execute,
        {
            "retry_sql":     "retry_sql",
            "suggest_chart": "suggest_chart",
        }
    )

    # ✅ Retry loops back into execute_sql (not guardrail — LLM already filtered)
    builder.add_edge("retry_sql",     "execute_sql")

    # Remaining straight edges
    builder.add_edge("suggest_chart", "explain_answer")
    builder.add_edge("explain_answer", END)

    return builder.compile()
