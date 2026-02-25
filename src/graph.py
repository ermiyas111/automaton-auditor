from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.detective import detective_repo_node
from src.nodes.auditor import expert_auditor_node

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("detective", detective_repo_node)
    workflow.add_node("expert_auditor", expert_auditor_node)
    workflow.add_edge(START, "detective")
    workflow.add_edge("detective", "expert_auditor")
    workflow.add_edge("expert_auditor", END)
    return workflow.compile()
