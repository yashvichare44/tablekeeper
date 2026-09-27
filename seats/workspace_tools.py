"""Generic workspace tools. No product or track knowledge."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from langchain_core.tools import tool


def workspace_root() -> Path:
    raw = os.getenv("WORKSPACE_ROOT")
    if not raw:
        raise RuntimeError("WORKSPACE_ROOT is not set")
    root = Path(raw).resolve()
    if not root.is_dir():
        raise RuntimeError(f"WORKSPACE_ROOT does not exist: {root}")
    return root


def _safe_path(relative: str) -> Path:
    root = workspace_root()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise ValueError("path escapes the workspace")
    return path


@tool
def list_dir(path: str = ".") -> str:
    """List files and directories under a workspace-relative path."""
    target = _safe_path(path)
    if not target.exists():
        return f"not found: {path}"
    if target.is_file():
        return f"file: {path}"
    entries = []
    for child in sorted(target.iterdir()):
        kind = "dir" if child.is_dir() else "file"
        entries.append(f"{kind}\t{child.relative_to(workspace_root())}")
    return "\n".join(entries) or "(empty)"


@tool
def read_file(path: str) -> str:
    """Read a UTF-8 text file relative to the workspace root."""
    target = _safe_path(path)
    if not target.is_file():
        return f"not a file: {path}"
    if target.stat().st_size > 200_000:
        return "file too large to read"
    return target.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a UTF-8 text file relative to the workspace root."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"wrote {path} ({len(content)} bytes)"


@tool
def run_command(command: str) -> str:
    """Run a shell command inside the workspace. Use for tests and local builds."""
    root = workspace_root()
    result = subprocess.run(
        command,
        shell=True,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = (result.stdout + result.stderr).strip()
    if len(output) > 12_000:
        output = output[:12_000] + "\n...truncated..."
    return f"exit={result.returncode}\n{output}"


READ_TOOLS = [list_dir, read_file]
WRITE_TOOLS = [list_dir, read_file, write_file, run_command]
REVIEW_TOOLS = [list_dir, read_file, run_command]
