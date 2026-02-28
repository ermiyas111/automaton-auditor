from __future__ import annotations
# Tool to list all file paths in a repository
from langchain_core.tools import tool

import tempfile
from pathlib import Path
from urllib.parse import urlparse
from git import Repo
from langchain_core.tools import tool

@tool
def list_repo_files(repository_path: str) -> list[str]:
    """List all file paths in the repository (relative to root). Accepts local path or repo URL."""
    from pathlib import Path
    import tempfile
    # Helper to check if input is a repo URL
    def _is_repository_url(value: str) -> bool:
        if value.startswith("git@"):
            return True
        from urllib.parse import urlparse
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https", "git", "ssh"} and bool(parsed.netloc)

    if _is_repository_url(repository_path):
        # Clone to temp dir
        temp_dir = Path(tempfile.mkdtemp(prefix="automaton_auditor_ls_"))
        local_repo_path = temp_dir / "repo"
        Repo.clone_from(repository_path, local_repo_path)
        base_path = local_repo_path
    else:
        base_path = Path(repository_path).expanduser().resolve()
    if not base_path.exists() or not base_path.is_dir():
        raise FileNotFoundError(f"Repository path does not exist or is not a directory: {base_path}")
    ignored_names = {".git", "__pycache__"}
    file_list = []
    for path in base_path.rglob("*"):
        if any(part in ignored_names for part in path.parts):
            continue
        if path.is_file():
            file_list.append(str(path.relative_to(base_path)))
    return file_list

def is_repository_url(value: str) -> bool:
    if value.startswith("git@"):
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "git", "ssh"} and bool(parsed.netloc)


@tool
def clone_repository(url: str) -> str:
    """Clone a git repository into a temporary directory and return the local path."""
    temp_dir = Path(tempfile.mkdtemp(prefix="automaton_auditor_"))
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

