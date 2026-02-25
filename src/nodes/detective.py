from __future__ import annotations


from typing import Any, cast
from src.state import AgentState
from src.tools.repo_tools import (
    is_repository_url,
    clone_repository,
    read_project_files,
)
from src.tools.doc_tools import parse_audit_pdf



# Detective node for repository/code evidence
def detective_repo_node(state: AgentState) -> AgentState:
    """Detective node for repository/code evidence."""
    state_data = cast(dict[str, Any], state)
    errors: list[str] = list(state_data.get("errors", []))

    repository_path = str(state_data.get("repository_path", "")).strip()
    resolved_repository_path = repository_path

    if repository_path and is_repository_url(repository_path):
        try:
            resolved_repository_path = clone_repository.invoke({"url": repository_path})
            state_data["repository_path"] = resolved_repository_path
        except Exception as exc:
            errors.append(f"Failed to clone repository '{repository_path}': {exc}")

    if resolved_repository_path:
        try:
            project_files = read_project_files.invoke({"repository_path": resolved_repository_path})
            existing_evidence = state_data.get("evidence", {})
            if isinstance(existing_evidence, dict):
                state_data["evidence"] = existing_evidence | project_files
            else:
                state_data["evidence"] = project_files
        except Exception as exc:
            errors.append(f"Failed to read repository files from '{resolved_repository_path}': {exc}")
    else:
        errors.append("No repository_path was provided for evidence collection")

    if errors:
        state_data["errors"] = errors

    return cast(AgentState, state_data)


# Detective node for document (PDF) evidence
def detective_doc_node(state: AgentState) -> AgentState:
    """Detective node for document (PDF) evidence."""
    state_data = cast(dict[str, Any], state)
    errors: list[str] = list(state_data.get("errors", []))

    pdf_state_keys = ("pdf_path", "audit_report_path", "audit_report_pdf_path")
    pdf_path = next((str(state_data.get(key, "")).strip() for key in pdf_state_keys if state_data.get(key)), "")
    if pdf_path:
        try:
            state_data["audit_report_text"] = parse_audit_pdf.invoke({"pdf_path": pdf_path})
        except Exception as exc:
            errors.append(f"Failed to parse audit PDF '{pdf_path}': {exc}")

    if errors:
        state_data["errors"] = errors

    return cast(AgentState, state_data)


# Detective node for vision/image evidence (stub)
def detective_vision_node(state: AgentState) -> AgentState:
    """Detective node for vision/image evidence (stub)."""
    # Placeholder: implement vision/image extraction logic as needed
    return state
