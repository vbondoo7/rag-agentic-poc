# UNUSED BACKUP FILE - ai_agents/db copy.py (moved to archive)
# Original content preserved for review.

# ai_agents/db.py
import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chats.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


class ChatDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Ensure DB schema exists (preserve existing chats table)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                # keep chats table exactly as requested
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_query TEXT,
                        agent_name TEXT,
                        agent_response TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                # messages table to store turn-level messages (multi-turn)
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        role TEXT,              -- 'user' or 'agent'
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
                    )
                    """
                )
                conn.commit()
            logger.info("DB initialized at %s", self.db_path)
        except Exception as e:
            logger.exception("Failed to initialize DB: %s", e)
            raise

    # ... (rest of original content omitted in archive copy) 
