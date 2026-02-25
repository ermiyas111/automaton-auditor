from langgraph.graph import StateGraph, START, END
from src.state import AgentState


# Import or define all required nodes
try:
    from src.nodes.detective import detective_repo_node, detective_doc_node, detective_vision_node
except ImportError:
    detective_repo_node = detective_doc_node = detective_vision_node = lambda state: state
try:
    from src.nodes.evidence_aggregator import evidence_aggregator_node
except ImportError:
    def evidence_aggregator_node(state):
        """Placeholder: aggregate evidence from detective layer."""
        return state
from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.chief_justice import chief_justice_node
from src.nodes.router import should_continue
from src.nodes.quality_assurance import quality_assurance_node


def build_graph():
    workflow = StateGraph(AgentState)
    # Fan-out: Detectives (Repo, Doc, Vision)
    workflow.add_node("detective_repo", detective_repo_node)
    workflow.add_node("detective_doc", detective_doc_node)
    workflow.add_node("detective_vision", detective_vision_node)
    # Fan-in: EvidenceAggregator
    workflow.add_node("evidence_aggregator", evidence_aggregator_node)
    # Fan-out: Judges (Prosecutor, Defense, TechLead)
    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("defense", defense_node)
    workflow.add_node("tech_lead", tech_lead_node)
    # Fan-in: ChiefJustice
    workflow.add_node("chief_justice", chief_justice_node)
    workflow.add_node("quality_assurance", quality_assurance_node)
    workflow.add_node("router", should_continue)

    # Fan-out from START to all detectives
    workflow.add_edge(START, "detective_repo")
    workflow.add_edge(START, "detective_doc")
    workflow.add_edge(START, "detective_vision")
    # Fan-in: all detectives to evidence aggregator
    workflow.add_edge("detective_repo", "evidence_aggregator")
    workflow.add_edge("detective_doc", "evidence_aggregator")
    workflow.add_edge("detective_vision", "evidence_aggregator")

    # Fan-out: evidence aggregator to all judges
    workflow.add_edge("evidence_aggregator", "prosecutor")
    workflow.add_edge("evidence_aggregator", "defense")
    workflow.add_edge("evidence_aggregator", "tech_lead")
    # Fan-in: all judges to chief justice
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")
    workflow.add_edge("chief_justice", "router")

    workflow.add_conditional_edges(
        "router",
        {
            # On appeal, re-fan-out to all detectives
            "detective": ["detective_repo", "detective_doc", "detective_vision"],
            "quality_assurance": "quality_assurance",
        },
        default=END,
    )
    workflow.add_edge("quality_assurance", END)
    return workflow.compile()
