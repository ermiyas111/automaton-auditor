
from typing import Any, cast
from src.state import AgentState, Evidence


import logging
from typing import List, Dict, Any
from src.state import AgentState, Evidence

def evidence_aggregator_node(state: AgentState) -> Dict[str, Any]:
    evidence_list: List[Evidence] = state.get("evidence_list", [])
    sources = {ev.source for ev in evidence_list if hasattr(ev, 'source')}
    repo_data = next((ev for ev in evidence_list if getattr(ev, 'source', None) == 'repository'), None)
    pdf_data = next((ev for ev in evidence_list if getattr(ev, 'source', None) == 'pdf_report'), None)

    # Unified protocol map
    unified_forensics = {}
    if repo_data:
        unified_forensics['git_narrative'] = repo_data.protocol_results.get('git_narrative')
        unified_forensics['graph_wiring'] = repo_data.protocol_results.get('graph_wiring')
        unified_forensics['state_structure'] = repo_data.protocol_results.get('state_structure')
        file_manifest = repo_data.raw_data.get('file_manifest', [])
    else:
        file_manifest = []
    if pdf_data:
        unified_forensics['citation_check'] = pdf_data.protocol_results.get('citation_check')
        unified_forensics['concept_evaluations'] = pdf_data.protocol_results.get('concept_evaluations')
        claimed_features = pdf_data.raw_data.get('claimed_features', [])
    else:
        claimed_features = []

    # Manifest comparison: Discrepancy List
    discrepancy_list = []
    if claimed_features and file_manifest:
        for feature in claimed_features:
            if isinstance(feature, str):
                feature_file = feature.strip()
                if feature_file and feature_file not in file_manifest:
                    discrepancy_list.append(feature_file)
    unified_forensics['discrepancy_list'] = discrepancy_list

    # Log the merge
    logger = logging.getLogger("evidence_aggregator")
    logger.info(f"Aggregator merged {len(evidence_list)} sources into unified forensic brief.")

    # Update state
    new_state = dict(state)
    new_state['unified_forensics'] = unified_forensics
    return new_state
