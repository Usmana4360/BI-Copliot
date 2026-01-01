import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

import logging
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.utils.logging_config import setup_logging
from backend.agent.runner import run_agent
from backend.eval.run_eval import run_full_evaluation
from backend.eval.schema_drift import run_schema_drift_evaluation
from backend.eval.safety_eval import run_safety_evaluation
from backend.config import EVAL_TOP_K


logger = logging.getLogger("bi_copilot")

app = FastAPI(title="BI Copilot (LangChain + LangGraph)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_logging()

class NLQueryRequest(BaseModel):
    question: str
    top_k: int | None = None

class NLQueryResponse(BaseModel):
    question: str
    chosen_sql: str | None
    candidates: list
    chart: dict | None
    tft_ms: float
    tfr_ms: float
    total_latency_ms: float
    explanation: str | None

class EvalRequest(BaseModel):
    split: str = "test"
    top_k: int | None = None

class EvalResponse(BaseModel):
    metrics: Dict[str, Any]

class SchemaDriftResponse(BaseModel):
    baseline: Dict[str, Any]
    drift: Dict[str, Any]
    delta_asem: float | None

class SafetyEvalResponse(BaseModel):
    guardrail_rate: float
    total_dangerous: int
    blocked_dangerous: int
    examples: list

@app.post("/agent/nl2sql", response_model=NLQueryResponse)
def nl2sql(req: NLQueryRequest):
    top_k = req.top_k or EVAL_TOP_K
    state = run_agent(question=req.question, top_k=top_k)

    chosen_sql = state.get("chosen_sql")
    candidates = state.get("executed_results", [])
    chart = state.get("chart_spec")
    tft_ms = state.get("tft_ms", 0.0)
    tfr_ms = state.get("tfr_ms", 0.0)
    total_latency_ms = state.get("metadata", {}).get("total_latency_ms", 0.0)
    explanation = state.get("metadata", {}).get("explanation")

    return NLQueryResponse(
        question=req.question,
        chosen_sql=chosen_sql,
        candidates=candidates,
        chart=chart,
        tft_ms=tft_ms,
        tfr_ms=tfr_ms,
        total_latency_ms=total_latency_ms,
        explanation=explanation,
    )

@app.post("/agent/evaluate", response_model=EvalResponse)
def evaluate(req: EvalRequest):
    top_k = req.top_k or EVAL_TOP_K
    metrics = run_full_evaluation(split=req.split, top_k=top_k)
    return EvalResponse(metrics=metrics)

@app.post("/agent/schema_drift_eval", response_model=SchemaDriftResponse)
def schema_drift_eval():
    result = run_schema_drift_evaluation()
    return SchemaDriftResponse(
        baseline=result["baseline"],
        drift=result["drift"],
        delta_asem=result["delta_asem"],
    )

@app.post("/agent/safety_eval", response_model=SafetyEvalResponse)
def safety_eval():
    result = run_safety_evaluation()
    return SafetyEvalResponse(
        guardrail_rate=result["guardrail_rate"],
        total_dangerous=result["total_dangerous"],
        blocked_dangerous=result["blocked_dangerous"],
        examples=result["examples"],
    )

from openai import OpenAI
from backend.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

@app.get("/test_openai")
def test_openai():
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10,
        )

        return {
            "success": True,
            "reply": response.choices[0].message.content,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


from sqlalchemy import text
from sqlalchemy import create_engine, inspect
from backend.config import DATABASE_URL
@app.get("/debug/tables")
def debug_tables():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    return {
        "tables": inspector.get_table_names(schema="public")
    }

@app.get("/debug/sql")
def debug_sql():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM machines LIMIT 5"))
        return [dict(row._mapping) for row in result]
