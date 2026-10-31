from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1] / "mcp_servers"))
from common import safe_path, WORKSPACE

def test_safe_path_inside():
    assert safe_path("a/b.py").is_relative_to(WORKSPACE)

def test_safe_path_rejects_escape():
    try:
        safe_path("../outside.txt")
        assert False, "expected ValueError"
    except ValueError:
        pass
