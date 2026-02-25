from pathlib import Path
from langchain_core.tools import tool
from PyPDF2 import PdfReader

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
