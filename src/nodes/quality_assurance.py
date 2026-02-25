from typing import Any, cast
from src.state import AgentState

def should_continue(state: AgentState) -> str:
    """
    Router node: decide next step after chief justice.
    Returns 'detective' to trigger appeal, 'quality_assurance' for QA, or END.
    """
    state_data = cast(dict[str, Any], state)
    # Example: if 'appeal' in state, trigger detectives again
    if state_data.get("appeal", False):
        return "detective"
    # Example: if 'qa_required' in state, trigger QA
    if state_data.get("qa_required", False):
        return "quality_assurance"
    # Default: end
    return "END"


def quality_assurance_node(state: AgentState) -> AgentState:
    """
    Quality assurance node: perform final checks or audits.
    Optionally update state with QA results.
    """
    state_data = cast(dict[str, Any], state)
    # Example: add QA status
    state_data["qa_status"] = "passed"
    return cast(AgentState, state_data)
