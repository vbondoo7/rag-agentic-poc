# ai_agents/embedding_agent.py
import logging
from typing import List, Dict, Any
from tools.vector_store import VectorStore

logger = logging.getLogger(__name__)

class EmbeddingRAG:
    def __init__(self, persist_directory: str = "chroma_db"):
        self.persist_directory = persist_directory
        self.vs = VectorStore(persist_directory=self.persist_directory)
        self.db = None

    def build_index(self, folders: List[str]) -> Any:
        """
        Build or update the vector index from folder list.
        Returns the Chroma DB instance.
        """
        logger.info("Building vector index for folders: %s", folders)
        docs = self.vs.load_files(folders)
        if not docs:
            logger.info("No changed docs; loading existing DB")
            self.db = self.vs.load_vector_store()
            return self.db
        self.db = self.vs.create_vector_store(docs)
        logger.info("Vector DB built with %d docs", len(docs))
        return self.db

    def get_retriever(self, k: int = 5):
        """
        Return a retriever object (as_retriever) for RAG queries.
        """
        if not self.db:
            self.db = self.vs.load_vector_store()
        try:
            retriever = self.db.as_retriever(search_kwargs={"k": k})
            return retriever
        except Exception:
            # fallback to similarity_search wrapper
            class SimpleRetriever:
                def __init__(self, db, k):
                    self.db = db
                    self.k = k
                def get_relevant_documents(self, query):
                    try:
                        return self.db.similarity_search(query, k=self.k)
                    except Exception:
                        return []
            return SimpleRetriever(self.db, k)
