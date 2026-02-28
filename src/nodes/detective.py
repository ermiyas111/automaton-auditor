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
    protocol_results = {}
    critical_findings = []

    # --- Protocol A: State Structure ---
    state_py = Path("src/state.py")
    graph_py = Path("src/graph.py")
    state_code = state_py.read_text(encoding="utf-8") if state_py.exists() else ""
    graph_code = graph_py.read_text(encoding="utf-8") if graph_py.exists() else ""
    state_has_typed = ("TypedDict" in state_code or "BaseModel" in state_code)
    if state_has_typed:
        protocol_results["state_structure"] = "PASS: Typed state definition found."
    else:
        protocol_results["state_structure"] = "FAIL: No typed state definition found."
        critical_findings.append("FAIL: No typed state definition found.")

    # --- Protocol B: Graph Wiring ---
    import ast
    try:
        tree = ast.parse(graph_code, filename="src/graph.py")
        # Count add_edge calls by source node (fan-out) and by destination node (fan-in)
        edge_map_out = {}
        edge_map_in = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'attr') and node.func.attr == 'add_edge':
                if len(node.args) >= 2:
                    src = None
                    dst = None
                    # Source node
                    if isinstance(node.args[0], ast.Constant):
                        src = node.args[0].value
                    elif isinstance(node.args[0], ast.Str):  # Python <3.8
                        src = node.args[0].s
                    # Destination node
                    if isinstance(node.args[1], ast.Constant):
                        dst = node.args[1].value
                    elif isinstance(node.args[1], ast.Str):
                        dst = node.args[1].s
                    if src:
                        edge_map_out.setdefault(src, 0)
                        edge_map_out[src] += 1
                    if dst:
                        edge_map_in.setdefault(dst, 0)
                        edge_map_in[dst] += 1
        fanout_found = any(count > 1 for count in edge_map_out.values())
        fanin_found = any(count > 1 for count in edge_map_in.values())
        if fanout_found and fanin_found:
            protocol_results["graph_wiring"] = "PASS: Parallel fan-out and fan-in detected."
        elif fanout_found:
            protocol_results["graph_wiring"] = "Parallel fan-out detected, but no parallel fan-in."
        elif fanin_found:
            protocol_results["graph_wiring"] = "Parallel fan-in detected, but no parallel fan-out."
        else:
            protocol_results["graph_wiring"] = "No parallel fan-out or fan-in detected."
    except Exception as e:
        protocol_results["graph_wiring"] = f"ERROR: AST parse failed: {e}"

    # --- Protocol C: Git Narrative ---
    import subprocess
    try:
        git_log = subprocess.check_output(["git", "log", "--pretty=format:%H|%ct|%s"], cwd=".", encoding="utf-8", errors="ignore")
        lines = git_log.strip().split("\n")
        commit_count = len(lines)
        timestamps = [int(line.split("|")[1]) for line in lines if "|" in line]
        if commit_count == 1:
            protocol_results["git_narrative"] = "Monolithic History: Only one commit."
            critical_findings.append("Monolithic History: Only one commit.")
        else:
            # Calculate days between first and last commit (inclusive)
            if timestamps:
                min_ts = min(timestamps)
                max_ts = max(timestamps)
                days = max(1, int((max_ts - min_ts) / 86400) + 1)
                avg_commits_per_day = commit_count / days
                if avg_commits_per_day < 3:
                    protocol_results["git_narrative"] = f"Monolithic History: {commit_count} commits over {days} days (avg {avg_commits_per_day:.2f}/day)."
                    critical_findings.append(f"Monolithic History: {commit_count} commits over {days} days (avg {avg_commits_per_day:.2f}/day).")
                else:
                    protocol_results["git_narrative"] = f"{commit_count} commits over {days} days (avg {avg_commits_per_day:.2f}/day)."
            else:
                protocol_results["git_narrative"] = f"{commit_count} commits."
    except Exception as e:
        protocol_results["git_narrative"] = f"ERROR: git log failed: {e}"

    # --- Repo File Map ---
    if is_repository_url(repo_path_val):
        repo_path = clone_repository.invoke({"url": repo_path_val})
        logging.info(f"[RepoInvestigator] Cloned repository to: {repo_path}")
    else:
        repo_path = str(Path(repo_path_val).expanduser().resolve())
    logging.info(f"[RepoInvestigator] Processing repository at: {repo_path}")
    file_map = read_project_files.invoke({"repository_path": repo_path})

    # Add file manifest to protocol_results for DocAnalyst
    protocol_results["file_manifest"] = list(file_map.keys())

    # Risk scan (legacy)
    for fname, content in file_map.items():
        logging.info(f"[RepoInvestigator] Analyzing file: {fname}")
        if fname.endswith(".py"):
            critical_findings.extend(scan_code_for_risks(content, fname))

    evidence = Evidence(
        source="repository",
        content_summary=f"Analyzed {len(file_map)} files in repo.",
        raw_data=file_map,
        critical_findings=critical_findings,
        protocol_results=protocol_results,
    )
    # Return evidence_list only for reducer
    return {"evidence_list": state.get("evidence_list", []) + [evidence]}


