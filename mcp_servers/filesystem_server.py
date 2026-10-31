from mcp.server.fastmcp import FastMCP
from common import WORKSPACE, safe_path

mcp = FastMCP("coding-filesystem")

@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List files under the configured workspace."""
    path = safe_path(directory)
    if not path.is_dir():
        return "Directory does not exist"
    return "\\n".join(str(p.relative_to(WORKSPACE)) for p in path.rglob("*") if p.is_file())

@mcp.tool()
def read_file(path: str) -> str:
    """Read a UTF-8 text file inside workspace."""
    target = safe_path(path)
    if not target.is_file():
        return "File not found"
    if target.stat().st_size > 1_000_000:
        return "File too large (>1MB)"
    return target.read_text(encoding="utf-8")

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Create or overwrite a UTF-8 file inside workspace. Use only after user request."""
    target = safe_path(path)
    if len(content.encode("utf-8")) > 1_000_000:
        return "Content too large (>1MB)"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {path}"

@mcp.tool()
def search_files(keyword: str, file_suffix: str = "") -> str:
    """Search text files in workspace for a literal keyword."""
    found = []
    for p in WORKSPACE.rglob("*"):
        if not p.is_file() or (file_suffix and p.suffix != file_suffix):
            continue
        try:
            if keyword in p.read_text(encoding="utf-8"):
                found.append(str(p.relative_to(WORKSPACE)))
        except (UnicodeError, OSError):
            pass
    return "\\n".join(found[:200]) or "No matches"

if __name__ == "__main__":
    mcp.run(transport="stdio")
