"""Saves and loads chatbot conversations in SQLite."""
from typing import Dict, List

from hotel_agent.database.connection import Database


class ConversationManager:
    def __init__(self, db: Database):
        self.db = db

    def save_message(self, session_id: str, role: str, message: str, intent: str = "") -> int:
        if role not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return self.db.execute(
            "INSERT INTO conversations (session_id, role, message, intent) VALUES (?, ?, ?, ?)",
            (session_id, role, message, intent or ""))

    def get_history(self, session_id: str, limit: int = 200) -> List[Dict]:
        rows = self.db.query(
            "SELECT * FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (session_id, int(limit)))
        return list(reversed(rows))

    def recent_messages(self, limit: int = 100) -> List[Dict]:
        return self.db.query("SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (int(limit),))

    def clear_session(self, session_id: str) -> None:
        self.db.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))

    def count(self) -> int:
        return self.db.query_one("SELECT COUNT(*) AS c FROM conversations")["c"]