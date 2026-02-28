import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph import build_graph


load_dotenv()

graph = build_graph()
initial_state = {
    "task_description": "Audit this repository against the provided report.",
    "repository_path": "https://github.com/ermiyas111/10Acweek2",
    "audit_report_text": "",
    "pdf_path": "C:\\Users\\HP\\Downloads\\final_report.pdf",
    "evidence": [],
    "audit_summary": {},
    "final_verdict": "",
}


result = graph.invoke(
    initial_state,
    config={"run_name": "automaton-auditor-test", "tags": ["langsmith", "test"]},
)

# Generate Peer Audit Markdown report
import datetime

opinions_raw = result.get("judicial_opinions", [])
errors = result.get("errors", [])

def _status_from_score(final_score: float) -> str:
    if final_score >= 4.0:
        return "Pass"
    if final_score >= 2.5:
        return "Needs Improvement"
    return "Fail"

markdown_report = "# Peer Audit Report\n\nRubric missing or invalid."

# print(markdown_report)
with open("peer_audit_report.md", "w", encoding="utf-8") as f:
    f.write(markdown_report)
if errors:
    print("Errors:", errors)