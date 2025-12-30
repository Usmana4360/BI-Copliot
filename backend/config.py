import os
# from dotenv import load_dotenv
# load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:1234@localhost:5432/maintenance",
)

DRIFT_DATABASE_URL = os.getenv(
    "DRIFT_DATABASE_URL",
    DATABASE_URL,
)

DATASET_PATH = os.getenv(
    "DATASET_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "nl_sql_all_100.csv"),
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

EVAL_TOP_K = int(os.getenv("EVAL_TOP_K", "3"))
EVAL_TAU_ATOL = float(os.getenv("EVAL_TAU_ATOL", "1e-6"))
EVAL_TAU_RTOL = float(os.getenv("EVAL_TAU_RTOL", "1e-3"))
