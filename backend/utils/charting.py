from typing import Any, Dict, List, Optional
import pandas as pd

def _is_numeric_series(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)

def suggest_chart(df: pd.DataFrame) -> Optional[Dict[str, str]]:
    if df is None or df.empty:
        return None

    cols = list(df.columns)
    if len(cols) < 2:
        return None

    numeric_cols = [c for c in cols if _is_numeric_series(df[c])]
    non_numeric_cols = [c for c in cols if c not in numeric_cols]
    time_cols = [c for c in cols if any(k in c.lower() for k in ["date", "time", "year"])]

    if time_cols and numeric_cols:
        return {"chart_type": "line", "x": time_cols[0], "y": numeric_cols[0]}
    if non_numeric_cols and numeric_cols:
        return {"chart_type": "bar", "x": non_numeric_cols[0], "y": numeric_cols[0]}
    if len(numeric_cols) >= 2:
        return {"chart_type": "line", "x": numeric_cols[0], "y": numeric_cols[1]}
    return None
