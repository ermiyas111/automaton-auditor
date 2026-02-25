import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, cast
from src.state import AgentState, Evidence
from src.tools.repo_tools import read_project_files
from src.tools.doc_tools import parse_audit_pdf

logging.basicConfig(level=logging.INFO)

def scan_code_for_risks(file_content: str, filename: str) -> List[str]:
    """Scan Python code for high-risk patterns using AST."""
    risks = []
    try:
        tree = ast.parse(file_content, filename=filename)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = getattr(node.func, 'id', '') or getattr(getattr(node.func, 'attr', ''), 'id', '')
                if func in {"eval", "exec"}:
                    risks.append(f"Use of {func}() in {filename}")
            if isinstance(node, ast.Attribute):
                if getattr(node.value, 'id', '') == "os" and node.attr == "system":
                    risks.append(f"Use of os.system() in {filename}")
        # Simple regex for hardcoded API keys (not AST, but quick scan)
        import re
        if re.search(r"(?i)api[_-]?key\s*=\s*['\"]\w{16,}['\"]", file_content):
            risks.append(f"Possible hardcoded API key in {filename}")
    except Exception as e:
        risks.append(f"AST parse error in {filename}: {e}")
    return risks

def RepoInvestigator_node(state: AgentState) -> Dict:
    repo_path_val = state["repository_path"]
    from src.tools.repo_tools import is_repository_url, clone_repository
    if is_repository_url(repo_path_val):
        repo_path = clone_repository.invoke({"url": repo_path_val})
        logging.info(f"[RepoInvestigator] Cloned repository to: {repo_path}")
    else:
        repo_path = str(Path(repo_path_val).expanduser().resolve())
    logging.info(f"[RepoInvestigator] Processing repository at: {repo_path}")
    file_map = read_project_files.invoke({"repository_path": repo_path})
    critical_findings = []
    for fname, content in file_map.items():
        logging.info(f"[RepoInvestigator] Analyzing file: {fname}")
        if fname.endswith(".py"):
            critical_findings.extend(scan_code_for_risks(content, fname))
    evidence = Evidence(
        source="repository",
        content_summary=f"Analyzed {len(file_map)} files in repo.",
        raw_data=file_map,
        critical_findings=critical_findings,
    )
    # Return as list for operator.add
    return {**state, "evidence": [evidence]}

def DocAnalyst_node(state: AgentState) -> Dict:
    pdf_path = Path(state["pdf_path"]).expanduser().resolve()
    logging.info(f"[DocAnalyst] Processing PDF at: {pdf_path}")
    text = parse_audit_pdf.invoke({"pdf_path": str(pdf_path)})
    # Simple extraction for 'Claimed Features' and 'Reported Vulnerabilities'
    import re
    claimed = re.findall(r"Claimed Features:(.*?)(?:\n\w|$)", text, re.DOTALL)
    vulnerabilities = re.findall(r"Reported Vulnerabilities:(.*?)(?:\n\w|$)", text, re.DOTALL)
    findings = []
    if claimed:
        findings.extend([f"Claimed Feature: {c.strip()}" for c in claimed[0].split("\n") if c.strip()])
    if vulnerabilities:
        findings.extend([f"Reported Vulnerability: {v.strip()}" for v in vulnerabilities[0].split("\n") if v.strip()])
    evidence = Evidence(
        source="pdf_report",
        content_summary="Extracted claimed features and vulnerabilities from PDF.",
        raw_data={"claimed_features": claimed, "reported_vulnerabilities": vulnerabilities, "full_text": text},
        critical_findings=findings,
    )
    return {**state, "evidence": [evidence]}
