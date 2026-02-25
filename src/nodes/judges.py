from __future__ import annotations

from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import-not-found]

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


def run_judge_persona(state: AgentState, persona_config: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """Run one judicial persona and return a reducer-friendly opinion payload."""

    state_data = cast(dict[str, Any], state)
    evidence = state_data.get("evidence", {})
    evidence_dict = evidence if isinstance(evidence, dict) else {}
    evidence_filenames = [str(name) for name in evidence_dict.keys()]

    persona_name = persona_config["persona"]
    system_directive = persona_config["system_prompt"]

    if not evidence_dict:
        no_evidence_opinion = JudicialOpinion(
            persona=persona_name,
            score=1,
            rationale="No Evidence Found: Detective layer returned an empty evidence dictionary, so no code-based judicial analysis is possible.",
            cited_files=[],
        )
        return {"judicial_opinions": [no_evidence_opinion.model_dump()]}

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    structured_llm = llm.with_structured_output(JudicialOpinion)

    audit_report_text = str(state_data.get("audit_report_text", ""))[:MAX_AUDIT_REPORT_CHARS]
    evidence_text = _format_evidence_for_prompt(evidence_dict)

    common_policy = (
        "You are a judge in the Automation Auditor Digital Courtroom. "
        "Return a valid JudicialOpinion object only. "
        "Use score from 1 to 5. "
        "Your rationale must explicitly mention concrete filenames from the evidence set. "
        "Set cited_files to only filenames that exist in the provided evidence. "
        "If evidence is insufficient for a claim, say so explicitly."
    )

    human_prompt = (
        f"Task Description:\n{state_data.get('task_description', '')}\n\n"
        f"Audit Report (PDF extracted text):\n{audit_report_text}\n\n"
        f"Evidence Filenames:\n{evidence_filenames}\n\n"
        f"Evidence Content Snippets:\n{evidence_text}\n"
    )

    opinion = structured_llm.invoke(
        [
            SystemMessage(content=f"{system_directive}\n\n{common_policy}"),
            HumanMessage(content=human_prompt),
        ]
    )

    valid_citations = [name for name in opinion.cited_files if name in evidence_filenames]
    if not valid_citations and evidence_filenames:
        valid_citations = evidence_filenames[:3]

    updated_rationale = opinion.rationale
    if valid_citations and not any(filename in updated_rationale for filename in valid_citations):
        updated_rationale = f"{updated_rationale}\n\nReferenced files: {', '.join(valid_citations)}"

    normalized_opinion = JudicialOpinion(
        persona=opinion.persona or persona_name,
        score=opinion.score,
        rationale=updated_rationale,
        cited_files=valid_citations,
    )
    return {"judicial_opinions": [normalized_opinion.model_dump()]}


def prosecutor_node(state: AgentState) -> dict[str, list[dict[str, Any]]]:
    persona_config = {
        "persona": "The Cynic",
        "system_prompt": (
            "The Cynic. Scrutinize for security risks like SQL injection and raw os.system calls, "
            "missing or weak tests, and hallucinated PDF claims that are not present in code."
        ),
    }
    return run_judge_persona(state, persona_config)


def defense_node(state: AgentState) -> dict[str, list[dict[str, Any]]]:
    persona_config = {
        "persona": "The Advocate",
        "system_prompt": (
            "The Advocate. Highlight strong library usage and clean abstractions, and explain why "
            "MVP shortcuts may have been practical under delivery constraints."
        ),
    }
    return run_judge_persona(state, persona_config)


def tech_lead_node(state: AgentState) -> dict[str, list[dict[str, Any]]]:
    persona_config = {
        "persona": "The Architect",
        "system_prompt": (
            "The Architect. Evaluate technical debt, type hint coverage, documentation quality, "
            "and whether StateGraph orchestration appears logically sound."
        ),
    }
    return run_judge_persona(state, persona_config)
