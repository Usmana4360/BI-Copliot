from typing import Dict, List, Tuple
import time

import numpy as np
import pandas as pd

from backend.config import EVAL_TAU_ATOL, EVAL_TAU_RTOL
from backend.utils.db import get_engine, run_sql_df

def is_aggregate_query(sql: str) -> bool:
    s = sql.lower()
    return any(k in s for k in ["sum(", "avg(", "count(", "min(", "max(", "group by"])

def fetch_result_df(sql: str, drift: bool = False) -> Tuple[pd.DataFrame, float, bool, str]:
    engine = get_engine(drift=drift)
    start = time.time()
    try:
        df = run_sql_df(engine, sql)
        latency_ms = (time.time() - start) * 1000.0
        return df, latency_ms, True, ""
    except Exception as e:
        latency_ms = (time.time() - start) * 1000.0
        return pd.DataFrame(), latency_ms, False, str(e)

def answer_set_exact_match(df_pred: pd.DataFrame, df_gold: pd.DataFrame) -> bool:
    try:
        return df_pred.equals(df_gold)
    except Exception:
        return False

def value_accuracy_tau(df_pred: pd.DataFrame, df_gold: pd.DataFrame) -> bool:
    if df_pred.shape != df_gold.shape:
        return False
    num_cols = df_gold.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        if col not in df_pred.columns:
            return False
        a = df_pred[col].to_numpy()
        b = df_gold[col].to_numpy()
        if not np.allclose(a, b, atol=EVAL_TAU_ATOL, rtol=EVAL_TAU_RTOL):
            return False
    return True

def set_f1(df_pred: pd.DataFrame, df_gold: pd.DataFrame) -> float:
    if df_pred.empty and df_gold.empty:
        return 1.0

    key_cols = list(df_gold.columns)
    def rows_to_set(df):
        return set(tuple(df[c].iloc[i] for c in key_cols) for i in range(len(df)))

    s_pred = rows_to_set(df_pred)
    s_gold = rows_to_set(df_gold)

    if not s_pred and not s_gold:
        return 1.0
    if not s_pred or not s_gold:
        return 0.0

    intersection = len(s_pred & s_gold)
    precision = intersection / len(s_pred) if s_pred else 0.0
    recall = intersection / len(s_gold) if s_gold else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)

def compute_latency_stats(latencies: List[float]) -> Dict[str, float]:
    if not latencies:
        return {"median": 0.0, "p90": 0.0}
    arr = np.array(latencies)
    return {
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
    }
