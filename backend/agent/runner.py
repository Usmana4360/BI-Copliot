"""
runner.py — Agent runner for the Manufacturing BI Copilot.

The compiled graph is built once at import time and reused for every request,
avoiding repeated graph compilation overhead.
"""

import time
import logging

from .state import AgentState
from .graph import build_graph

logger = logging.getLogger("bi_copilot")

# Compile once at module load — reused across all requests.
_graph = build_graph()


def run_agent(question: str) -> AgentState:
    """
    Run the fast-path agent for a single natural-language question.

    Returns the final AgentState, which includes:
      - chosen_sql      : the generated SQL query
      - executed_results: list with one SQLResult entry
      - chart_spec      : Chart.js-compatible chart specification (or None)
      - metadata        : total_latency_ms, explanation, ingest_time
      - tft_ms / tfr_ms : individual latency measurements
    """
    init_state: AgentState = {"question": question}

    start = time.time()
    final_state = _graph.invoke(init_state)
    total_latency_ms = (time.time() - start) * 1000.0

    final_state.setdefault("metadata", {})["total_latency_ms"] = total_latency_ms
    logger.info(
        "Trace %s — run_agent complete. total_latency_ms=%.2f",
        final_state.get("trace_id"),
        total_latency_ms,
    )
    return final_state
