"""
nodes.py — Agent nodes for Manufacturing BI Copilot.

Key changes vs. original:
  - Schema is fetched ONCE at module load and cached (_SCHEMA_CACHE).
    Every request reuses the cache — no DB round-trip per query.
  - generate_candidates → fast_path_sql: produces ONE high-quality SQL query.
  - System prompt is tailored for manufacturing KPIs (OEE, downtime,
    inventory, order fulfillment, production throughput).
  - explain_answer now emits exactly ONE concise sentence to minimise
    final-hop latency.
  - retry_count / last_error / max_retries fields removed throughout.
"""

import json
import time
import logging
from typing import Optional

import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from backend.config import OPENAI_MODEL, OPENAI_API_KEY
from .state import AgentState, SQLResult, SafetyFlags
from backend.utils.db import get_engine, run_sql
from backend.utils.guardrails import check_sql_safety
from backend.utils.charting import suggest_chart

logger = logging.getLogger("bi_copilot")

# ---------------------------------------------------------------------------
# Schema cache — populated once at startup, reused for every request.
# ---------------------------------------------------------------------------
_SCHEMA_CACHE: Optional[str] = None


def _get_cached_schema() -> str:
    """
    Return the cached DB schema string.
    Fetches from the database only on the first call; subsequent calls are
    instant (no network/IO overhead).
    """
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        logger.info("Schema cache miss — fetching schema from database …")
        engine = get_engine()
        db = SQLDatabase(engine)
        _SCHEMA_CACHE = db.get_table_info()
        logger.info("Schema cached successfully (%d chars).", len(_SCHEMA_CACHE))
    return _SCHEMA_CACHE


def warm_schema_cache() -> None:
    """
    Call this from the FastAPI startup event so the schema is ready before
    the first real request arrives.
    """
    _get_cached_schema()


# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

def _ensure_llm() -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.0,   # deterministic output for production reliability
    )


# ---------------------------------------------------------------------------
# Manufacturing-focused system prompt
# ---------------------------------------------------------------------------

_MANUFACTURING_SYSTEM_PROMPT = """\
You are a PostgreSQL expert embedded in a manufacturing operations platform.
Your sole job is to write a single, production-ready SELECT query that answers
the operator's question using ONLY the tables and columns in the provided schema.

DOMAIN FOCUS — Manufacturing KPIs:
  • Production efficiency & OEE (Overall Equipment Effectiveness)
  • Machine downtime (planned vs. unplanned, MTBF, MTTR)
  • Inventory levels (raw materials, WIP, finished goods, reorder alerts)
  • Order fulfillment (on-time delivery rate, lead time, backlog)
  • Shift / line / cell throughput and yield rates

QUERY RULES:
  1. ALWAYS write time-series queries when the question involves trends,
     history, or "over time" — GROUP BY the date/shift column and ORDER BY
     it ascending so charts render correctly.
  2. First column  → Label / Dimension (date, machine_id, product_line, …)
     Remaining cols → Numeric aggregates (SUM, AVG, COUNT, MIN, MAX).
  3. Use meaningful aliases: total_units_produced, avg_cycle_time_min,
     downtime_hours, fulfillment_rate_pct, etc.
  4. Never expose raw surrogate IDs unless explicitly requested.
  5. For rankings, apply LIMIT 10 (or fewer if asked).
  6. Write READ-ONLY queries. Never emit INSERT, UPDATE, DELETE, DROP, ALTER,
     TRUNCATE, CREATE, or GRANT.
  7. Return ONLY valid JSON — no markdown, no explanations:
     {"sql": "<your single SQL query>"}
  8. Always cast to NUMERIC before using ROUND() with a scale:
     Use ROUND(AVG(...)::NUMERIC, 2) not ROUND(AVG(...), 2).
     PostgreSQL ROUND(double precision, integer) does not exist.
"""

