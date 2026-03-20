# tools/embedder.py
import os
import glob
import logging
import hashlib
from typing import List, Dict
from sentence_transformers import SentenceTransformer

from tools.vector_store import VectorStore

logger = logging.getLogger(__name__)

# helper
def _sha256_of_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", persist_dir: str = "chroma_db"):
        logger.info("🔁 Loading SentenceTransformer model (%s) — this may take a moment.", model_name)
        self.model = SentenceTransformer(model_name)
        self.vs = VectorStore(persist_directory=persist_dir)
        logger.info("✅ Embedder initialized")

    def _gather_files(self, base_dir: str, exts: List[str] = None) -> List[str]:
        exts = exts or ["*"]
        files = []
        for ext in exts:
            files += glob.glob(os.path.join(base_dir, "**", ext), recursive=True)
        # filter directories
        files = [f for f in files if os.path.isfile(f)]
        logger.info("📁 Found %d files under %s", len(files), base_dir)
        return files

    def embed_codebase(self, base_dir: str, include_exts: List[str] = None):
        include_exts = include_exts or ["*.py", "*.java", "*.go", "*.js", "*.ts", "*.md", "*.txt", "*.yaml", "*.yml", "*.json"]
        files = []
        for p in include_exts:
            files += glob.glob(os.path.join(base_dir, "**", p), recursive=True)
        files = [f for f in files if os.path.isfile(f)]
        logger.info("📦 Encoding %d files from %s", len(files), base_dir)

        docs = []
        ids = []
        metadatas = []
        embeddings = []

        for idx, fp in enumerate(files):
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
            except Exception:
                # binary or unreadable => skip
                logger.warning("⚠️ Skipping unreadable file: %s", fp)
                continue
            if not content.strip():
                logger.info("⏭️ Empty content, skipping: %s", fp)
                continue
            chunk_id = f"{os.path.relpath(fp, base_dir)}::{_sha256_of_file(fp)[:8]}"
            ids.append(chunk_id)
            docs.append(content)
            metadatas.append({"source": fp})
            emb = self.model.encode(content, show_progress_bar=False).tolist()
            embeddings.append(emb)

        if docs:
            self.vs.add_documents(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
            logger.info("✅ Persisted %d code chunks to vector DB", len(ids))
        else:
            logger.warning("⚠️ No document content to embed.")
