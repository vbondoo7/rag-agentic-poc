# agents/sdk_tools.py
import logging
from typing import Tuple, List, Dict, Any
from tools.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Thin wrapper for RAG search
def search_vector(query: str, top_k: int = 5, topk: int = None, persist_dir: str = "chroma_db") -> Tuple[str, Dict[str, Any]]:
    """Run a vector search and return (context_text, docs_dict).

    Returns:
      - context_text: joined document text used as prompt context
      - docs_dict: raw documents+metadatas dict for callers that need sources

    Accepts either `top_k` or `topk` (legacy callers).
    """
    if topk is not None:
        top_k = topk
    vs = VectorStore(persist_directory=persist_dir)
    res = vs.query([query], n_results=top_k)

    # chroma returns nested lists per-query; we expect a single-query call so we take first element
    documents = []
    metadatas = []
    try:
        documents = res.get("documents", [[]])[0] if isinstance(res.get("documents", None), list) else res.get("documents", [])
        metadatas = res.get("metadatas", [[]])[0] if isinstance(res.get("metadatas", None), list) else res.get("metadatas", [])
    except Exception:
        logger.exception("Failed to normalize vector store response")

    # join into a single context string (agents expect plain text context)
    context = "\n\n".join([d for d in documents if d])
    docs_dict = {"documents": documents, "metadatas": metadatas}
    return context, docs_dict


def detect_intent(query: str) -> str:
    q = query.lower()
    if any(kw in q for kw in ["impact", "affected", "impact assessment"]):
        return "impact"
    if any(kw in q for kw in ["blueprint", "solution", "design", "architecture"]):
        return "blueprint"
    if any(kw in q for kw in ["document", "doc", "documentation", "docs"]):
        return "documentation"
    if any(kw in q for kw in ["understand", "explain", "functionality", "what does"]):
        return "understanding"
    return "generic"

# Minimal memory helpers. The project also includes a more complete ChatDB in ai_agents/db.py —
# these helpers provide a lightweight in-memory fallback so agents that call memory functions
# won't crash when run from scripts/tests.
_memory_store: List[Dict] = []

def read_memory(limit: int = 20) -> List[Dict]:
    """Return recent memory entries (simple in-memory list)."""
    return list(_memory_store[-limit:])

def append_memory(entry: Dict) -> bool:
    """Append a memory entry to the in-memory store. Returns True on success."""
    try:
        _memory_store.append(entry)
        return True
    except Exception:
        logger.exception("Failed to append memory")
        return False
