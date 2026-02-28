from langchain_google_genai import ChatGoogleGenerativeAI
import os

def verify_concepts_in_report(text: str) -> dict:
    """Extract sophisticated terms and verify if they are explained in the report using LLM."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    # Use only the known working model
    model_name = "gemini-2.5-flash"
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    except Exception as e:
        return {"findings": [f"Failed to initialize Google Generative AI model '{model_name}': {e}"], "protocol_results": {"concept_extraction": f"Model error: {e}"}}
    # extract_prompt = (
    #     "You are an expert in AI reviewer Agent development. Read the following report and extract a list of all phrases, terms, or concepts specifically relevant to AI evaluation systems, such as rubric-driven assessment, LLM-based scoring, evidence propagation, concept verification, forensic protocols, technical audit workflows, and related advanced AI/ML evaluation methodologies. "
    #     "Return a JSON list of unique phrases or terms that are directly related to the design, implementation, or evaluation of AI systems.\n\nReport:\n" + text + "\nRespond in JSON: [str, ...]"
    # )
    sophisticated_terms = []
    findings = []
    concept_evaluations = []
    protocol_results = {}
    try:
        # Single prompt: extract and evaluate concepts in one call
        unified_prompt = (
            "You are an expert in AI reviewer Agent development. Read the following report and do the following: "
            "1. Extract a list of all phrases, terms, or concepts specifically relevant to AI evaluation systems, such as rubric-driven assessment, LLM-based scoring, evidence propagation, concept verification, forensic protocols, technical audit workflows, and related advanced AI/ML evaluation methodologies. "
            "2. For each extracted concept, determine if the report provides a deep explanation of how the architecture or implementation executes or embodies it. Be specific: If it is explained anywhere in the report, summarize how. If not, state it is just a buzzword.\n\n"
            f"Full report:\n{text}"
            "\nRespond in JSON as: { 'concepts': [str, ...], 'evaluations': [{ 'concept': str, 'status': 'Explained' or 'Buzzword only', 'summary': str }, ...] }"
        )
        response = llm.invoke(unified_prompt)
        content = getattr(response, 'content', None)
        import json, re
        if isinstance(content, str) and content.strip():
            # Remove markdown code block if present
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
            if match:
                json_str = match.group(1)
            else:
                json_str = content
            try:
                result = json.loads(json_str)
            except Exception as e:
                print(f"Failed to parse JSON: {e}\nContent was: {json_str}")
                result = {}
        else:
            result = {}
        sophisticated_terms = result.get('concepts', [])
        results = result.get('evaluations', [])
        for eval_result in results:
            word = eval_result.get('concept', '')
            status = eval_result.get('status', 'Buzzword only')
            summary = eval_result.get('summary', '')
            findings.append(f"Concept '{word}': {status}. {summary}")
    except Exception as e:
        findings.append(f"Unified LLM analysis failed: {e}")
        protocol_results["concept_extraction"] = f"LLM error: {e}"
        if 'sophisticated_terms' in locals():
            for word in sophisticated_terms:
                protocol_results[f"concept_{word}"] = f"LLM error: {e}"
    protocol_results["concept_evaluations"] = results
    return {"findings": findings, "protocol_results": protocol_results}
from pathlib import Path
from langchain_core.tools import tool
from PyPDF2 import PdfReader

@tool
def read_markdown_file(md_path: str) -> str:
    """Read a markdown file and return its content as a string."""
    from pathlib import Path
    path = Path(md_path).expanduser().resolve()
    if not path.exists() or not path.suffix.lower() == ".md":
        raise FileNotFoundError(f"Markdown file not found: {md_path}")
    return path.read_text(encoding="utf-8")

@tool
def parse_audit_pdf(pdf_path: str) -> str:
    """Extract raw text from an audit PDF file."""
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        unlock_result = reader.decrypt("")
        if unlock_result == 0:
            raise ValueError("PDF is encrypted and cannot be read without a password")
    extracted_pages: list[str] = []
    for page in reader.pages:
        extracted_pages.append(page.extract_text() or "")
    return "\n".join(extracted_pages).strip()
