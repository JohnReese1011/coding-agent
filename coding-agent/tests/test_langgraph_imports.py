import ast
from pathlib import Path


def test_langgraph_entrypoint_modules_have_no_relative_imports():
    root = Path(__file__).resolve().parents[1]
    for relative in (
        "src/coding_agent/graph.py",
        "src/coding_agent/llm.py",
        "src/coding_agent/mcp.py",
    ):
        tree = ast.parse((root / relative).read_text())
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level > 0]
        assert not imports, f"Relative imports found in {relative}: {imports}"
