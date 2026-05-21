from __future__ import annotations

import json
from typing import Any

from models.database import Database


class LocalizationHistoryRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(
        self,
        video_id: int,
        source_language: str,
        target_language: str,
        transcription_accuracy: float,
        translation_accuracy: float,
        dubbing_quality: float,
        transcript_text: str,
        translated_text: str,
        output_path: str,
        segments: list[dict[str, Any]],
    ) -> int:
        return self.database.execute(
            """
            INSERT INTO LocalizationHistory (
                video_id,
                source_language,
                target_language,
                transcription_accuracy,
                translation_accuracy,
                dubbing_quality,
                completion_date,
                transcript_text,
                translated_text,
                output_path,
                segments_json
            )
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
            """,
            (
                video_id,
                source_language,
                target_language,
                transcription_accuracy,
                translation_accuracy,
                dubbing_quality,
                transcript_text,
                translated_text,
                output_path,
                json.dumps(segments),
            ),
        )

    def list_by_video(self, video_id: int) -> list[dict[str, Any]]:
        rows = self.database.fetch_all(
            "SELECT * FROM LocalizationHistory WHERE video_id = %s ORDER BY completion_date DESC, target_language ASC",
            (video_id,),
        )
        return [self.serialize(row) for row in rows]

    def find_output(self, video_id: int, target_language: str | None) -> dict[str, Any] | None:
        if target_language:
            row = self.database.fetch_one(
                """
                SELECT * FROM LocalizationHistory
                WHERE video_id = %s AND target_language = %s
                ORDER BY completion_date DESC
                LIMIT 1
                """,
                (video_id, target_language),
            )
            return self.serialize(row)

        row = self.database.fetch_one(
            "SELECT * FROM LocalizationHistory WHERE video_id = %s ORDER BY completion_date DESC LIMIT 1",
            (video_id,),
        )
        return self.serialize(row)

    @staticmethod
    def serialize(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        segments = row.get("segments_json")
        if isinstance(segments, str):
            try:
                segments = json.loads(segments)
            except json.JSONDecodeError:
                segments = []
        return {
            "history_id": row["history_id"],
            "video_id": row["video_id"],
            "source_language": row["source_language"],
            "target_language": row["target_language"],
            "transcription_accuracy": row["transcription_accuracy"],
            "translation_accuracy": row["translation_accuracy"],
            "dubbing_quality": row["dubbing_quality"],
            "completion_date": row["completion_date"],
            "transcript_text": row.get("transcript_text") or "",
            "translated_text": row.get("translated_text") or "",
            "output_path": row.get("output_path"),
            "segments": segments or [],
        }
