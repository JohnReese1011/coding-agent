from pathlib import Path
from mcp.server.fastmcp import FastMCP
from common import WORKSPACE
from dotenv import load_dotenv

load_dotenv()
mcp = FastMCP("coding-knowledge")


def _vector_store(embedding_model):
    from langchain_milvus import Milvus
    from coding_agent.settings import MILVUS_URI, milvus_collection_name

    Path(MILVUS_URI).parent.mkdir(parents=True, exist_ok=True)
    return Milvus(
        embedding_function=embedding_model,
        collection_name=milvus_collection_name(),
        connection_args={"uri": MILVUS_URI},
    )


@mcp.tool()
def index_code() -> str:
    """Index workspace source files into Milvus using the configured embedding provider."""
    try:
        from langchain_core.documents import Document
        from coding_agent.llm import embeddings
        from coding_agent.settings import MILVUS_URI, milvus_collection_name
        from langchain_milvus import Milvus

        model = embeddings()
        suffixes = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".md", ".txt"}
        docs = []
        for path in WORKSPACE.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeError, OSError):
                continue
            if content.strip():
                for offset in range(0, len(content), 1800):
                    docs.append(Document(
                        page_content=content[offset:offset + 1800],
                        metadata={"path": str(path.relative_to(WORKSPACE)), "offset": offset},
                    ))
        if not docs:
            return "No source files found to index."

        Path(MILVUS_URI).parent.mkdir(parents=True, exist_ok=True)
        Milvus.from_documents(
            docs,
            model,
            collection_name=milvus_collection_name(),
            connection_args={"uri": MILVUS_URI},
            drop_old=False,
        )
        return (
            f"Indexed {len(docs)} chunks into {MILVUS_URI}; "
            f"collection={milvus_collection_name()}"
        )
    except ImportError as exc:
        return f"Missing dependency: {exc}. Install: pip install -e '.[rag]'"
    except Exception as exc:
        return f"Indexing failed: {type(exc).__name__}: {exc}"


@mcp.tool()
def search_code(query: str, k: int = 5) -> str:
    """Semantic search indexed workspace code using the configured embedding provider."""
    try:
        from coding_agent.llm import embeddings

        store = _vector_store(embeddings())
        docs = store.similarity_search(query, k=max(1, min(k, 10)))
        return "\n\n".join(
            f"[{doc.metadata.get('path')} @ {doc.metadata.get('offset')}]\n{doc.page_content}"
            for doc in docs
        ) or "No relevant code found."
    except ImportError as exc:
        return f"Missing dependency: {exc}. Install: pip install -e '.[rag]'"
    except Exception as exc:
        return f"Search failed: {type(exc).__name__}: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
