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

    # ---------- chats table helpers ----------
    def add_chat(self, user_query: str, agent_name: str, agent_response: str) -> Optional[int]:
        """
        Insert a new chat record (summary) and return its ID.
        We still insert a chats row for backward compatibility and quick listing.
        """
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
            logger.exception("DB insert (chats) failed: %s", e)
            return None

    def get_all_chats(self, limit: Optional[int] = None) -> List[Tuple]:
        """
        Retrieve all chat summary records sorted by creation time (desc).
        Returns list of tuples: (id, user_query, agent_name, agent_response, created_at)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                q = "SELECT id, user_query, agent_name, agent_response, created_at FROM chats ORDER BY created_at DESC"
                if limit:
                    q += f" LIMIT {int(limit)}"
                cur.execute(q)
                rows = cur.fetchall()
                logger.debug("Fetched %d chat summaries", len(rows))
                return rows
        except Exception as e:
            logger.exception("DB fetch (chats) failed: %s", e)
            return []

    def get_chat_by_id(self, chat_id: int) -> Optional[Tuple]:
        """
        Retrieve a specific chat summary.
        returns (id, user_query, agent_name, agent_response, created_at) or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, user_query, agent_name, agent_response, created_at FROM chats WHERE id = ?",
                    (chat_id,),
                )
                row = cur.fetchone()
                return row
        except Exception as e:
            logger.exception("DB get_chat_by_id failed: %s", e)
            return None

    # ---------- messages table helpers ----------
    def add_message(self, chat_id: int, role: str, content: str) -> Optional[int]:
        """
        Append a message (user or agent) to messages table under chat_id.
        Returns message id.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO messages (chat_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (chat_id, role, content, datetime.now()),
                )
                conn.commit()
                mid = cur.lastrowid
                logger.info("💬 Message added — chat_id=%s message_id=%s role=%s", chat_id, mid, role)
                return mid
        except Exception as e:
            logger.exception("DB insert (messages) failed: %s", e)
            return None

    def get_chat_messages(self, chat_id: int) -> List[Tuple]:
        """
        Get ordered messages for a chat.
        returns list of tuples (role, content, created_at)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at ASC",
                    (chat_id,),
                )
                rows = cur.fetchall()
                logger.debug("Fetched %d messages for chat_id=%s", len(rows), chat_id)
                return rows
        except Exception as e:
            logger.exception("DB fetch (messages) failed: %s", e)
            return []

    # convenience: create chat + first message + agent response as atomic operation
    def create_chat_with_messages(self, user_query: str, agent_name: str, agent_response: str) -> Optional[int]:
        """
        Create a chat row and create two message rows (user and agent). Returns chat_id.
        Useful to create everything in one go.
        """
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
                chat_id = cur.lastrowid
                cur.execute(
                    """
                    INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)
                    """,
                    (chat_id, "user", user_query, datetime.now()),
                )
                cur.execute(
                    """
                    INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)
                    """,
                    (chat_id, "agent", agent_response, datetime.now()),
                )
                conn.commit()
                logger.info("💾 Created chat_id=%s with initial messages", chat_id)
                return chat_id
        except Exception as e:
            logger.exception("Failed to create chat with messages: %s", e)
            return None