def DocAnalyst_node(state: AgentState) -> Dict:
    pdf_path = Path(state["pdf_path"]).expanduser().resolve()
    logging.info(f"[DocAnalyst] Processing PDF at: {pdf_path}")
    text = parse_audit_pdf.invoke({"pdf_path": str(pdf_path)})
    import re
    findings = []
    protocol_results = {}

    # --- Protocol A: Citation Check ---
    # Use list_repo_files tool to get file manifest
    from src.tools.repo_tools import list_repo_files
    repo_path_val = state["repository_path"]
    try:
        file_manifest = set(list_repo_files.invoke({"repository_path": repo_path_val}))
    except Exception as e:
        file_manifest = set()
        protocol_results["citation_check"] = f"ERROR: Could not get file manifest: {e}"
    # Find all file-like mentions in PDF (must have at least one directory with a forward slash, and at least one alphanumeric character in each part)
    # Disallow spaces anywhere in the matched file path
    # Require at least one directory, at least one alphabet in filename and extension, and no spaces
    # Only match file paths with known extensions
    known_exts = ["py", "md", "json", "txt", "pdf", "csv", "yml", "yaml", "ini", "cfg", "rst", "toml", "js", "ts", "html", "css", "ipynb"]
    ext_pattern = "|".join(known_exts)
    pattern = rf"([a-zA-Z0-9][\w.-]*/(?:[a-zA-Z0-9][\w.-]*/)*[a-zA-Z0-9]*[a-zA-Z][\w.-]*\.({ext_pattern}))"
    mentioned_files = set(match[0] for match in re.findall(pattern, text))
    # Normalize both sets for robust comparison
    norm = lambda p: p.replace("\\", "/").lower().lstrip("./")
    file_manifest_norm = {norm(f) for f in file_manifest}
    hallucinated = [f for f in mentioned_files if norm(f) not in file_manifest_norm]
    if hallucinated:
        for f in hallucinated:
            findings.append(f"Hallucination: {f} mentioned in report but not found in repo.")
        protocol_results["citation_check"] = f"Hallucinated files: {hallucinated}"
    elif "citation_check" not in protocol_results:
        protocol_results["citation_check"] = "No hallucinated files."

    # --- Protocol B: Concept Verification ---
    buzzwords = ["Dialectical Synthesis", "Metacognition"]
    for word in buzzwords:
        idx = text.find(word)
        if idx == -1:
            continue
        # Look for explanation within 200 chars after the word
        snippet = text[idx:idx+200]
        if re.search(r"explain|how|implemented|logic|architecture|flow", snippet, re.IGNORECASE):
            findings.append(f"Concept '{word}' explained in context.")
            protocol_results[f"concept_{word}"] = "Explained"
        else:
            findings.append(f"Concept '{word}' used as buzzword only.")
            protocol_results[f"concept_{word}"] = "Buzzword only"

    # Legacy: extract claimed features and vulnerabilities
    claimed = re.findall(r"Claimed Features:(.*?)(?:\n\w|$)", text, re.DOTALL)
    vulnerabilities = re.findall(r"Reported Vulnerabilities:(.*?)(?:\n\w|$)", text, re.DOTALL)
    if claimed:
        findings.extend([f"Claimed Feature: {c.strip()}" for c in claimed[0].split("\n") if c.strip()])
    if vulnerabilities:
        findings.extend([f"Reported Vulnerability: {v.strip()}" for v in vulnerabilities[0].split("\n") if v.strip()])

    evidence = Evidence(
        source="pdf_report",
        content_summary="Extracted claimed features, vulnerabilities, and protocol findings from PDF.",
        raw_data={"claimed_features": claimed, "reported_vulnerabilities": vulnerabilities, "full_text": text},
        critical_findings=findings,
        protocol_results=protocol_results,
    )
    # Return evidence_list only for reducer
    return {"evidence_list": state.get("evidence_list", []) + [evidence]}
