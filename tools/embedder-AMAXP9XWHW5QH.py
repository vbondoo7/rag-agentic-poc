# tools/embedder.py
import os
import glob
import logging
import hashlib
from typing import List, Dict, Union
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
    def __init__(self,
                 model_names: Union[str, List[str]] = None,
                 persist_dir: str = "chroma_db",
                 chunk_size: int = 2000,
                 chunk_overlap: int = 200,
                 model_name: Union[str, None] = None):
        """Embedder with support for multiple open-source SentenceTransformer models and chunking.

        model_names: single model name or list of model names to try in order as fallbacks.
        chunk_size: approximate characters per chunk when splitting large files.
        chunk_overlap: overlap in characters between chunks.
        """
        # Backwards compatibility: accept `model_name` kwarg used elsewhere in the repo
        if model_name is not None:
            # If a single legacy model_name was provided, prefer it
            model_names = model_name

        if model_names is None:
            # Default list of robust open-source sentence-transformers models
            model_names = [
                "all-MiniLM-L6-v2",
                "all-mpnet-base-v2",
                "paraphrase-MiniLM-L6-v2",
            ]
        if isinstance(model_names, str):
            model_names = [model_names]

        self.model_name_loaded = None
        last_exc = None
        logger.info("🔁 Attempting to load embedding model(s): %s", model_names)
        for name in model_names:
            try:
                logger.info("   trying model: %s", name)
                self.model = SentenceTransformer(name)
                self.model_name_loaded = name
                logger.info("✅ Loaded embedding model: %s", name)
                break
            except Exception as e:
                last_exc = e
                logger.warning("⚠️ Failed to load model %s: %s", name, e)
        if self.model_name_loaded is None:
            logger.error("❌ Could not load any of the requested models. Raising last error.")
            raise last_exc

        self.vs = VectorStore(persist_directory=persist_dir)
        self.chunk_size = int(chunk_size)
        self.chunk_overlap = int(chunk_overlap)
        logger.info("✅ Embedder initialized (model=%s)", self.model_name_loaded)

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
        include_exts = include_exts or ["*.py", "*.java", "*.go", "*.js", "*.ts", "*.md", "*.txt", "*.yaml", "*.yml", "*.json", "*.puml", "*.mmd"]
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
            # If file is large, chunk it into overlapping pieces to improve embedding utility
            chunks = self._chunk_text(content, self.chunk_size, self.chunk_overlap)
            for cidx, chunk in enumerate(chunks):
                chunk_id = f"{os.path.relpath(fp, base_dir)}::{_sha256_of_file(fp)[:8]}::chunk{cidx}"
                ids.append(chunk_id)
                docs.append(chunk)
                # add metadata about source and chunking; tag diagram files specially
                meta = {"source": fp, "chunk_index": cidx, "chunk_length": len(chunk)}
                if fp.endswith('.puml') or fp.endswith('.pu'):
                    meta["type"] = "puml"
                if fp.endswith('.mmd') or fp.endswith('.mdm'):
                    meta["type"] = "mermaid"
                metadatas.append(meta)
                try:
                    emb = self.model.encode(chunk, show_progress_bar=False)
                    # ensure python list for persistence
                    embeddings.append(emb.tolist())
                except Exception as e:
                    logger.warning("⚠️ Encoding chunk failed for %s (chunk %d): %s", fp, cidx, e)
                    continue

        if docs:
            self.vs.add_documents(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
            logger.info("✅ Persisted %d code chunks to vector DB", len(ids))
        else:
            logger.warning("⚠️ No document content to embed.")

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Simple character-based chunking with overlap. Returns list of chunks.

        This is a pragmatic approach; for more accurate token-based chunking, integrate a tokenizer.
        """
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            if end >= text_len:
                break
            # move start forward but keep overlap
            start = end - overlap
        return chunks
