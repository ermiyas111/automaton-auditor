from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.detective import RepoInvestigator_node
from src.nodes.detective import DocAnalyst_node
from src.nodes.auditor import expert_auditor_node

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("repo_investigator", RepoInvestigator_node)
    workflow.add_node("doc_analyst", DocAnalyst_node)
    workflow.add_node("expert_auditor", expert_auditor_node)
    workflow.add_edge(START, "repo_investigator")
    workflow.add_edge(START, "doc_analyst")
    workflow.add_edge("repo_investigator", "expert_auditor")
    workflow.add_edge("doc_analyst", "expert_auditor")
    workflow.add_edge("expert_auditor", END)
    return workflow.compile()
