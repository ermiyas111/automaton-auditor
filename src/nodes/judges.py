from __future__ import annotations

from typing import Any, cast



from src.state import AgentState, JudicialOpinion


MAX_FILES_FOR_PROMPT = 30
MAX_CHARS_PER_FILE = 2500
MAX_AUDIT_REPORT_CHARS = 12000


def _format_evidence_for_prompt(evidence: dict[str, Any]) -> str:
    if not evidence:
        return ""

    chunks: list[str] = []
    for filename, content in list(evidence.items())[:MAX_FILES_FOR_PROMPT]:
        if isinstance(content, str):
            snippet = content[:MAX_CHARS_PER_FILE]
        else:
            snippet = str(content)[:MAX_CHARS_PER_FILE]
        chunks.append(f"### FILE: {filename}\n{snippet}")
    return "\n\n".join(chunks)



# Helper to extract rubric sections
def extract_rubric_sections(rubric, section_names):
    if not rubric or "dimensions" not in rubric:
        return []
    return [d for d in rubric["dimensions"] if d["name"] in section_names]

# Shared judge logic
def judge_node(state: AgentState, persona: str, focus_sections: list[str]) -> dict:
    state_data = cast(dict[str, Any], state)
    rubric = state_data.get("rubric", {})
    evidence_list = state_data.get("evidence_list", [])
    audit_report_text = state_data.get("audit_report_text", "")
    # Extract relevant rubric sections
    relevant_sections = extract_rubric_sections(rubric, focus_sections)
    # Compose rationale and score (mock logic, replace with LLM call)
    cited_files = []
    rationale = []
    total_score = 0
    for section in relevant_sections:
        # Example: look for evidence that matches rubric
        section_score = 4  # Placeholder: real logic/LLM would analyze evidence_list
        total_score += section_score
        rationale.append(f"Assessed {section['name']}: {section['success_pattern']}")
        # Optionally cite files (mock)
        if evidence_list:
            cited_files.append(evidence_list[0].raw_data.keys())
    avg_score = total_score // len(relevant_sections) if relevant_sections else 1
    opinion = JudicialOpinion(
        persona=persona,
        score=avg_score,
        rationale="\n".join(rationale),
        cited_files=list(set([f for sublist in cited_files for f in sublist])) if cited_files else [],
    )
    return {"judicial_opinions": [opinion.model_dump()]}


def prosecutor_node(state: AgentState) -> dict:
    # Focus on 'Security' and 'Vulnerability' rubric sections
    return judge_node(state, "Prosecutor", ["Security", "Vulnerability"])


def defense_node(state: AgentState) -> dict:
    # Focus on 'Architecture' and 'Design Intent' rubric sections
    return judge_node(state, "Defense", ["Architecture", "Design Intent"])


def tech_lead_node(state: AgentState) -> dict:
    # Focus on 'Code Quality', 'Type Hinting', and 'State Management' rubric sections
    return judge_node(state, "TechLead", ["Code Quality", "Type Hinting", "State Management"])
