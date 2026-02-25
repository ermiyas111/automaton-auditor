from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.detective import detective_repo_node, detective_doc_node, detective_vision_node
from src.nodes.evidence_aggregator import evidence_aggregator_node
from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.chief_justice import chief_justice_node
from src.nodes.quality_assurance import should_continue, quality_assurance_node

# Markdown rendering node for the final report
def render_markdown_report(state: AgentState) -> AgentState:
    """Render the final verdict and opinions as a Markdown report."""
    verdict = state.get("final_verdict", "No verdict.")
    opinions = state.get("judicial_opinions", [])
    report = f"# Audit Report\n\n**Final Verdict:** {verdict}\n\n## Judicial Opinions\n"
    for op in opinions:
        persona = op.get("persona", "Unknown")
        score = op.get("score", "?")
        rationale = op.get("rationale", "")
        cited = ', '.join(op.get("cited_files", []))
        report += f"\n### {persona}\n- **Score:** {score}\n- **Rationale:** {rationale}\n- **Cited Files:** {cited}\n"
    state["markdown_report"] = report
    return state

def build_graph():
    workflow = StateGraph(AgentState)
    # Parallel fan-out: Detectives
    workflow.add_node("detective_repo", detective_repo_node)
    # workflow.add_node("detective_doc", detective_doc_node)
    # workflow.add_node("detective_vision", detective_vision_node)
    # Fan-in: EvidenceAggregator
    workflow.add_node("evidence_aggregator", evidence_aggregator_node)
    # Parallel fan-out: Judges
    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("defense", defense_node)
    workflow.add_node("tech_lead", tech_lead_node)
    # Fan-in: ChiefJustice
    workflow.add_node("chief_justice", chief_justice_node)
    # QA and router
    workflow.add_node("quality_assurance", quality_assurance_node)
    workflow.add_node("router", should_continue)
    # Final Markdown rendering
    workflow.add_node("render_markdown_report", render_markdown_report)

    # Start: fan-out to all detectives
    workflow.add_edge(START, "detective_repo")
    # workflow.add_edge(START, "detective_doc")
    # workflow.add_edge(START, "detective_vision")
    # Fan-in: all detectives to evidence aggregator
    workflow.add_edge("detective_repo", "evidence_aggregator")
    # workflow.add_edge("detective_doc", "evidence_aggregator")
    # workflow.add_edge("detective_vision", "evidence_aggregator")
    # Fan-out: evidence aggregator to all judges
    workflow.add_edge("evidence_aggregator", "prosecutor")
    workflow.add_edge("evidence_aggregator", "defense")
    workflow.add_edge("evidence_aggregator", "tech_lead")
    # Fan-in: all judges to chief justice
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")
    # Router for error handling, appeals, QA
    workflow.add_edge("chief_justice", "router")
    workflow.add_conditional_edges(
        "router",
        {
            "detective": lambda state: {
                "detective_repo": state,
                "detective_doc": state,
                "detective_vision": state,
            },
            "quality_assurance": lambda state: {"quality_assurance": state},
        },
    )
    # Default: router to Markdown rendering
    workflow.add_edge("router", "render_markdown_report")
    workflow.add_edge("quality_assurance", "render_markdown_report")
    workflow.add_edge("render_markdown_report", END)
    return workflow.compile()
