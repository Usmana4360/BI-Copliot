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

def build_graph(top_k: int = 3):
    builder = StateGraph(AgentState)

    builder.add_node("ingest_question", ingest_question)
    builder.add_node("inspect_schema", inspect_schema)

    def generate_candidates_node(state: AgentState) -> AgentState:
        return generate_candidates(state, top_k=top_k)

    builder.add_node("generate_candidates", generate_candidates_node)
    builder.add_node("guardrail", guardrail)
    builder.add_node("execute_sql", execute_sql_node)
    builder.add_node("rank_candidates", rank_candidates)
    builder.add_node("suggest_chart", suggest_chart_node)
    builder.add_node("explain_answer", explain_answer)

    builder.set_entry_point("ingest_question")
    builder.add_edge("ingest_question", "inspect_schema")
    builder.add_edge("inspect_schema", "generate_candidates")
    builder.add_edge("generate_candidates", "guardrail")
    builder.add_edge("guardrail", "execute_sql")
    builder.add_edge("execute_sql", "rank_candidates")
    builder.add_edge("rank_candidates", "suggest_chart")
    builder.add_edge("suggest_chart", "explain_answer")
    builder.add_edge("explain_answer", END)

    return builder.compile()
