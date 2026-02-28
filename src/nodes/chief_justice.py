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


    rubric = state.get("rubric", {})
    opinions_raw = state.get("judicial_opinions", [])
    errors: list[str] = list(state.get("errors", []))
    return {
        "rubric": rubric,
        "judicial_opinions": opinions_raw,
        "errors": errors
    }
