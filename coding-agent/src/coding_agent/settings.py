import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path.cwd()
WORKSPACE = Path(os.getenv("WORKSPACE", "./workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

# Chat model configuration. Legacy OLLAMA_* variables remain supported.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower().replace("-", "_")
LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", os.getenv("OLLAMA_TEMPERATURE", "0.1")))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "8192"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "16384"))

# Embeddings are configured independently from the chat model.
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").strip().lower().replace("-", "_")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")

MCP_CONFIG = Path(os.getenv("MCP_CONFIG", "./config/mcp_servers.json"))
MILVUS_URI = os.getenv("MILVUS_URI", "./data/milvus.db")
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "code_chunks")


def _safe_collection_part(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return value[:48] or "default"


def milvus_collection_name() -> str:
    """Use a separate collection per embedding provider/model to avoid dimension mixing."""
    explicit = os.getenv("MILVUS_COLLECTION")
    # The previous project template hard-coded "code_chunks". Treat that legacy
    # value like the default so existing .env files are safely namespaced too.
    if explicit and explicit != "code_chunks":
        return explicit
    return "code_chunks_{}_{}".format(
        _safe_collection_part(EMBEDDING_PROVIDER),
        _safe_collection_part(EMBEDDING_MODEL),
    )

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

