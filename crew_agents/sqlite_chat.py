"""
SQLite chat storage for CrewAI chat UI.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/chats.db')

class ChatDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            agent_name TEXT,
            agent_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()

    def add_chat(self, user_query, agent_name, agent_response):
        c = self.conn.cursor()
        c.execute('INSERT INTO chats (user_query, agent_name, agent_response) VALUES (?, ?, ?)',
                  (user_query, agent_name, agent_response))
        chat_id = c.lastrowid
        self.conn.commit()
        return chat_id

    def add_message(self, chat_id, role, content):
        c = self.conn.cursor()
        c.execute('INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)',
                  (chat_id, role, content))
        self.conn.commit()

    def get_all_chats(self):
        c = self.conn.cursor()
        c.execute('SELECT id, user_query, agent_name, agent_response, created_at FROM chats ORDER BY id DESC')
        return c.fetchall()

    def get_chat_by_id(self, chat_id):
        c = self.conn.cursor()
        c.execute('SELECT id, user_query, agent_name, agent_response, created_at FROM chats WHERE id=?', (chat_id,))
        return c.fetchone()

    def get_chat_messages(self, chat_id):
        c = self.conn.cursor()
        c.execute('SELECT role, content, created_at FROM messages WHERE chat_id=? ORDER BY id ASC', (chat_id,))
        return c.fetchall()
