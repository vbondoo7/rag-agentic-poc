# agents/sdk_tools.py
import logging
from typing import Tuple, List, Dict
from tools.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Thin wrapper for RAG search
def search_vector(query: str, top_k: int = 5, persist_dir: str = "chroma_db") -> Dict:
    vs = VectorStore(persist_directory=persist_dir)
    res = vs.query([query], n_results=top_k)
    # normalize result
    return res

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