_FEW_SHOT_EXAMPLES = """\
Examples:
Q: Show machine downtime by day for the last 30 days
A: {"sql": "SELECT DATE(event_time) AS day, SUM(downtime_minutes) / 60.0 AS downtime_hours FROM machine_events WHERE event_type = 'downtime' AND event_time >= NOW() - INTERVAL '30 days' GROUP BY DATE(event_time) ORDER BY day;"}

Q: Which production lines have the lowest OEE this week?
A: {"sql": "SELECT line_id, ROUND(AVG(oee_pct)::NUMERIC, 2) AS avg_oee_pct FROM production_metrics WHERE shift_date >= DATE_TRUNC('week', CURRENT_DATE) GROUP BY line_id ORDER BY avg_oee_pct ASC LIMIT 10;"}

Q: Current inventory levels below reorder point
A: {"sql": "SELECT part_number, description, quantity_on_hand, reorder_point, (reorder_point - quantity_on_hand) AS shortage FROM inventory WHERE quantity_on_hand < reorder_point ORDER BY shortage DESC;"}

Q: On-time delivery rate by customer for this month
A: {"sql": "SELECT customer_name, COUNT(*) AS total_orders, ROUND(100.0 * SUM(CASE WHEN delivered_date <= promised_date THEN 1 ELSE 0 END) / COUNT(*), 2) AS on_time_pct FROM orders WHERE DATE_TRUNC('month', promised_date) = DATE_TRUNC('month', CURRENT_DATE) GROUP BY customer_name ORDER BY on_time_pct ASC;"}
"""


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

def ingest_question(state: AgentState) -> AgentState:
    """Stamp trace ID and record ingest timestamp."""
    trace_id = state.get("trace_id") or str(int(time.time() * 1000))
    state["trace_id"] = trace_id
    state.setdefault("metadata", {})["ingest_time"] = time.time()
    logger.info("Trace %s — ingest_question: %s", trace_id, state.get("question"))
    return state


