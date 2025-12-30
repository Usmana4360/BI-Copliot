import time
import logging

from .state import AgentState
from .graph import build_graph

logger = logging.getLogger("bi_copilot")

_graph_cache = {}

def get_graph(top_k: int = 3):
    global _graph_cache
    if top_k not in _graph_cache:
        _graph_cache[top_k] = build_graph(top_k=top_k)
    return _graph_cache[top_k]

def run_agent(question: str, top_k: int = 3) -> AgentState:
    graph = get_graph(top_k=top_k)
    init_state: AgentState = {"question": question}
    start = time.time()
    final_state = graph.invoke(init_state)
    total_latency_ms = (time.time() - start) * 1000.0
    final_state.setdefault("metadata", {})
    final_state["metadata"]["total_latency_ms"] = total_latency_ms
    logger.info("Trace %s - run_agent total_latency_ms=%.2f", final_state.get("trace_id"), total_latency_ms)
    return final_state
