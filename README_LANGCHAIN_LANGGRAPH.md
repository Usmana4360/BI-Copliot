# BI Copilot Agent (LangChain + LangGraph + OpenAI)

This project implements an **agentic BI Copilot** that:

- Accepts **natural language questions**
- Uses **LangChain + LangGraph + OpenAI** to generate **k SQL candidates**
- Applies **guardrails** to block dangerous queries
- Executes SQL on **PostgreSQL**
- Ranks candidates, returns the best result and a suggested **chart**
- Provides an **evaluation harness** implementing metrics:
  - Execution Accuracy (EA)
  - Answer Set Exact Match (ASEM)
  - Value Accuracy @ τ (VA@τ)
  - Set-F1
  - Pass@k
  - Latency (TFT/TFR)
  - Robustness (schema drift)
  - Safety (Guardrail Rate)

See backend/README or code comments for details.

uvicorn backend.app:app --reload
uvicorn app:app --reload
