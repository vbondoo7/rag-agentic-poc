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


def read_memory(limit: int = 10) -> list:
    """Simple memory reader stub. Returns recent memory entries.

    This is intentionally minimal — projects can replace with a proper memory store.
    """
    try:
        # read a JSON lines file if present
        import json, os
        mem_file = os.path.join("data", "memory.jsonl")
        if not os.path.exists(mem_file):
            return []
        out = []
        with open(mem_file, "r", encoding="utf8") as fh:
            for i, line in enumerate(fh):
                if i >= limit:
                    break
                try:
                    out.append(json.loads(line.strip()))
                except Exception:
                    out.append({"text": line.strip()})
        return out
    except Exception:
        return []


def append_memory(entry: dict) -> bool:
    """Append a memory entry (dict) to the memory file. Returns True on success."""
    try:
        import json, os
        os.makedirs("data", exist_ok=True)
        mem_file = os.path.join("data", "memory.jsonl")
        with open(mem_file, "a", encoding="utf8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False
