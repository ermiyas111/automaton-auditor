from __future__ import annotations


from typing import Any, cast
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os



from src.state import AgentState, JudicialOpinion, CriterionAssessment


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

# Helper to extract all rubric criteria
def extract_rubric_criteria(rubric):
    if not rubric or "dimensions" not in rubric:
        return []
    return rubric["dimensions"]

# Shared judge logic


def judge_node(state: AgentState, persona: str) -> dict:
    print(f"--- {persona} is evaluating ---")
    import json
    rubric_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "rubric.json")
    with open(rubric_path, "r", encoding="utf-8") as f:
        rubric = json.load(f)
    unified_forensics = state.get("unified_forensics", "")
    unified_forensics = state.get("unified_forensics", {})
    rubric_criteria = extract_rubric_criteria(rubric)
    if not rubric_criteria:
        return {"judicial_opinions": [JudicialOpinion(
            persona=persona,
            assessments=[],
            overall_summary="No rubric criteria found."
        ).model_dump()]}

    persona_instructions = {
        "Prosecutor": "Be extremely strict, adversarial, and focus on finding flaws, especially security and vulnerability issues. For each criterion, cite specific evidence or files that support your score. If a security flaw is found, explain it in detail. Keep each rationale concise (1-2 sentences).",
        "Defense": "Be balanced, reward effort, intent, and creative workarounds, but do not ignore critical flaws. For each criterion, highlight positive intent and creative solutions, but be honest about any shortcomings. Keep each rationale concise (1-2 sentences).",
        "TechLead": "Be pragmatic, focus on architectural soundness, maintainability, and practical viability. For each criterion, assess how the architecture supports long-term success and practical use. Keep each rationale concise (1-2 sentences).",
    }
    persona_instruction = persona_instructions.get(persona, "Be fair and thorough.")

    # Compose a prompt for the LLM to produce a list of CriterionAssessment for each rubric criterion
    criteria_descriptions = "\n".join([
        f"- {c['name']} (id: {c['id']}): Success: {c['success_pattern']} | Failure: {c['failure_pattern']}" for c in rubric_criteria
    ])

    system_prompt = (
        f"You are the {persona} for a Technical Audit. Your task is to grade the project on EVERY rubric criterion below.\n"
        f"Rubric Criteria:\n{criteria_descriptions}\n"
        f"Forensic Brief: {unified_forensics}\n"
        f"Instructions: {persona_instruction} For each criterion, respond with a JSON object: {{'criterion_id': str, 'criterion_name': str, 'score': int (1-5), 'rationale': str}}. After all criteria, provide an overall_summary string that synthesizes your findings. Respond in JSON: {{'assessments': [CriterionAssessment...], 'overall_summary': str}}."
    )

    api_key = os.environ.get("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

    try:
        # Use the LLM to generate the full JudicialOpinion (assessments + summary)
        response = llm.invoke(system_prompt)
        # Try to parse the response as a JudicialOpinion
        content = getattr(response, 'content', None)
        import json, re
        if isinstance(content, str) and content.strip():
            # Remove markdown code block if present
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
            if match:
                json_str = match.group(1)
            else:
                json_str = content
            try:
                result = json.loads(json_str)
            except Exception as e:
                print(f"Failed to parse JSON: {e}\nContent was: {json_str}")
                result = {}
        else:
            result = {}

        return {"judicial_opinions": state.get("judicial_opinions", []) + [{**result, "persona": persona}]}
    except Exception as e:
        return {"judicial_opinions": state.get("judicial_opinions", []) + [{"error": str(e), "persona": persona}]}




def prosecutor_node(state: AgentState) -> dict:
    return judge_node(state, "Prosecutor")




def defense_node(state: AgentState) -> dict:
    return judge_node(state, "Defense")




def tech_lead_node(state: AgentState) -> dict:
    return judge_node(state, "TechLead")
