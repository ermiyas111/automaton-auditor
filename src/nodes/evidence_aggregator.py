
from typing import Any, cast
from src.state import AgentState, Evidence


def evidence_aggregator_node(state: AgentState) -> AgentState:
    """
    Aggregates evidence from all detective nodes into the structured Evidence state.
    Merges repo_files, doc_text, and vision_data if present in state.
    """
    state_data = cast(dict[str, Any], state)
    evidence: Evidence = {}


    # Always treat evidence as a dict, never as a string
    existing_evidence = state_data.get("evidence", {})
    if not isinstance(existing_evidence, dict):
        existing_evidence = {}

    # Merge repo_files
    repo_files = existing_evidence.get("repo_files")
    if repo_files:
        evidence["repo_files"] = repo_files

    # Merge doc_text
    doc_text = state_data.get("audit_report_text") or existing_evidence.get("doc_text")
    if doc_text:
        evidence["doc_text"] = doc_text

    # Merge vision_data
    vision_data = existing_evidence.get("vision_data")
    if vision_data:
        evidence["vision_data"] = vision_data

    state_data["evidence"] = evidence
    return cast(AgentState, state_data)
