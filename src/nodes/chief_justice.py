from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore[import-not-found]
from pydantic import BaseModel, Field

from src.state import AgentState


PERSONA_WEIGHTS: dict[str, float] = {
    "the cynic": 0.45,
    "the advocate": 0.2,
    "the architect": 0.35,
}


class ChiefJusticeSynthesis(BaseModel):
    executive_summary: str = Field(description="A concise Pass/Fail/Needs Improvement summary.")
    conflict_resolution: str = Field(description="How conflicting judicial opinions were reconciled.")
    actionable_remediation: list[str] = Field(description="Top 3 immediate fixes for the developer.")


def _normalize_score(raw_score: Any) -> int:
    try:
        numeric = int(raw_score)
    except (TypeError, ValueError):
        return 1
    return max(1, min(5, numeric))


def _weighted_score(opinions: list[dict[str, Any]]) -> float:
    total_weight = 0.0
    weighted_total = 0.0

    for opinion in opinions:
        persona = str(opinion.get("persona", "")).strip().lower()
        weight = PERSONA_WEIGHTS.get(persona, 1.0)
        score = _normalize_score(opinion.get("score", 1))
        weighted_total += score * weight
        total_weight += weight

    if total_weight == 0:
        return 1.0
    return weighted_total / total_weight


def _has_critical_security_flag(opinions: list[dict[str, Any]]) -> bool:
    for opinion in opinions:
        score = _normalize_score(opinion.get("score", 1))
        rationale = str(opinion.get("rationale", "")).lower()
        if score != 1:
            continue
        if "critical" in rationale and any(
            keyword in rationale
            for keyword in (
                "security",
                "sql injection",
                "os.system",
                "command injection",
                "secret",
                "api key",
            )
        ):
            return True
    return False


def _status_from_score(final_score: float) -> str:
    if final_score >= 4.0:
        return "Pass"
    if final_score >= 2.5:
        return "Needs Improvement"
    return "Fail"


def chief_justice_node(state: AgentState) -> dict[str, Any]:
    """Synthesize judge opinions into a final executive verdict markdown report."""

    state_data = dict(state)
    errors: list[str] = list(state_data.get("errors", []))
    opinions_raw = state_data.get("judicial_opinions", [])

    opinions: list[dict[str, Any]] = []
    if isinstance(opinions_raw, list):
        opinions = [item for item in opinions_raw if isinstance(item, dict)]

    if not opinions:
        errors.append("Chief Justice could not generate a ruling: no judicial_opinions were provided.")
        fallback_report = (
            "# Supreme Court Verdict\n\n"
            "## Executive Summary\n"
            "Fail — No judicial opinions were available to review.\n\n"
            "## The Balanced Score\n"
            "1.00 / 5.00\n\n"
            "## Conflict Resolution\n"
            "No conflict resolution was possible because the Prosecution, Defense, and Technical Lead opinions were missing.\n\n"
            "## Actionable Remediation\n"
            "- Ensure Prosecutor, Defense, and Tech Lead nodes execute successfully.\n"
            "- Confirm reducer wiring for `judicial_opinions` uses `operator.add`.\n"
            "- Re-run the workflow and verify each persona contributes one opinion.\n"
        )
        return {"final_verdict": fallback_report, "errors": errors}

    computed_score = _weighted_score(opinions)
    if _has_critical_security_flag(opinions):
        computed_score = min(computed_score, 2.0)

    final_score = max(1.0, min(5.0, round(computed_score, 2)))
    status = _status_from_score(final_score)

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
    structured_llm = llm.with_structured_output(ChiefJusticeSynthesis)

    system_prompt = (
        "You are the Chief Justice. Review the attached Prosecution, Defense, and Technical Lead opinions. "
        "Resolve their contradictions and write a final executive verdict."
    )

    human_prompt = (
        f"Task Description:\n{state_data.get('task_description', '')}\n\n"
        f"Judicial Opinions:\n{opinions}\n\n"
        "Write concise output with:\n"
        "1) executive_summary (must be one of: Pass, Needs Improvement, Fail, plus one sentence),\n"
        "2) conflict_resolution (explain key tradeoffs and why one side is more compelling where applicable),\n"
        "3) actionable_remediation (exactly 3 bullet-worthy items, concrete and immediate).\n"
        "Reference concrete concerns from the opinions and do not invent evidence."
    )

    try:
        synthesis = structured_llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]
        )
    except Exception as exc:
        errors.append(f"Chief Justice synthesis failed: {exc}")
        synthesis = ChiefJusticeSynthesis(
            executive_summary=f"{status} — Automated synthesis failed; score is based on weighted judicial inputs.",
            conflict_resolution=(
                "Conflicts could not be fully synthesized due to an LLM invocation error. "
                "Use the existing judicial opinions directly for manual adjudication."
            ),
            actionable_remediation=[
                "Resolve the LLM/service error and retry Chief Justice synthesis.",
                "Prioritize any score-1 findings in prosecution rationale.",
                "Re-run end-to-end after fixes and compare score deltas.",
            ],
        )

    remediation_items = synthesis.actionable_remediation[:3]
    while len(remediation_items) < 3:
        remediation_items.append("Add a concrete remediation step tied to a cited judicial concern.")

    markdown_report = (
        "# Supreme Court Verdict\n\n"
        "## Executive Summary\n"
        f"{synthesis.executive_summary}\n"
        f"Overall Status: **{status}**\n\n"
        "## The Balanced Score\n"
        f"{final_score:.2f} / 5.00\n\n"
        "## Conflict Resolution\n"
        f"{synthesis.conflict_resolution}\n\n"
        "## Actionable Remediation\n"
        f"- {remediation_items[0]}\n"
        f"- {remediation_items[1]}\n"
        f"- {remediation_items[2]}\n"
    )

    if errors:
        return {"final_verdict": markdown_report, "errors": errors}
    return {"final_verdict": markdown_report}
