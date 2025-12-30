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
    question: str
    schema_snapshot: str
    sql_candidates: List[str]
    executed_results: List[SQLResult]
    chosen_sql: Optional[str]
    chosen_df: Optional[pd.DataFrame]
    chart_spec: Optional[Dict[str, str]]
    safety_flags: SafetyFlags
    tft_ms: float
    tfr_ms: float
    trace_id: str
    metadata: Dict[str, Any]
