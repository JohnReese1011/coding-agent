import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
WORKSPACE = Path(os.getenv("WORKSPACE", "./workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

def safe_path(relative: str) -> Path:
    target = (WORKSPACE / relative).resolve()
    if not target.is_relative_to(WORKSPACE):
        raise ValueError("Path escapes workspace")
    return target
