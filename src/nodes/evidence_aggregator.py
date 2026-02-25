
from typing import Any, cast
from src.state import AgentState, Evidence


def evidence_aggregator_node(state: AgentState) -> AgentState:
    """
    Aggregates evidence from all detective nodes into the structured Evidence state.
    Merges repo_files, doc_text, and vision_data if present in state.
    """
    state_data = cast(dict[str, Any], state)
    evidence: Evidence = {}

    # Collect repo_files from evidence or legacy evidence
    repo_files = None
    if "evidence" in state_data and isinstance(state_data["evidence"], dict):
        maybe_repo = state_data["evidence"].get("repo_files")
        if maybe_repo:
            repo_files = maybe_repo
        # Backward compatibility: if code files are at top level
        if not repo_files:
            # Heuristic: if there are .py or .js keys, treat as repo_files
            file_keys = [k for k in state_data["evidence"].keys() if isinstance(k, str) and (k.endswith(".py") or k.endswith(".js"))]
            if file_keys:
                repo_files = {k: state_data["evidence"][k] for k in file_keys}
    if repo_files:
        evidence["repo_files"] = repo_files

    # Collect doc_text from audit_report_text or evidence
    doc_text = state_data.get("audit_report_text")
    if not doc_text and "evidence" in state_data and isinstance(state_data["evidence"], dict):
        doc_text = state_data["evidence"].get("doc_text")
    if doc_text:
        evidence["doc_text"] = doc_text

    # Collect vision_data if present
    vision_data = None
    if "evidence" in state_data and isinstance(state_data["evidence"], dict):
        vision_data = state_data["evidence"].get("vision_data")
    if vision_data:
        evidence["vision_data"] = vision_data

    state_data["evidence"] = evidence
    return cast(AgentState, state_data)
