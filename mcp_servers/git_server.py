import subprocess
from mcp.server.fastmcp import FastMCP
from common import WORKSPACE, safe_path

mcp = FastMCP("coding-git")

def git(*args):
    p = subprocess.run(["git", *args], cwd=WORKSPACE, capture_output=True, text=True, timeout=30)
    return f"exit_code={p.returncode}\\n{(p.stdout + p.stderr)[:15000]}"

@mcp.tool()
def git_status() -> str:
    """Show git status."""
    return git("status", "--short", "--branch")

@mcp.tool()
def git_diff() -> str:
    """Show unstaged and staged diff."""
    return git("diff", "HEAD", "--")

@mcp.tool()
def git_log(limit: int = 10) -> str:
    """Show recent commits."""
    return git("log", f"-{max(1, min(limit, 30))}", "--oneline")

@mcp.tool()
def git_add(paths: list[str]) -> str:
    """Stage selected workspace-relative paths. Does not commit."""
    checked = []
    for item in paths:
        safe_path(item)
        checked.append(item)
    return git("add", "--", *checked)

if __name__ == "__main__":
    mcp.run(transport="stdio")
