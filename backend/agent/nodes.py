import time
import logging
from typing import List

import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from backend.config import OPENAI_MODEL, OPENAI_API_KEY
from .state import AgentState, SQLResult, SafetyFlags
from backend.utils.db import get_engine, run_sql
from backend.utils.guardrails import check_sql_safety
from backend.utils.charting import suggest_chart

logger = logging.getLogger("bi_copilot")

def _ensure_llm() -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.1,
    )
    return llm

def ingest_question(state: AgentState) -> AgentState:
    trace_id = state.get("trace_id") or str(int(time.time() * 1000))
    state["trace_id"] = trace_id
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["ingest_time"] = time.time()
    logger.info("Trace %s - ingest_question: %s", trace_id, state.get("question"))
    return state

def inspect_schema(state: AgentState) -> AgentState:
    engine = get_engine()
    db = SQLDatabase(engine)
    schema = db.get_table_info()
    state["schema_snapshot"] = schema
    logger.info("Trace %s - inspect_schema complete", state.get("trace_id"))
    return state

def generate_candidates(state: AgentState, top_k: int = 3) -> AgentState:
    llm = _ensure_llm()
    question = state["question"]
    schema = state.get("schema_snapshot", "")

    system_prompt = (
        "You are a BI assistant that writes read-only PostgreSQL SQL queries.\n"
        "You MUST only generate SELECT queries (optionally with CTEs).\n"
        "Use only the tables and columns from the provided schema.\n"
        "Respond in JSON with a single field 'candidates' which is a list of SQL strings.\n"
    )

    few_shot_hint = (
        "Example:\n"
        "Question: total sales by year\n"
        "SQL: SELECT EXTRACT(YEAR FROM order_date) AS year, SUM(total_price) AS total_sales "
        "FROM orders GROUP BY EXTRACT(YEAR FROM order_date) ORDER BY year;"
    )

    user_prompt = (
        f"SCHEMA:\n{schema}\n\n"
        f"{few_shot_hint}\n\n"
        f"Now write up to {top_k} candidate SQL queries for this question:\n"
        f"Question: {question}\n"
        "Return JSON only."
    )

    start = time.time()
    resp = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    tft_ms = (time.time() - start) * 1000.0

    import json
    sql_candidates: List[str] = []
    try:
        data = json.loads(resp.content)
        cands = data.get("candidates", [])
        sql_candidates = [c.strip() for c in cands if isinstance(c, str)]
    except Exception:
        logger.exception("Failed to parse LLM JSON, falling back to single candidate")
        sql_candidates = [resp.content.strip()]

    sql_candidates = sql_candidates[:top_k]
    state["sql_candidates"] = sql_candidates
    state["tft_ms"] = tft_ms
    logger.info("Trace %s - generated %d SQL candidates", state.get("trace_id"), len(sql_candidates))
    return state

def guardrail(state: AgentState) -> AgentState:
    candidates = state.get("sql_candidates", [])
    safety_flags: SafetyFlags = {"blocked": False, "reasons": []}
    filtered: List[str] = []
    for sql in candidates:
        is_safe, reasons = check_sql_safety(sql)
        if is_safe:
            filtered.append(sql)
        else:
            safety_flags["blocked"] = True
            safety_flags.setdefault("reasons", []).extend(reasons)
    if not filtered and candidates:
        filtered = candidates
    state["sql_candidates"] = filtered
    state["safety_flags"] = safety_flags
    logger.info("Trace %s - guardrail: %d candidates (blocked=%s)", state.get("trace_id"), len(filtered), safety_flags.get("blocked"))
    return state

def execute_sql_node(state: AgentState) -> AgentState:
    engine = get_engine()
    candidates = state.get("sql_candidates", [])
    executed_results: List[SQLResult] = []
    tfr_ms = None
    for sql in candidates:
        sql_result: SQLResult = {
            "sql": sql,
            "success": False,
            "error": None,
            "blocked": False,
            "latency_ms": 0.0,
            "preview_rows": [],
            "columns": [],
        }
        import time as _time
        start = _time.time()
        try:
            cols, rows = run_sql(engine, sql)
            latency_ms = (_time.time() - start) * 1000.0
            sql_result["success"] = True
            sql_result["latency_ms"] = latency_ms
            sql_result["columns"] = cols
            sql_result["preview_rows"] = rows[:20]
            if tfr_ms is None:
                tfr_ms = latency_ms
        except Exception as e:
            sql_result["success"] = False
            sql_result["error"] = str(e)
        executed_results.append(sql_result)

    state["executed_results"] = executed_results
    state["tfr_ms"] = tfr_ms if tfr_ms is not None else 0.0
    logger.info("Trace %s - execute_sql: %d candidates executed", state.get("trace_id"), len(executed_results))
    return state

def rank_candidates(state: AgentState) -> AgentState:
    executed_results = state.get("executed_results", [])
    chosen = None
    for r in executed_results:
        if r.get("success"):
            chosen = r
            break
    if chosen is None and executed_results:
        chosen = executed_results[0]
    if chosen is not None:
        state["chosen_sql"] = chosen["sql"]
        try:
            df = pd.DataFrame(chosen["preview_rows"], columns=chosen["columns"])
        except Exception:
            df = None
        state["chosen_df"] = df
    logger.info("Trace %s - rank_candidates chosen_sql: %s", state.get("trace_id"), state.get("chosen_sql"))
    return state

def suggest_chart_node(state: AgentState) -> AgentState:
    df = state.get("chosen_df")
    if isinstance(df, pd.DataFrame):
        state["chart_spec"] = suggest_chart(df)
    else:
        state["chart_spec"] = None
    logger.info("Trace %s - chart suggestion: %s", state.get("trace_id"), state.get("chart_spec"))
    return state

def explain_answer(state: AgentState) -> AgentState:
    if "chosen_sql" not in state or not state["chosen_sql"]:
        return state
    llm = _ensure_llm()
    question = state["question"]
    sql = state["chosen_sql"]
    system_prompt = "You are a BI assistant that explains SQL query results to business users."

    user_prompt = (
        f"Question: {question}\n"
        f"SQL: {sql}\n\n"
        "Explain in 2-3 short sentences what this query is doing and what kind of insight it returns.\n"
    )
    resp = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    state.setdefault("metadata", {})
    state["metadata"]["explanation"] = resp.content
    logger.info("Trace %s - explanation added", state.get("trace_id"))
    return state
