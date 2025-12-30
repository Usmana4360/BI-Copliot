from typing import Dict, Any
import logging

from backend.eval.run_eval import run_full_evaluation

logger = logging.getLogger("bi_copilot")

def run_schema_drift_evaluation() -> Dict[str, Any]:
    logger.info("Running baseline evaluation (no drift)")
    base_metrics = run_full_evaluation(split="test")

    logger.info("Running drift evaluation (DRIFT_DATABASE_URL)")
    drift_metrics = run_full_evaluation(split="test")

    delta_asem = None
    if "answer_set_exact_match" in base_metrics and "answer_set_exact_match" in drift_metrics:
        delta_asem = base_metrics["answer_set_exact_match"] - drift_metrics["answer_set_exact_match"]

    return {
        "baseline": base_metrics,
        "drift": drift_metrics,
        "delta_asem": delta_asem,
    }
