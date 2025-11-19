# ai_agents/db.py
import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# default DB path (from config you pass into ChatDB constructor in main)
DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "chats.db")
os.makedirs(os.path.dirname(DEFAULT_DB), exist_ok=True)


class ChatDB:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def _init_db(self):
        """Ensure DB schema exists. Keeps your original chats table."""
        try:
            conn = self._get_conn()
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
            # Optional messages table for multi-turn conversation
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats(id)
                )
                """
            )
            conn.commit()
            conn.close()
            logger.info("DB initialized at %s", self.db_path)
        except Exception as e:
            logger.exception("Failed to init DB: %s", e)

    # --- Chat operations (compatible with your existing usage) ---
    def add_chat(self, user_query: str, agent_name: str, agent_response: str):
        """Insert a new chat record and return its ID."""
        try:
            conn = self._get_conn()
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
            conn.close()
            logger.info("💬 Chat added — ID=%s | Agent=%s", chat_id, agent_name)
            return chat_id
        except Exception as e:
            logger.exception("DB insert failed: %s", e)
            return None

    def get_all_chats(self):
        """Return all chats ordered desc by created_at (matches your UI expectation)"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, user_query, agent_name, agent_response, created_at
                FROM chats
                ORDER BY created_at DESC
                """
            )
            rows = cur.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.exception("DB fetch failed: %s", e)
            return []

    def get_chat_by_id(self, chat_id: int):
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, user_query, agent_name, agent_response, created_at FROM chats WHERE id = ?",
                (chat_id,),
            )
            row = cur.fetchone()
            conn.close()
            return row
        except Exception as e:
            logger.exception("DB get_chat_by_id failed: %s", e)
            return None

    def update_chat_response(self, chat_id: int, agent_name: str, agent_response: str):
        """Update the chats summary row with latest agent response."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE chats SET agent_name = ?, agent_response = ?, created_at = ?
                WHERE id = ?
                """,
                (agent_name, agent_response, datetime.now(), chat_id),
            )
            conn.commit()
            conn.close()
            logger.info("Chat %s updated with agent response", chat_id)
        except Exception as e:
            logger.exception("update_chat_response failed: %s", e)

    # --- Messages table for multi-turn — optional but preferred ---
    def add_message(self, chat_id: int, role: str, content: str):
        """Insert message into messages table for multi-turn dialogues."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, datetime.now()),
            )
            conn.commit()
            conn.close()
            logger.info("Message added to chat %s role=%s", chat_id, role)
        except Exception as e:
            logger.exception("add_message failed: %s", e)

    def get_chat_messages(self, chat_id: int):
        """Return list of (role, content, created_at), ordered ascending by time."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
                (chat_id,),
            )
            rows = cur.fetchall()
            conn.close()
            return rows
        except Exception as e:
            logger.exception("get_chat_messages failed: %s", e)
            return []
