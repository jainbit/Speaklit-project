from __future__ import annotations

from typing import Any

from models.database import Database


class FeedbackRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, user_id: int, comments: str, rating: int) -> int:
        return self.database.execute(
            "INSERT INTO Feedback (user_id, comments, rating, feedback_date) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)",
            (user_id, comments, rating),
        )

    def list_by_user(self, user_id: int) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            "SELECT feedback_id, user_id, comments, rating, feedback_date FROM Feedback WHERE user_id = %s ORDER BY feedback_date DESC",
            (user_id,),
        )
