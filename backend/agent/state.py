"""
state.py — AgentState definition for the Manufacturing BI Copilot.

Removed from original:
  - retry_count, max_retries, last_error  (no retry loop in fast-path graph)
"""

from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
import pandas as pd


class SQLResult(TypedDict, total=False):
    sql: str
    success: bool
    error: Optional[str]
    blocked: bool
    latency_ms: float
    preview_rows: List[List[Any]]
    columns: List[str]


class SafetyFlags(TypedDict, total=False):
    blocked: bool
    reasons: List[str]


class AgentState(TypedDict, total=False):
    # Core I/O
    question: str
    schema_snapshot: str          # kept for compatibility; populated from cache

    # SQL pipeline
    sql_candidates: List[str]     # always a list of 1 in fast-path mode
    executed_results: List[SQLResult]
    chosen_sql: Optional[str]
    chosen_df: Optional[pd.DataFrame]

    retry_count: int            # how many retries have been attempted
    last_error: Optional[str]   # last SQL execution error message

    # Downstream artefacts
    chart_spec: Optional[Dict[str, Any]]
    safety_flags: SafetyFlags

    # Latency telemetry
    tft_ms: float                 # Time-to-First-Token (LLM generation)
    tfr_ms: float                 # Time-to-First-Result (DB execution)

    # Observability
    trace_id: str
    metadata: Dict[str, Any]     # carries total_latency_ms, explanation, …
