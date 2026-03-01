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
    import json
    import os
    from src.state import JudicialOpinion, CriterionAssessment

    # Load rubric from file
    rubric_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "rubric.json")
    with open(rubric_path, "r", encoding="utf-8") as f:
        rubric = json.load(f)
    rubric_criteria = rubric.get("dimensions", [])

    # Get opinions as list of JudicialOpinion
    opinions_raw = state.get("judicial_opinions", [])
    # Convert to JudicialOpinion objects if needed
    opinions = []
    for op in opinions_raw:
        if isinstance(op, dict):
            try:
                opinions.append(op)
            except Exception:
                continue

    # Build a mapping: criterion_id -> list of (persona, score, rationale)
    criterion_map = {c["id"]: {"name": c["name"], "assessments": []} for c in rubric_criteria}
    for op in opinions_raw:
        persona = op.get("persona", "")
        for assess in op.get("assessments", []):
            entry = criterion_map.get(assess.get("criterion_id"))
            if entry is not None:
                entry["assessments"].append({
                    "persona": persona,
                    "score": assess.get("score", 1),
                    "rationale": assess.get("rationale", "")
                })

    # Synthesis rules
    rules = rubric.get("synthesis_rules", {})
    def security_override(assessments):
        for a in assessments:
            if a["persona"].lower() == "prosecutor" and ("security" in a["rationale"].lower() or a["score"] <= 2):
                return True
        return False

    def score_stats(scores):
        return min(scores), max(scores), sum(scores)/len(scores) if scores else 0

    # Build markdown report
    lines = []
    # Executive Summary
    all_scores = []
    for entry in criterion_map.values():
        for a in entry["assessments"]:
            all_scores.append(a["score"])
    overall_score = sum(all_scores)/len(all_scores) if all_scores else 0
    lines.append(f"# Audit Report\n")
    lines.append(f"## Executive Summary\n")
    lines.append(f"Overall Score: {overall_score:.2f}/5.0. Criteria Evaluated: {len(criterion_map)}.\n")

    # Criterion Breakdown
    lines.append(f"## Criterion Breakdown\n")
    remediation_plan = []
    print(f"Processing {criterion_map} criteria for synthesis.")
    for crit in rubric_criteria:
        cid = crit["id"]
        entry = criterion_map[cid]
        print(f"Processing criterion: {cid} with {len(entry['assessments'])} assessments")
        name = entry["name"]
        print(f"Assessments for {name}: {entry['assessments']}")
        assessments = entry["assessments"]
        if not assessments:
            continue
        scores = [a["score"] for a in assessments]
        min_score, max_score, avg_score = score_stats(scores)
        # Synthesis: security override
        if security_override(assessments):
            final_score = min(3, avg_score)
        else:
            final_score = avg_score
        lines.append(f"\n### {name}\n**Final Score:** {round(final_score)}/5\n")
        # Judge Opinions
        lines.append(f"**Judge Opinions:**\n")
        for a in assessments:
            lines.append(f"- **{a['persona']}** (Score: {a['score']}): {a['rationale']}")
        # Dissent
        if max_score - min_score > 2:
            dissent = "Significant disagreement: " + ", ".join([f"{a['persona']}={a['score']}" for a in assessments])
            lines.append(f"**Dissent:** {dissent}")
        # Remediation
        lines.append(f"**Remediation:** {crit.get('failure_pattern','Review criterion requirements.')}\n---")
        remediation_plan.append((name, final_score, crit.get('failure_pattern','Review criterion requirements.')))

    # Prioritized Remediation Plan
    lines.append(f"\n## Remediation Plan\n")
    remediation_plan.sort(key=lambda x: x[1])
    for idx, (name, score, issue) in enumerate(remediation_plan, 1):
        lines.append(f"## Priority {idx}: {name} (Score: {round(score)}/5)\n✅ **Issue:** {issue}\n")

    import datetime
    report = "\n".join(lines)
    # Generate filename with pattern peer_grading_YEAR_MONTH_DAY_HH_MM_SS.md
    now = datetime.datetime.now()
    filename = f"peer_grading_{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}_{now.minute:02d}_{now.second:02d}.md"
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report)
    return {"markdown_report": report, "file_path": file_path}
