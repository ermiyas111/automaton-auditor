import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph import build_graph

load_dotenv()

graph = build_graph()
initial_state = {
    "task_description": "Audit this repository against the provided report.",
    "repository_path": "https://github.com/ermiyas111/automaton-auditor",
    "audit_report_text": "",
    "pdf_path": "C:\\Users\\HP\\Downloads\\ProjectChimeraResearch.pdf",
    "evidence": [],
    "audit_summary": {},
    "final_verdict": "",
}

result = graph.invoke(
    initial_state,
    config={"run_name": "automaton-auditor-test", "tags": ["langsmith", "test"]},
)
print(result)