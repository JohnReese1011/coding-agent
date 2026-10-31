import subprocess
from mcp.server.fastmcp import FastMCP
from common import WORKSPACE

mcp = FastMCP("coding-terminal")
# Deliberately conservative allowlist. Extend only for a trusted local workspace.
DISALLOWED = {"rm", "dd", "chmod", "mkfs", "mv"}


@mcp.tool()
def run_command(command: str, timeout_seconds: int = 60) -> str:
    """Run a command in workspace. Only allowlisted executables; no shell expansion/pipes."""
    import shlex
    try:
        args = shlex.split(command)
    except ValueError as e:
        return f"Invalid command: {e}"
    if not args or args[0] in DISALLOWED:
        return f"Blocked executable. DisAllowed: {', '.join(sorted(DISALLOWED))}"
#    if any(x in command for x in (";", "&&", "||", "|", ">", "<", "`", "$(")):
#        return "Blocked shell operators. Run one command at a time."
    timeout = max(1, min(int(timeout_seconds), 120))
    try:
        proc = subprocess.run(args, cwd=WORKSPACE, capture_output=True, text=True,
                              timeout=timeout, check=False)
        output = (proc.stdout + "\\n" + proc.stderr).strip()
        return f"exit_code={proc.returncode}\\n{output[:20000]}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"

@mcp.tool()
def run_tests(test_path: str = ".") -> str:
    """Run pytest against a path under workspace."""
    return run_command(f"pytest -q {test_path}", 120)

if __name__ == "__main__":
    mcp.run(transport="stdio")
