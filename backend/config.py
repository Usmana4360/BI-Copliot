"""
config.py — Environment-based configuration for Manufacturing BI Copilot.

Removed from original:
  - DRIFT_DATABASE_URL   (no schema-drift eval)
  - DATASET_PATH         (no eval dataset)
  - EVAL_TOP_K           (no top-k candidate generation)
  - EVAL_TAU_ATOL/RTOL   (no value-accuracy metric)
"""

import os

# Database
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:1234@localhost:5432/maintenance",
)

# OpenAI
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
