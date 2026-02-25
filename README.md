# Automaton Auditor

A modular, multi-agent audit system built with LangGraph and Python.

## Features
- Parallel evidence gathering from code, documents, and vision sources
- Fan-in/fan-out graph orchestration for scalable agent workflows
- Modular detective, judge, and chief justice nodes
- Self-correction loop with appeal/discovery routing
- MinMax quality assurance node for claim validation
- Markdown report rendering for audit results
- State persistence with MemorySaver (optional)
- Visual graph architecture (Mermaid PNG)

## Project Structure
```
automation-auditor/
├── src/
│   ├── state.py
│   ├── graph.py
│   ├── nodes/
│   │   ├── detective.py
│   │   ├── judges.py
│   │   ├── chief_justice.py
│   │   ├── evidence_aggregator.py
│   │   ├── router.py
│   │   ├── quality_assurance.py
│   ├── tools/
│   │   ├── repo_tools.py
│   │   ├── doc_tools.py
├── scripts/
│   ├── test_langsmith.py
│   ├── e2e_langsmith.py
├── pyproject.toml
├── README.md
```

## Quick Start
1. Clone the repository and install dependencies:
   ```bash
   git clone <repo-url>
   cd automation-auditor
   uv pip install
   ```
2. Run the audit workflow:
   ```bash
   uv run python scripts/test_langsmith.py
   ```
3. View the graph architecture:
   ```bash
   uv run python src/graph.py
   # See graph_structure.png
   ```

## LangGraph Workflow
- **Detective Node:** Gathers evidence from repo, docs, vision
- **Judges:** Prosecutor, Defense, Tech Lead analyze evidence in parallel
- **Chief Justice:** Aggregates opinions, issues verdict
- **Router:** Handles appeal/discovery loop based on verdict confidence
- **Quality Assurance:** Validates claims and triggers re-evaluation if needed
- **Markdown Report:** Final output for audit results

## Customization
- Add new detective or judge nodes in `src/nodes/`
- Extend evidence types in `src/state.py`
- Modify routing logic in `src/nodes/router.py`

## Visualization
- The graph structure is rendered as a PNG for easy verification.

## License
MIT

## Authors
- Your Name

---
For advanced debugging and tracing, use LangSmith and inspect runs at https://smith.langchain.com/
