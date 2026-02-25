from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse
from git import Repo
from langchain_core.tools import tool
from PyPDF2 import PdfReader


def is_repository_url(value: str) -> bool:
    if value.startswith("git@"):
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "git", "ssh"} and bool(parsed.netloc)


@tool
def clone_repository(url: str) -> str:
    """Clone a git repository into a temporary directory and return the local path."""
    temp_dir = Path(tempfile.mkdtemp(prefix="automation_auditor_"))
    local_repo_path = temp_dir / "repo"
    Repo.clone_from(url, local_repo_path)
    return str(local_repo_path)


@tool
def read_project_files(repository_path: str) -> dict[str, str]:
    """Read project files recursively and return a mapping of relative path to text content."""
    base_path = Path(repository_path).expanduser().resolve()
    if not base_path.exists() or not base_path.is_dir():
        raise FileNotFoundError(f"Repository path does not exist or is not a directory: {base_path}")
    ignored_names = {".git", "__pycache__"}
    file_map: dict[str, str] = {}
    for path in base_path.rglob("*"):
        if any(part in ignored_names for part in path.parts):
            continue
        if not path.is_file():
            continue
        try:
            file_map[str(path.relative_to(base_path))] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            file_map[str(path.relative_to(base_path))] = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return file_map


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
