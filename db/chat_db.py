# db/chat_db.py
import os
import sqlite3
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from logs.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "chat_history.db")


CREATE_MESSAGES_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    agent_name TEXT,
    intent TEXT,
    message TEXT,
    response_json TEXT,
    timestamp TEXT NOT NULL
);
"""

def _get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize database and tables if not exist."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(CREATE_MESSAGES_SQL)
        conn.commit()
        conn.close()
        logger.info("Initialized DB at %s", DB_PATH)
    except Exception as e:
        logger.exception("init_db failed: %s", e)


def save_message(chat_id: str, sender: str, agent_name: Optional[str], intent: Optional[str], message: str, response_json: Optional[Dict]=None) -> int:
    """Insert a message row. Returns inserted row id."""
    ts = datetime.utcnow().isoformat() + "Z"
    rjson = json.dumps(response_json, ensure_ascii=False) if response_json is not None else None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (chat_id, sender, agent_name, intent, message, response_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (chat_id, sender, agent_name, intent, message, rjson, ts)
        )
        conn.commit()
        rowid = cur.lastrowid
        conn.close()
        logger.info("Saved message id=%s chat=%s sender=%s agent=%s", rowid, chat_id, sender, agent_name)
        return rowid
    except Exception as e:
        logger.exception("save_message failed: %s", e)
        raise


def list_chats(limit: int = 200) -> List[Dict[str, Any]]:
    """
    Return a list of distinct chats with latest metadata.
    Each item: {chat_id, last_message_ts, last_sender, last_agent, intent_sample, message_count}
    """
    try:
        conn = _get_conn()
        cur = conn.cursor()
        # get top chats by latest timestamp
        cur.execute("""
            SELECT chat_id,
                   MAX(timestamp) as last_ts,
                   SUM(1) as message_count,
                   MAX(agent_name) as last_agent,
                   MAX(intent) as intent_sample
            FROM messages
            GROUP BY chat_id
            ORDER BY last_ts DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        out = []
        for r in rows:
            out.append({
                "chat_id": r[0],
                "last_ts": r[1],
                "message_count": r[2],
                "last_agent": r[3],
                "intent_sample": r[4]
            })
        return out
    except Exception as e:
        logger.exception("list_chats failed: %s", e)
        return []


def get_chat_messages(chat_id: str) -> List[Dict[str, Any]]:
    """Return ordered messages for a chat_id."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, sender, agent_name, intent, message, response_json, timestamp FROM messages WHERE chat_id=? ORDER BY id ASC", (chat_id,))
        rows = cur.fetchall()
        conn.close()
        out = []
        for r in rows:
            out.append({
                "id": r[0],
                "sender": r[1],
                "agent_name": r[2],
                "intent": r[3],
                "message": r[4],
                "response_json": json.loads(r[5]) if r[5] else None,
                "timestamp": r[6]
            })
        return out
    except Exception as e:
        logger.exception("get_chat_messages failed: %s", e)
        return []


def get_all_messages() -> List[Dict[str, Any]]:
    """Return all message rows (careful with large DBs)."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, chat_id, sender, agent_name, intent, message, response_json, timestamp FROM messages ORDER BY id ASC")
        rows = cur.fetchall()
        conn.close()
        out = []
        for r in rows:
            out.append({
                "id": r[0],
                "chat_id": r[1],
                "sender": r[2],
                "agent_name": r[3],
                "intent": r[4],
                "message": r[5],
                "response_json": json.loads(r[6]) if r[6] else None,
                "timestamp": r[7]
            })
        return out
    except Exception as e:
        logger.exception("get_all_messages failed: %s", e)
        return []


def delete_chat(chat_id: str):
    """Delete all messages for chat_id."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
        conn.commit()
        conn.close()
        logger.warning("Deleted chat %s", chat_id)
    except Exception as e:
        logger.exception("delete_chat failed: %s", e)
        raise


def delete_all_chats():
    """Delete all messages in DB."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
        logger.warning("Deleted all chats from DB.")
    except Exception as e:
        logger.exception("delete_all_chats failed: %s", e)
        raise


def export_chat_to_file(chat_id: str, out_path: str):
    """Export a single chat (messages) to JSON lines (or JSON array) at out_path."""
    try:
        msgs = get_chat_messages(chat_id)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(msgs, fh, ensure_ascii=False, indent=2)
        logger.info("Exported chat %s to %s", chat_id, out_path)
    except Exception as e:
        logger.exception("export_chat_to_file failed: %s", e)
        raise


def export_all_chats_csv(out_path: str):
    """
    Export all chats into a CSV with columns:
    id, chat_id, sender, agent_name, intent, message, response_json, timestamp
    """
    try:
        all_msgs = get_all_messages()
        with open(out_path, "w", encoding="utf-8", newline="") as csvfile:
            fieldnames = ["id", "chat_id", "sender", "agent_name", "intent", "message", "response_json", "timestamp"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for m in all_msgs:
                row = m.copy()
                row["response_json"] = json.dumps(row["response_json"], ensure_ascii=False) if row.get("response_json") else ""
                writer.writerow(row)
        logger.info("Exported all chats to CSV: %s", out_path)
    except Exception as e:
        logger.exception("export_all_chats_csv failed: %s", e)
        raise
