# tools/vector_store.py
import os
import json
import logging
from typing import List, Dict, Optional

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_directory: str = "chroma_db", collection_name: str = "code_embeddings"):
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        self.collection_name = collection_name

        # Initialize PersistentClient (newer Chroma)
        try:
            logger.info("🔄 Initializing Chroma PersistentClient at %s", self.persist_directory)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            # Default embedding function wrapper (we pass raw embeddings from sentence-transformers)
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            # get_or_create_collection will create if missing
            self.collection = self.client.get_or_create_collection(name=self.collection_name, embedding_function=self.embedding_fn)
            logger.info("✅ Chroma Initialized, collection: %s", self.collection_name)
        except Exception as e:
            logger.exception("💥 Failed to initialize Chroma: %s", e)
            raise

    def add_documents(self, ids: List[str], documents: List[str], metadatas: List[Dict], embeddings: Optional[List[List[float]]] = None):
        try:
            # If embeddings are provided, use them. Otherwise Chroma will try to call embedding_function (if configured)
            if embeddings:
                self.collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
            else:
                self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
            logger.info("✅ Added %d items to Chroma collection '%s'", len(ids), self.collection_name)
        except Exception as e:
            logger.exception("💥 Error adding docs to Chroma: %s", e)
            raise

    def query(self, query_texts: List[str], n_results: int = 5):
        try:
            res = self.collection.query(query_texts=query_texts, n_results=n_results)
            logger.info("🔍 Chroma query for %d texts returned.", len(query_texts))
            return res
        except Exception as e:
            logger.exception("💥 Chroma query failed: %s", e)
            return {"ids": [], "documents": [], "metadatas": []}

    def persist(self):
        try:
            # PersistentClient persists automatically, but keep a hook
            logger.info("💾 Chroma persistence OK (PersistentClient handles on-disk state).")
        except Exception as e:
            logger.exception("⚠️ Chroma persist failed: %s", e)
