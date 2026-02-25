# Automaton Auditor

A modular, auditable, and self-correcting multi-agent audit system built with LangGraph, Python, and Pydantic.

## Features
- **Pydantic Validation:** All evidence and opinions are structured with Pydantic models for schema enforcement and safe aggregation.
- **AST-Based Code Analysis:** RepoInvestigator uses Python’s ast module to scan for risky patterns and logic flow.
- **Ephemeral Sandboxing:** Repositories are cloned into a temporary directory and only read operations are performed.
- **Fan-Out/Fan-In Workflow:** Parallel detective nodes aggregate evidence for comprehensive analysis.
- **LLM-Driven Audit:** Expert auditor node synthesizes evidence and report claims for final verdict.

## Architecture
- **StateGraph:** Orchestrates parallel and sequential node execution.
- **AgentState:** TypedDict for workflow state, with evidence as a list of Pydantic Evidence objects.
- **Detective Layer:**
  - `RepoInvestigator_node`: Clones and analyzes repo files, flags risks via AST.
  - `DocAnalyst_node`: Extracts and analyzes PDF report claims.
- **Expert Auditor Node:** Combines evidence and report for a comprehensive audit summary.

## How It Works
1. **Detective Layer:**
   - RepoInvestigator clones the repo and scans files for risky patterns.
   - DocAnalyst extracts claimed features and vulnerabilities from the PDF report.
2. **Aggregation:**
   - Evidence from both nodes is merged and validated.
3. **Audit Synthesis:**
   - Expert auditor node analyzes all evidence and report claims, returning a final score and list of issues.

## Security & Sandboxing
- All code analysis is performed in a temporary, isolated directory.
- No code execution occurs during analysis.

## Extensibility
- Easily add new detective or auditor nodes.
- Supports advanced orchestration patterns (fan-out/fan-in, conditional routing).

## Requirements
- Python 3.10+
- LangGraph
- Pydantic
- PyPDF2
- GitPython

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the audit workflow:
   ```bash
   uv run python scripts/test_langsmith.py
   ```

## Project Structure
- `src/state.py`: State schema and Pydantic models
- `src/nodes/detective.py`: Detective layer nodes
- `src/nodes/auditor.py`: Expert auditor node
- `src/graph.py`: Workflow orchestration
- `scripts/test_langsmith.py`: Example test harness

## License
MIT
