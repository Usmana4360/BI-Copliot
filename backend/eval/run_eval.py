from typing import Dict, Any
import numpy as np
import logging

from backend.agent.runner import run_agent
from backend.eval.dataset import make_splits
from backend.eval.metrics import (
    is_aggregate_query,
    fetch_result_df,
    answer_set_exact_match,
    value_accuracy_tau,
    set_f1,
    compute_latency_stats,
)
from backend.config import EVAL_TOP_K

logger = logging.getLogger("bi_copilot")

def run_full_evaluation(split: str = "test", top_k: int = EVAL_TOP_K) -> Dict[str, Any]:
    train_df, val_df, test_df = make_splits()
    df = {"train": train_df, "val": val_df, "test": test_df}[split]

    ea_flags = []
    asem_flags = []
    va_flags = []
    f1_scores = []
    passk_flags = []
    tft_list = []
    tfr_list = []

    for _, row in df.iterrows():
        question = row["nl"]
        gold_sql = row["sql"]
        is_agg = is_aggregate_query(gold_sql)

        df_gold, lat_gold, ok_gold, err_gold = fetch_result_df(gold_sql)
        if not ok_gold:
            logger.warning("Gold SQL failed, skipping: %s (%s)", gold_sql, err_gold)
            continue

        state = run_agent(question=question, top_k=top_k)

        executed = state.get("executed_results", [])
        tft_ms = state.get("tft_ms", 0.0)
        tfr_ms = state.get("tfr_ms", 0.0)
        if tft_ms:
            tft_list.append(tft_ms)
        if tfr_ms:
            tfr_list.append(tfr_ms)

        success_any = any(r.get("success") for r in executed)
        ea_flags.append(1 if success_any else 0)

        # Pass@k: any candidate yields exact match vs gold
        passk_success = False
        for r in executed:
            if not r.get("success"):
                continue
            cand_df, _, ok_cand, _ = fetch_result_df(r["sql"])
            if ok_cand and answer_set_exact_match(cand_df, df_gold):
                passk_success = True
                break
        passk_flags.append(1 if passk_success else 0)

        chosen_sql = state.get("chosen_sql")
        if chosen_sql:
            df_pred, _, ok_pred, _ = fetch_result_df(chosen_sql)
            if ok_pred:
                if is_agg:
                    va_flags.append(1 if value_accuracy_tau(df_pred, df_gold) else 0)
                else:
                    asem_flags.append(1 if answer_set_exact_match(df_pred, df_gold) else 0)
                    f1_scores.append(set_f1(df_pred, df_gold))

    metrics: Dict[str, Any] = {}
    if ea_flags:
        metrics["execution_accuracy"] = float(np.mean(ea_flags))
    if asem_flags:
        metrics["answer_set_exact_match"] = float(np.mean(asem_flags))
    if va_flags:
        metrics["value_accuracy_tau"] = float(np.mean(va_flags))
    if f1_scores:
        metrics["set_f1_mean"] = float(np.mean(f1_scores))
    if passk_flags:
        metrics["pass_at_k"] = float(np.mean(passk_flags))

    if tft_list:
        m = compute_latency_stats(tft_list)
        metrics["latency_tft_ms_median"] = m["median"]
        metrics["latency_tft_ms_p90"] = m["p90"]
    if tfr_list:
        m = compute_latency_stats(tfr_list)
        metrics["latency_tfr_ms_median"] = m["median"]
        metrics["latency_tfr_ms_p90"] = m["p90"]

    return metrics
