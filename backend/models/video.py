from __future__ import annotations

import json
from typing import Any

from models.database import Database


class VideoRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
        user_id: int,
        video_title: str,
        file_path: str,
        source_language: str,
        target_languages: list[str],
        original_filename: str,
        storage_size: float,
    ) -> int:
        return self.database.execute(
            """
            INSERT INTO Videos (
                user_id,
                video_title,
                file_path,
                upload_date,
                status,
                source_language,
                target_languages,
                original_filename,
                output_manifest,
                current_stage,
                progress,
                processing_log,
                storage_size,
                updated_at
            )
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                video_title,
                file_path,
                "pending",
                source_language,
                json.dumps(target_languages),
                original_filename,
                json.dumps([]),
                "uploaded",
                0,
                json.dumps([]),
                storage_size,
            ),
        )

    def list_by_user(self, user_id: int) -> list[dict[str, Any]]:
        return self.database.fetch_all(
            """
            SELECT video_id, user_id, video_title, file_path, upload_date, status, source_language,
                   target_languages, output_manifest, current_stage, progress, error_message,
                   processing_log, storage_size, updated_at, original_filename
            FROM Videos
            WHERE user_id = %s
            ORDER BY upload_date DESC
            """,
            (user_id,),
        )

    def get_by_id(self, video_id: int) -> dict[str, Any] | None:
        return self.database.fetch_one("SELECT * FROM Videos WHERE video_id = %s", (video_id,))

    def update_processing_state(
        self,
        video_id: int,
        *,
        status: str | None = None,
        current_stage: str | None = None,
        progress: int | None = None,
        error_message: str | None = None,
        output_manifest: list[dict[str, Any]] | None = None,
    ) -> None:
        video = self.get_by_id(video_id)
        if not video:
            return

        next_status = status or video["status"]
        next_stage = current_stage or video["current_stage"]
        next_progress = video["progress"] if progress is None else progress
        next_manifest = output_manifest
        if next_manifest is None:
            next_manifest = self._load_json(video.get("output_manifest"), default=[])

        self.database.execute(
            """
            UPDATE Videos
            SET status = %s,
                current_stage = %s,
                progress = %s,
                error_message = %s,
                output_manifest = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE video_id = %s
            """,
            (next_status, next_stage, next_progress, error_message, json.dumps(next_manifest), video_id),
        )

    def append_log(self, video_id: int, message: str) -> None:
        video = self.get_by_id(video_id)
        if not video:
            return
        logs = self._load_json(video.get("processing_log"), default=[])
        logs.append(message)
        self.database.execute(
            "UPDATE Videos SET processing_log = %s, updated_at = CURRENT_TIMESTAMP WHERE video_id = %s",
            (json.dumps(logs), video_id),
        )

    def set_output_manifest(self, video_id: int, manifest: list[dict[str, Any]]) -> None:
        self.database.execute(
            "UPDATE Videos SET output_manifest = %s, updated_at = CURRENT_TIMESTAMP WHERE video_id = %s",
            (json.dumps(manifest), video_id),
        )

    @staticmethod
    def _load_json(value: Any, default: Any):
        if not value:
            return default
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default

    def serialize(self, video: dict[str, Any] | None) -> dict[str, Any] | None:
        if not video:
            return None
        return {
            "video_id": video["video_id"],
            "user_id": video["user_id"],
            "video_title": video["video_title"],
            "file_path": video["file_path"],
            "upload_date": video["upload_date"],
            "status": video["status"],
            "source_language": video.get("source_language", "en"),
            "target_languages": self._load_json(video.get("target_languages"), default=[]),
            "output_manifest": self._load_json(video.get("output_manifest"), default=[]),
            "current_stage": video.get("current_stage", "uploaded"),
            "progress": video.get("progress", 0),
            "error_message": video.get("error_message"),
            "logs": self._load_json(video.get("processing_log"), default=[]),
            "storage_size": video.get("storage_size", 0),
            "updated_at": video.get("updated_at"),
            "original_filename": video.get("original_filename"),
        }
