from typing import Any, cast
from src.state import AgentState

def expert_auditor_node(state: AgentState) -> AgentState:
    """
    Single expert auditor node: combines software architect and security auditor personas.
    Analyzes code evidence and audit_report_text, returns final score and issues.
    """
    state_data = cast(dict[str, Any], state)
    evidence = state_data.get("evidence", [])
    if not isinstance(evidence, list):
        evidence = [evidence] if evidence else []
    audit_report_text = state_data.get("audit_report_text", "")
    # System prompt for LLM (pseudo-code, replace with actual LLM call)
    system_prompt = (
        "You are a Senior Software Architect and Security Auditor. "
        "Analyze the provided code evidence against the claims in the PDF report. "
        "Identify hallucinations, security risks, and architectural flaws in one comprehensive pass."
    )
    # Pseudo-LLM call (replace with actual model call, e.g., GPT-4o)
    # result = call_llm(system_prompt, evidence, audit_report_text)
    # For demonstration, mock output:
    result = {
        "final_score": 4.5,
        "issues": [
            "No major hallucinations detected.",
            "Minor security risk in input validation.",
            "Architecture is modular but lacks async error handling."
        ]
    }
    state_data["audit_summary"] = result
    state_data["final_verdict"] = f"Score: {result['final_score']} | Issues: {len(result['issues'])}"
    return cast(AgentState, state_data)
