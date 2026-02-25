from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.detective import RepoInvestigator_node
from src.nodes.detective import DocAnalyst_node
from src.nodes.evidence_aggregator import evidence_aggregator_node

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("repo_investigator", RepoInvestigator_node)
    workflow.add_node("doc_analyst", DocAnalyst_node)
    workflow.add_node("evidence_aggregator", evidence_aggregator_node)
    workflow.add_edge(START, "repo_investigator")
    workflow.add_edge(START, "doc_analyst")
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    workflow.add_edge("evidence_aggregator", END)
    return workflow.compile()