def fast_path_sql(state: AgentState) -> AgentState:
    """
    Generate ONE high-quality SQL query in a single LLM call.

    Uses the cached schema — no DB round-trip.
    Returns the SQL in state["sql_candidates"] (list of one) so the rest of
    the pipeline (guardrail, execute_sql) stays compatible.
    """
    llm = _ensure_llm()
    question = state["question"]
    schema = _get_cached_schema()

    user_prompt = (
        f"SCHEMA:\n{schema}\n\n"
        f"{_FEW_SHOT_EXAMPLES}\n"
        f"Now write one SQL query for:\n"
        f"Question: {question}\n"
        "Return ONLY JSON: {\"sql\": \"<query>\"}"
    )

    start = time.time()
    resp = llm.invoke(
        [
            {"role": "system", "content": _MANUFACTURING_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ]
    )
    tft_ms = (time.time() - start) * 1000.0

    sql = ""
    try:
        data = json.loads(resp.content)
        sql = data.get("sql", "").strip()
    except Exception:
        logger.exception("Trace %s — failed to parse LLM JSON; using raw content.",
                         state.get("trace_id"))
        sql = resp.content.strip()

    state["sql_candidates"] = [sql] if sql else []
    state["tft_ms"] = tft_ms
    logger.info("Trace %s — fast_path_sql generated query in %.1f ms",
                state.get("trace_id"), tft_ms)
    return state


def guardrail(state: AgentState) -> AgentState:
    """Block any DML/DDL that slipped through the prompt."""
    candidates = state.get("sql_candidates", [])
    safety_flags: SafetyFlags = {"blocked": False, "reasons": []}
    filtered = []

    for sql in candidates:
        is_safe, reasons = check_sql_safety(sql)
        if is_safe:
            filtered.append(sql)
        else:
            safety_flags["blocked"] = True
            safety_flags.setdefault("reasons", []).extend(reasons)
            logger.warning("Trace %s — guardrail BLOCKED query: %s | reasons: %s",
                           state.get("trace_id"), sql[:80], reasons)

    # Fail-open: if everything was blocked, preserve candidate list so
    # execute_sql can surface a meaningful error rather than a silent empty.
    state["sql_candidates"] = filtered if filtered else candidates
    state["safety_flags"] = safety_flags
    logger.info("Trace %s — guardrail: %d candidate(s), blocked=%s",
                state.get("trace_id"), len(filtered), safety_flags["blocked"])
    return state


def execute_sql_node(state: AgentState) -> AgentState:
    """Execute the single candidate SQL and store results."""
    engine = get_engine()
    candidates = state.get("sql_candidates", [])
    executed_results = []
    tfr_ms = 0.0

    for sql in candidates:
        result: SQLResult = {
            "sql": sql,
            "success": False,
            "error": None,
            "blocked": state.get("safety_flags", {}).get("blocked", False),
            "latency_ms": 0.0,
            "preview_rows": [],
            "columns": [],
        }
        start = time.time()
        try:
            cols, rows = run_sql(engine, sql)
            latency_ms = (time.time() - start) * 1000.0
            result.update({
                "success": True,
                "latency_ms": latency_ms,
                "columns": cols,
                "preview_rows": rows[:20],
            })
            tfr_ms = latency_ms
            logger.info("Trace %s — SQL executed in %.1f ms, %d rows returned.",
                        state.get("trace_id"), latency_ms, len(rows))
        except Exception as exc:
            result["error"] = str(exc)
            state["last_error"] = str(exc)
            logger.error("Trace %s — SQL execution error: %s", state.get("trace_id"), exc)

        executed_results.append(result)

    # Pick the first successful result as the chosen one
    chosen = next((r for r in executed_results if r.get("success")), None)
    if chosen is None and executed_results:
        chosen = executed_results[0]  # surface error gracefully

    state["executed_results"] = executed_results
    state["tfr_ms"] = tfr_ms

    if chosen:
        state["chosen_sql"] = chosen["sql"]
        try:
            df = pd.DataFrame(chosen["preview_rows"], columns=chosen["columns"])
        except Exception:
            df = None
        state["chosen_df"] = df

    return state


def suggest_chart_node(state: AgentState) -> AgentState:
    """Suggest a Chart.js-compatible chart spec based on the result shape."""
    df = state.get("chosen_df")
    if isinstance(df, pd.DataFrame) and not df.empty:
        chart_spec = suggest_chart(df)
        state["chart_spec"] = chart_spec
        logger.info("Trace %s — chart: %s",
                    state.get("trace_id"),
                    chart_spec.get("chart_type") if chart_spec else "none")
    else:
        state["chart_spec"] = None
    return state


def explain_answer(state: AgentState) -> AgentState:
    """
    Generate a ONE-sentence plain-English insight for the operator.

    Kept intentionally brief to minimise final-hop LLM latency.
    If no SQL was chosen, this node is a no-op.
    """
    chosen_sql = state.get("chosen_sql")
    if not chosen_sql:
        return state

    llm = _ensure_llm()
    question = state["question"]

    user_prompt = (
        f"Question: {question}\n"
        f"SQL: {chosen_sql}\n\n"
        "In ONE concise sentence (max 20 words), state the key manufacturing "
        "insight this query reveals. No preamble."
    )

    resp = llm.invoke(
        [
            {"role": "system",
             "content": "You are a terse manufacturing analyst. Respond in one sentence only."},
            {"role": "user", "content": user_prompt},
        ]
    )

    state.setdefault("metadata", {})["explanation"] = resp.content.strip()
    logger.info("Trace %s — explanation added.", state.get("trace_id"))
    return state

def retry_sql(state: AgentState) -> AgentState:
    """
    Lightweight retry node — called at most ONCE when execute_sql fails.

    Feeds the failed SQL + the DB error message back into the LLM so it can
    self-correct. Common fixes: wrong column name, missing JOIN, bad alias.
    """
    llm = _ensure_llm()
    question  = state["question"]
    schema    = _get_cached_schema()
    failed_sql = state.get("chosen_sql", "")
    error_msg  = state.get("last_error", "Unknown error")

    user_prompt = (
        f"SCHEMA:\n{schema}\n\n"
        f"The following SQL query failed with this database error:\n"
        f"SQL:   {failed_sql}\n"
        f"Error: {error_msg}\n\n"
        f"Original question: {question}\n\n"
        "Fix ONLY what the error describes — do not rewrite the entire query "
        "unless necessary. Return ONLY JSON: {\"sql\": \"<corrected query>\"}"
    )

    start = time.time()
    resp = llm.invoke(
        [
            {"role": "system", "content": _MANUFACTURING_SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ]
    )
    retry_tft_ms = (time.time() - start) * 1000.0

    sql = ""
    try:
        data = json.loads(resp.content)
        sql = data.get("sql", "").strip()
    except Exception:
        logger.exception("Trace %s — retry_sql: failed to parse LLM JSON.",
                         state.get("trace_id"))
        sql = resp.content.strip()

    state["sql_candidates"] = [sql] if sql else []
    state["retry_count"]    = state.get("retry_count", 0) + 1
    state["tft_ms"]         = state.get("tft_ms", 0.0) + retry_tft_ms
    state["last_error"]     = None   # clear error for the next execute attempt

    logger.info(
        "Trace %s — retry_sql produced corrected query in %.1f ms (retry #%d)",
        state.get("trace_id"), retry_tft_ms, state["retry_count"]
    )
    return state