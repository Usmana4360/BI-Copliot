from typing import Tuple, List
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from backend.config import DATABASE_URL, DRIFT_DATABASE_URL

_engine: Engine = None
_drift_engine: Engine = None

def get_engine(drift: bool = False) -> Engine:
    global _engine, _drift_engine
    if drift:
        if _drift_engine is None:
            _drift_engine = create_engine(DRIFT_DATABASE_URL)
        return _drift_engine
    else:
        if _engine is None:
            _engine = create_engine(DATABASE_URL)
        return _engine

def run_sql(engine: Engine, sql: str) -> Tuple[List[str], List[list]]:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        rows = result.fetchall()
        cols = result.keys()
    return list(cols), [list(r) for r in rows]

def run_sql_df(engine: Engine, sql: str) -> pd.DataFrame:
    cols, rows = run_sql(engine, sql)
    return pd.DataFrame(rows, columns=cols)
