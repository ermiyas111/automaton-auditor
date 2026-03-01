
# Automaton Auditor

A modular, dialectical, and rubric-driven multi-agent audit system built with LangGraph, Python, and Pydantic. Produces criterion-level, persona-driven technical audit reports in markdown.


## Features
- **Criterion-Level Rubric Assessment:** Each audit is scored and explained for every rubric criterion, using a structured JSON rubric.
- **Dialectical Judge Layer:** Three judge personas (Prosecutor, Defense, TechLead) independently assess each criterion, providing adversarial, charitable, and pragmatic perspectives.
- **Chief Justice Synthesis:** A deterministic synthesis node applies hardcoded rules (security override, fact supremacy, dissent handling) to produce a final markdown report with executive summary, criterion breakdown, and remediation plan.
- **Pydantic Validation:** All evidence and opinions are structured with Pydantic models for schema enforcement and safe aggregation.
- **AST-Based Code Analysis:** RepoInvestigator uses Python’s ast module to scan for risky patterns and logic flow.
- **Ephemeral Sandboxing:** Repositories are cloned into a temporary directory and only read operations are performed.
- **Fan-Out/Fan-In Workflow:** Parallel detective and judge nodes aggregate evidence and opinions for comprehensive analysis.
- **LLM-Driven Audit:** Judges and synthesis use LLMs for reasoning, but final verdict logic is deterministic and explainable.


## Architecture
- **StateGraph:** Orchestrates parallel and sequential node execution (fan-out/fan-in for detectives and judges).
- **AgentState:** TypedDict for workflow state, with evidence, judicial opinions, and unified forensics.
- **Detective Layer:**
   - `RepoInvestigator_node`: Clones and analyzes repo files, flags risks via AST.
   - `DocAnalyst_node`: Extracts and analyzes PDF report claims.
- **Evidence Aggregator:** Merges and formats all detective evidence for judge consumption.
- **Judicial Layer:**
   - `Prosecutor_node`, `Defense_node`, `TechLead_node`: Each loads the rubric from file and produces a list of CriterionAssessment for every criterion.
- **Chief Justice Node:** Synthesizes all judge opinions, applies rubric rules, and generates a markdown report with:
   - Executive Summary
   - Criterion Breakdown (with dissent and remediation)
   - Prioritized Remediation Plan


## How It Works
1. **Detective Layer:**
   - RepoInvestigator clones the repo and scans files for risky patterns.
   - DocAnalyst extracts claimed features and vulnerabilities from the PDF report.
2. **Evidence Aggregation:**
   - All detective evidence is merged and formatted for judge consumption.
3. **Judicial Layer:**
   - Each judge persona independently scores and explains every rubric criterion.
4. **Chief Justice Synthesis:**
   - Applies deterministic rules to synthesize judge opinions, resolve dissent, and generate a markdown report.


## Security & Sandboxing
- All code analysis is performed in a temporary, isolated directory.
- No code execution occurs during analysis.


## Extensibility
- Easily add new detective or judge nodes.
- Rubric-driven: Add or modify criteria in `src/resources/rubric.json`.
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
   uv run python scripts/run_audit.py
   ```
3. The final markdown report will be saved as `peer_grading_YEAR_MONTH_DAY_HH_MM_SS.md` in the project root.


## Project Structure
- `src/state.py`: State schema and Pydantic models
- `src/nodes/detective.py`: Detective layer nodes
- `src/nodes/evidence_aggregator.py`: Evidence aggregation logic
- `src/nodes/judges.py`: Judge persona nodes (Prosecutor, Defense, TechLead)
- `src/nodes/chief_justice.py`: Chief Justice markdown synthesis
- `src/graph.py`: Workflow orchestration
- `src/resources/rubric.json`: Rubric definition (criteria, synthesis rules)
- `src/tools/doc_tools.py`: PDF/report concept verification tools
- `scripts/run_audit.py`: Main audit workflow runner

## Concept Verification
- The tool `verify_concepts_in_report` scans the markdown/PDF report for the phrases "Dialectical Synthesis" and "Metacognition" and determines if they are explained (logic flow) or just used as buzzwords.

## License
MIT
