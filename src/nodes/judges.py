from __future__ import annotations


from typing import Any, cast
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os



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
    print(f"--- {persona} is evaluating ---")
    state_data = cast(dict[str, Any], state)
    rubric = state_data.get("rubric", {})
    evidence_list = state_data.get("evidence_list", [])
    audit_report_text = state_data.get("audit_report_text", "")
    relevant_sections = extract_rubric_sections(rubric, focus_sections)
    if not relevant_sections:
        return {"judicial_opinions": [JudicialOpinion(
            persona=persona,
            score=1,
            rationale="No relevant rubric section found.",
            cited_files=[],
        ).model_dump()]}

    # Prepare evidence context
    evidence_texts = []
    cited_files = set()
    for ev in evidence_list:
        if hasattr(ev, 'content_summary'):
            evidence_texts.append(ev.content_summary)
        if hasattr(ev, 'critical_findings'):
            evidence_texts.extend(ev.critical_findings)
        if hasattr(ev, 'raw_data') and isinstance(ev.raw_data, dict):
            cited_files.update(ev.raw_data.keys())
    evidence_text = "\n".join(evidence_texts)[:MAX_AUDIT_REPORT_CHARS]

    # Use only the first relevant rubric section for this persona
    rubric_section = relevant_sections[0]
    rubric_section_text = f"{rubric_section['name']}: {rubric_section['success_pattern']}\nFailure: {rubric_section['failure_pattern']}"

    # Persona-specific instructions
    persona_instructions = {
        "Prosecutor": "Be extremely strict, adversarial, and focus on finding flaws, especially security and vulnerability issues.",
        "Defense": "Be balanced, reward effort, intent, and creative workarounds, but do not ignore critical flaws.",
        "TechLead": "Be pragmatic, focus on architectural soundness, maintainability, and practical viability.",
    }
    persona_instruction = persona_instructions.get(persona, "Be fair and thorough.")

    system_prompt = (
        f"You are the {persona} for a Technical Audit. Your task is to grade the project based ONLY on the following rubric section: {rubric_section_text}\n"
        f"Evidence gathered from the repository and docs: {evidence_text}\n"
        f"Instructions: {persona_instruction} Cite specific files from the evidence. Respond in the following JSON format: {{'persona': str, 'score': int (1-5), 'rationale': str, 'cited_files': list[str]}}."
    )

    # Initialize Gemini LLM with structured output
    api_key = os.environ.get("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key).with_structured_output(JudicialOpinion)

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            # Optionally, add a HumanMessage if you want to allow user input
        ])
        # Validate output is a JudicialOpinion
        if isinstance(response, JudicialOpinion):
            return {"judicial_opinions": [response.model_dump()]}
        elif isinstance(response, dict):
            # Defensive: try to coerce
            return {"judicial_opinions": [JudicialOpinion(**response).model_dump()]}
        else:
            return {"judicial_opinions": [JudicialOpinion(
                persona=persona,
                score=1,
                rationale="LLM did not return a valid JudicialOpinion.",
                cited_files=list(cited_files),
            ).model_dump()]}
    except Exception as e:
        return {"judicial_opinions": [JudicialOpinion(
            persona=persona,
            score=1,
            rationale=f"LLM call failed: {e}",
            cited_files=list(cited_files),
        ).model_dump()]}



def prosecutor_node(state: AgentState) -> dict:
    # Focus on 'Security' and 'Vulnerability' rubric sections
    return judge_node(state, "Prosecutor", ["Security", "Vulnerability"])



def defense_node(state: AgentState) -> dict:
    # Focus on 'Architecture' and 'Design Intent' rubric sections
    return judge_node(state, "Defense", ["Architecture", "Design Intent"])



def tech_lead_node(state: AgentState) -> dict:
    # Focus on 'Code Quality', 'Type Hinting', and 'State Management' rubric sections
    return judge_node(state, "TechLead", ["Code Quality", "Type Hinting", "State Management"])
