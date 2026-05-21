from __future__ import annotations

from typing import Any

from models.database import Database


class UserRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, username: str, password: str, email: str, role: str = "user") -> int:
        return self.database.execute(
            """
            INSERT INTO Users (username, password, email, role, registration_date)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (username, password, email, role),
        )

    def get_by_username(self, username: str) -> dict[str, Any] | None:
        return self.database.fetch_one("SELECT * FROM Users WHERE username = %s", (username,))

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        return self.database.fetch_one("SELECT * FROM Users WHERE email = %s", (email,))

    def get_by_id(self, user_id: int) -> dict[str, Any] | None:
        return self.database.fetch_one(
            "SELECT user_id, username, email, role, registration_date FROM Users WHERE user_id = %s",
            (user_id,),
        )

    @staticmethod
    def serialize_public(user: dict[str, Any] | None) -> dict[str, Any] | None:
        if not user:
            return None
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "registration_date": user["registration_date"],
        }
