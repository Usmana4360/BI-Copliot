import re
from typing import Tuple, List

DANGEROUS_PATTERNS = [
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
]

def check_sql_safety(sql: str) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    upper = sql.upper()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, upper):
            reasons.append(f"Matched dangerous pattern: {pattern}")
    return (len(reasons) == 0, reasons)
