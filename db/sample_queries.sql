SELECT chat_id, MAX(timestamp) as last_ts, COUNT(*) AS messages
FROM messages
GROUP BY chat_id
ORDER BY last_ts DESC
LIMIT 50;


SELECT sender, agent_name, intent, message, response_json, timestamp
FROM messages
WHERE chat_id = '<chat_id_here>'
ORDER BY id ASC;
