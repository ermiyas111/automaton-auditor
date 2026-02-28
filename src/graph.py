from langgraph.graph import StateGraph, START, END
from src.state import AgentState

from src.nodes.detective import RepoInvestigator_node
from src.nodes.detective import DocAnalyst_node
from src.nodes.evidence_aggregator import evidence_aggregator_node

from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.chief_justice import chief_justice_node

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("repo_investigator", RepoInvestigator_node)
    workflow.add_node("doc_analyst", DocAnalyst_node)
    workflow.add_node("evidence_aggregator", evidence_aggregator_node)
    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("defense", defense_node)
    workflow.add_node("tech_lead", tech_lead_node)
    workflow.add_node("chief_justice", chief_justice_node)

    # Parallel Discovery
    workflow.add_edge(START, "repo_investigator")
    workflow.add_edge(START, "doc_analyst")
    # Fan-In
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    # Judicial Fan-Out
    workflow.add_edge("evidence_aggregator", "prosecutor")
    workflow.add_edge("evidence_aggregator", "defense")
    workflow.add_edge("evidence_aggregator", "tech_lead")
    # Final Fan-In
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")
    workflow.add_edge("chief_justice", END)
    return workflow.compile()
