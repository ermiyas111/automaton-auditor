
from typing import Any, cast
from src.state import AgentState, Evidence


import logging
from typing import List, Dict, Any
from src.state import AgentState, Evidence

def evidence_aggregator_node(state: AgentState) -> Dict[str, Any]:
    evidence_list: List[Evidence] = state.get("evidence_list", [])
    sources = {ev.source for ev in evidence_list if hasattr(ev, 'source')}
    if "repository" not in sources:
        logging.warning("Sanity Check: No code evidence found in evidence_list.")
    if "pdf_report" not in sources:
        logging.warning("Sanity Check: No document evidence found in evidence_list.")
    # Optionally aggregate evidence
    aggregated = Evidence(
        source="aggregator",
        content_summary=f"Aggregated {len(evidence_list)} items.",
        raw_data={"sources": list(sources)},
        critical_findings=[ev.content_summary for ev in evidence_list],
    )
    return {"evidence_list": [aggregated]}
