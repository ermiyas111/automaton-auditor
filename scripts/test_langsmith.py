import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.graph import build_graph

graph = build_graph()
initial_state = {
    "task_description": "Audit this repository against the provided report.",
    "repository_path": "https://github.com/ermiyas111/Project-Chimera",
    "audit_report_text": "",
    "evidence": {},
    "judicial_opinions": [],
    "final_verdict": "",
    "pdf_path": "C:\\Users\\HP\\Downloads\\ProjectChimeraResearch.pdf",
}

result = graph.invoke(
    initial_state,
    config={"run_name": "automation-auditor-test", "tags": ["langsmith", "test"]},
)
print(result)