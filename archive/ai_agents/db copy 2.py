# UNUSED BACKUP FILE - ai_agents/db copy 2.py (moved to archive)
# Original content preserved for review.

# ai_agents/db.py
import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chats.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


class ChatDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Ensure DB schema exists."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT,              -- 'user' or 'agent'
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id)
                )
                """
            )
            conn.commit()

    def add_chat(self, user_query: str, agent_name: str, agent_response: str):
        """Insert a new chat record and return its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO chats (user_query, agent_name, agent_response, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_query, agent_name, agent_response, datetime.now()),
                )
                conn.commit()
                chat_id = cur.lastrowid
                logger.info("💬 Chat added — ID=%s | Agent=%s", chat_id, agent_name)
                return chat_id
        except Exception as e:
            logger.exception("DB insert failed: %s", e)
            return None

    def get_all_chats(self):
        """Retrieve all chat records sorted by creation time (desc)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, user_query, agent_name, agent_response, created_at
                    FROM chats WHERE id IS NOT NULL
                    ORDER BY created_at DESC
                    """
                )
                return cur.fetchall()
        except Exception as e:
            logger.exception("DB fetch failed: %s", e)
            return []

    def get_chat_by_id(self, chat_id: int):
        """Retrieve a specific chat record."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, user_query, agent_name, agent_response, created_at FROM chats WHERE id = ?",
                    (chat_id,),
                )
                return cur.fetchone()
        except Exception as e:
            logger.exception("DB get_chat_by_id failed: %s", e)
            return None
