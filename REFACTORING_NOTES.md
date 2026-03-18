# Manufacturing BI Copilot — Refactoring Notes

## What Changed & Why

### 1. Removed: `backend/eval/` directory
The entire evaluation harness (dataset splits, EA/ASEM/VA/F1/Pass@k metrics,
schema-drift runner, safety evaluator) has been deleted. These were research
artefacts that added zero value in production and blocked every request with
unnecessary imports and heavy dependencies (`sklearn`, `numpy` stats loops).

**Deleted files:**
- `backend/eval/dataset.py`
- `backend/eval/metrics.py`
- `backend/eval/run_eval.py`
- `backend/eval/safety_eval.py`
- `backend/eval/schema_drift.py`

---

### 2. Simplified: `backend/agent/graph.py`
**Before:** 8 nodes, conditional retry loop, `increment_retry`, `should_retry`.  
**After:** 6 nodes, straight pipeline — no conditional edges, no retry counter.

```
ingest_question → fast_path_sql → guardrail → execute_sql → suggest_chart → explain_answer → END
```

The self-correction loop added 1–2 extra LLM round-trips on failures. In
production the manufacturing prompt is high-quality enough that first-pass
accuracy is acceptable. Failures surface as clean error messages instead.

---

### 3. Schema caching: `backend/agent/nodes.py`
**Before:** `inspect_schema` node called `SQLDatabase.get_table_info()` on
every single request — a DB round-trip for every query.

**After:** `_get_cached_schema()` fetches the schema **once** at startup
(via `warm_schema_cache()` in the FastAPI lifespan) and stores it in a
module-level variable `_SCHEMA_CACHE`. All subsequent calls are instant
in-memory reads.

**Savings:** ~20–80 ms per request depending on DB location.

---

### 4. Manufacturing system prompt
The generic BI prompt has been replaced with a domain-specific one focused on:
- **OEE** (Overall Equipment Effectiveness)
- **Machine downtime** (MTBF, MTTR, planned vs unplanned)
- **Inventory levels** (raw materials, WIP, finished goods, reorder alerts)
- **Order fulfillment** (on-time delivery rate, lead time, backlog)
- **Shift / line / cell throughput and yield**

Key rule added: *always write time-series queries for trend questions* —
this ensures Production line charts render correctly without extra prompting.

---

### 5. Concise `explain_answer`
**Before:** "Explain in 2–3 short sentences …" — 2 LLM sentences + overhead.  
**After:** "In ONE concise sentence (max 20 words) …" — single sentence, lower
token count, ~30–50 % less final-hop latency.

---

### 6. Cleaned up `backend/app.py`
**Removed endpoints:**
- `POST /agent/evaluate`
- `POST /agent/schema_drift_eval`
- `POST /agent/safety_eval`

**Added:**
- FastAPI `lifespan` context manager that calls `warm_schema_cache()` at
  startup — schema is hot before the first real request arrives.
- `GET /health` liveness probe for load-balancers / Railway / K8s.
- Simplified `NLQueryResponse` — no `candidates` list (only the chosen result).

---

### 7. Simplified `backend/config.py`
Removed eval-only variables: `DRIFT_DATABASE_URL`, `DATASET_PATH`,
`EVAL_TOP_K`, `EVAL_TAU_ATOL`, `EVAL_TAU_RTOL`.

---

### 8. Refactored `frontend/src/App.jsx`
- Removed Evaluate / Schema Drift / Safety Check buttons.
- Updated to use the new `result` field (single object, not `candidates` list).
- Added quick-pick manufacturing question buttons.
- Added safety-blocked warning banner.
- SQL shown in a collapsible `<details>` block (cleaner UX).

---

## Performance Summary

| Optimisation              | Latency saved (est.) |
|---------------------------|----------------------|
| Schema cache (no DB call) | 20–80 ms / request   |
| Single SQL vs top-3       | 1–2 × LLM round-trip |
| No retry loop             | 0–2 × LLM round-trip |
| 1-sentence explain        | ~30–50 % last hop    |

---

## Running the refactored app

```bash
# Backend
uvicorn backend.app:app --reload

# Frontend
cd frontend && npm run dev
```

Environment variables required (`.env` in `backend/`):
```
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini   # or gpt-4o-mini for lower cost
```
