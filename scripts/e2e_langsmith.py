import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from src.state import AgentState
from src.nodes.detective import detective_node
from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.chief_justice import chief_justice_node

load_dotenv()

builder = StateGraph(AgentState)
builder.add_node("detective", detective_node)
builder.add_node("prosecutor", prosecutor_node)
builder.add_node("defense", defense_node)
builder.add_node("tech_lead", tech_lead_node)
builder.add_node("chief_justice", chief_justice_node)

builder.add_edge(START, "detective")
builder.add_edge("detective", "prosecutor")
builder.add_edge("detective", "defense")
builder.add_edge("detective", "tech_lead")
builder.add_edge("prosecutor", "chief_justice")
builder.add_edge("defense", "chief_justice")
builder.add_edge("tech_lead", "chief_justice")
builder.add_edge("chief_justice", END)

graph = builder.compile()

initial_state = {
    "task_description": "Audit this repository against the provided report.",
    "repository_path": "https://github.com/owner/repo",  # or local path
    "audit_report_text": "",
    "evidence": {},
    "judicial_opinions": [],
    "final_verdict": "",
    # optional keys your detective node already supports:
    "pdf_path": "C:/path/to/audit_report.pdf",
}

result = graph.invoke(
    initial_state,
    config={"run_name": "automation-auditor-e2e", "tags": ["e2e", "judicial-layer"]},
)
print(result["final_verdict"])