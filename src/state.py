"""Shared state and structured outputs for the Automation Auditor graph.

Reducer operators are attached to fan-out fields so parallel "Digital Courtroom"
agents can merge updates deterministically instead of overwriting one another.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, List, TypedDict

from pydantic import BaseModel, Field


class JudicialOpinion(BaseModel):
    """Structured opinion emitted by each courtroom persona."""

    persona: str
    score: int = Field(ge=1, le=5)
    rationale: str
    cited_files: List[str]



# Structured evidence container for aggregation and merging

# Reducers for Evidence fields
from typing import Annotated
import operator


# New Pydantic Evidence model for Detective Layer
class Evidence(BaseModel):
    source: str
    content_summary: str
    raw_data: dict
    critical_findings: List[str]
    protocol_results: dict = Field(default_factory=dict, description="Forensic protocol pass/fail and analysis flags.")


class AgentState(TypedDict):
    """State container for LangGraph nodes in the streamlined Expert Auditor workflow.

    `operator.add` on `evidence` enables aggregation of Evidence objects from parallel detectives.
    """

    task_description: str
    repository_path: str
    audit_report_text: str
    pdf_path: str
    evidence_list: Annotated[List[Evidence], operator.add]
    audit_summary: dict[str, Any]
    final_verdict: str
    judicial_opinions: Annotated[List[JudicialOpinion], operator.add]
    unified_forensics: dict
    formatted_brief: str
