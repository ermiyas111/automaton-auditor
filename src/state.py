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

class Evidence(TypedDict, total=False):
    repo_files: Annotated[dict[str, Any], operator.ior]  # Merge dicts from parallel detectives
    doc_text: Annotated[str, operator.or_]               # Prefer non-null, or latest non-empty
    vision_data: Annotated[Any, operator.or_]            # Prefer non-null, or latest non-empty
    # Add more fields as needed for other evidence types


class AgentState(TypedDict):
    """State container for LangGraph nodes in the Digital Courtroom workflow.

    `operator.ior` on `evidence` enables dictionary merges from multiple agents,
    while `operator.add` on `judicial_opinions` preserves all parallel findings.
    """

    task_description: str
    repository_path: str
    audit_report_text: str
    evidence: Annotated[Evidence, operator.ior]
    judicial_opinions: Annotated[list[dict[str, Any]], operator.add]
    final_verdict: str
