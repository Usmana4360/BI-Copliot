from fastapi.middleware.cors import CORSMiddleware
from backend.auth.router import router as auth_router, get_current_user
from fastapi import Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from backend.kpis.router import router as kpi_router
from fastapi.responses import JSONResponse
import asyncio

import os
from dotenv import load_dotenv

limiter = Limiter(key_func=get_remote_address)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from backend.utils.logging_config import setup_logging
from backend.utils.db import get_engine, run_sql
from backend.agent.runner import run_agent
from backend.agent.nodes import warm_schema_cache
from backend.config import OPENAI_API_KEY, OPENAI_MODEL

setup_logging()
logger = logging.getLogger("bi_copilot")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Startup: warming schema cache …")
    try:
        warm_schema_cache()
        logger.info("Startup: schema cache ready.")
    except Exception as exc:
        logger.error("Startup: schema cache warm-up failed: %s", exc)
    yield
    logger.info("Shutdown: cleaning up.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Manufacturing BI Copilot",
    description="Natural language → SQL for manufacturing operations.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(kpi_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class NLQueryRequest(BaseModel):
    question: str


class SQLResultItem(BaseModel):
    sql: str
    success: bool
    error: Optional[str] = None
    latency_ms: float = 0.0
    columns: List[str] = []
    preview_rows: List[List[Any]] = []


class NLQueryResponse(BaseModel):
    question: str
    chosen_sql: Optional[str]
    result: Optional[SQLResultItem]
    chart: Optional[Dict[str, Any]]
    tft_ms: float
    tfr_ms: float
    total_latency_ms: float
    explanation: Optional[str]
    safety_blocked: bool = False


# ---------------------------------------------------------------------------
# Query log helper
# ---------------------------------------------------------------------------

def _save_query_log(
    user_email: str,
    question: str,
    state: dict,
    result_item: Optional[SQLResultItem],
) -> None:
    """
    Persist every nl2sql call to query_logs.
    Failures here are caught and logged — never allowed to break the API response.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO query_logs (
                        user_email, question, chosen_sql,
                        success, error,
                        tft_ms, tfr_ms, total_latency_ms,
                        safety_blocked, retried
                    ) VALUES (
                        :email, :question, :sql,
                        :success, :error,
                        :tft, :tfr, :total,
                        :safety_blocked, :retried
                    )
                """),
                {
                    "email":         user_email,
                    "question":      question,
                    "sql":           state.get("chosen_sql"),
                    "success":       result_item.success if result_item else False,
                    "error":         result_item.error if result_item else None,
                    "tft":           state.get("tft_ms", 0.0),
                    "tfr":           state.get("tfr_ms", 0.0),
                    "total":         state.get("metadata", {}).get("total_latency_ms", 0.0),
                    "safety_blocked": state.get("safety_flags", {}).get("blocked", False),
                    "retried":       state.get("retry_count", 0) > 0,
                },
            )
            conn.commit()
            logger.info("Query log saved for user: %s", user_email)
    except Exception as exc:
        # Never crash the request because of a logging failure
        logger.error("Failed to save query log: %s", exc)


# ---------------------------------------------------------------------------
# Core endpoint
# ---------------------------------------------------------------------------

@app.post("/agent/nl2sql", response_model=NLQueryResponse)
@limiter.limit("20/minute")
async def nl2sql(
    request: Request,
    req: NLQueryRequest,
    current_user: dict = Depends(get_current_user),
):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    state = await asyncio.to_thread(run_agent, question=req.question)

    executed = state.get("executed_results", [])
    result_item = None
    if executed:
        r = executed[0]
        result_item = SQLResultItem(
            sql=r.get("sql", ""),
            success=r.get("success", False),
            error=r.get("error"),
            latency_ms=r.get("latency_ms", 0.0),
            columns=r.get("columns", []),
            preview_rows=r.get("preview_rows", []),
        )

    # ✅ Save to query_logs — runs after response is built, never blocks it
    _save_query_log(
        user_email=current_user if isinstance(current_user, str) else current_user.get("email", "unknown"),
        question=req.question,
        state=state,
        result_item=result_item,
    )

    return NLQueryResponse(
        question=req.question,
        chosen_sql=state.get("chosen_sql"),
        result=result_item,
        chart=state.get("chart_spec"),
        tft_ms=state.get("tft_ms", 0.0),
        tfr_ms=state.get("tfr_ms", 0.0),
        total_latency_ms=state.get("metadata", {}).get("total_latency_ms", 0.0),
        explanation=state.get("metadata", {}).get("explanation"),
        safety_blocked=state.get("safety_flags", {}).get("blocked", False),
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )