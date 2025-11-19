-- db/schema.sql
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,          -- session / conversation id (UUID or timestamp)
    sender TEXT NOT NULL,           -- "user" or "assistant" or "system"
    agent_name TEXT,                -- which agent produced the response (impact, blueprint, understanding)
    intent TEXT,                    -- detected intent (impact|blueprint|understanding|generic)
    message TEXT,                   -- original user message (or assistant text when needed)
    response_json TEXT,             -- JSON string if agent produced structured JSON (nullable)
    timestamp TEXT NOT NULL         -- ISO timestamp when saved
);

-- Optional index for fast lookups by chat_id
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages (chat_id);

COMMIT;
