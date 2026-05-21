from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

try:
    import mysql.connector  # type: ignore
except ImportError:  # pragma: no cover
    mysql = None
else:  # pragma: no cover
    mysql = mysql.connector


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user')),
    registration_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Videos (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    video_title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    upload_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'completed', 'failed')),
    source_language TEXT NOT NULL DEFAULT 'en',
    target_languages TEXT,
    original_filename TEXT,
    output_manifest TEXT,
    current_stage TEXT NOT NULL DEFAULT 'uploaded',
    progress INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    processing_log TEXT,
    storage_size REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS LocalizationHistory (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    transcription_accuracy REAL NOT NULL DEFAULT 0,
    translation_accuracy REAL NOT NULL DEFAULT 0,
    dubbing_quality REAL NOT NULL DEFAULT 0,
    completion_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transcript_text TEXT,
    translated_text TEXT,
    output_path TEXT,
    segments_json TEXT,
    FOREIGN KEY (video_id) REFERENCES Videos(video_id)
);

CREATE TABLE IF NOT EXISTS Feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    comments TEXT,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    feedback_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS Analytics (
    analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER NOT NULL UNIQUE,
    processing_time INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    accuracy_score REAL NOT NULL DEFAULT 0,
    storage_size REAL NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    language_breakdown_json TEXT,
    FOREIGN KEY (video_id) REFERENCES Videos(video_id)
);
"""


class Database:
    def __init__(self, config: dict):
        self.config = config
        self.driver = config["DB_DRIVER"]

    def _sqlite_path(self) -> str:
        path = Path(self.config["SQLITE_PATH"])
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    @contextmanager
    def connection(self):
        if self.driver == "mysql" and mysql is not None:
            conn = mysql.connect(
                host=self.config["MYSQL_HOST"],
                port=self.config["MYSQL_PORT"],
                user=self.config["MYSQL_USER"],
                password=self.config["MYSQL_PASSWORD"],
                database=self.config["MYSQL_DATABASE"],
            )
            try:
                yield conn
            finally:
                conn.close()
            return

        conn = sqlite3.connect(self._sqlite_path(), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _adapt_query(self, query: str) -> str:
        if self.driver == "mysql" and mysql is not None:
            return query
        return query.replace("%s", "?")

    def _cursor(self, conn):
        if self.driver == "mysql" and mysql is not None:
            return conn.cursor(dictionary=True)
        return conn.cursor()

    def execute(self, query: str, params: Iterable[Any] | None = None) -> int:
        params = tuple(params or ())
        with self.connection() as conn:
            cursor = self._cursor(conn)
            cursor.execute(self._adapt_query(query), params)
            conn.commit()
            return int(getattr(cursor, "lastrowid", 0) or 0)

    def fetch_one(self, query: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
        params = tuple(params or ())
        with self.connection() as conn:
            cursor = self._cursor(conn)
            cursor.execute(self._adapt_query(query), params)
            row = cursor.fetchone()
            if row is None:
                return None
            if isinstance(row, sqlite3.Row):
                return dict(row)
            return row

    def fetch_all(self, query: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
        params = tuple(params or ())
        with self.connection() as conn:
            cursor = self._cursor(conn)
            cursor.execute(self._adapt_query(query), params)
            rows = cursor.fetchall()
            return [dict(row) if isinstance(row, sqlite3.Row) else row for row in rows]

    def init_schema(self) -> None:
        if self.driver == "mysql" and mysql is not None:
            schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
            statements = [item.strip() for item in schema_path.read_text(encoding="utf-8").split(";") if item.strip()]
            with self.connection() as conn:
                cursor = conn.cursor()
                for statement in statements:
                    cursor.execute(statement)
                conn.commit()
            return

        with self.connection() as conn:
            conn.executescript(SQLITE_SCHEMA)
            conn.commit()
