from __future__ import annotations

import json
from typing import Any

from models.database import Database


class AnalyticsRepository:
    def __init__(self, database: Database):
        self.database = database

    def upsert(
        self,
        video_id: int,
        processing_time: int,
        word_count: int,
        accuracy_score: float,
        storage_size: float,
        language_breakdown: list[dict[str, Any]],
    ) -> None:
        existing = self.database.fetch_one("SELECT analytics_id FROM Analytics WHERE video_id = %s", (video_id,))
        if existing:
            self.database.execute(
                """
                UPDATE Analytics
                SET processing_time = %s,
                    word_count = %s,
                    accuracy_score = %s,
                    storage_size = %s,
                    last_updated = CURRENT_TIMESTAMP,
                    language_breakdown_json = %s
                WHERE video_id = %s
                """,
                (processing_time, word_count, accuracy_score, storage_size, json.dumps(language_breakdown), video_id),
            )
            return

        self.database.execute(
            """
            INSERT INTO Analytics (
                video_id,
                processing_time,
                word_count,
                accuracy_score,
                storage_size,
                last_updated,
                language_breakdown_json
            )
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
            """,
            (video_id, processing_time, word_count, accuracy_score, storage_size, json.dumps(language_breakdown)),
        )

    def get_video_analytics(self, video_id: int) -> dict[str, Any] | None:
        return self.serialize(self.database.fetch_one("SELECT * FROM Analytics WHERE video_id = %s", (video_id,)))

    def get_user_dashboard(self, user_id: int) -> dict[str, Any]:
        videos = self.database.fetch_all(
            """
            SELECT v.video_id, v.video_title, v.status, v.current_stage, v.progress, v.upload_date,
                   a.processing_time, a.word_count, a.accuracy_score, a.storage_size,
                   a.last_updated, a.language_breakdown_json
            FROM Videos v
            LEFT JOIN Analytics a ON a.video_id = v.video_id
            WHERE v.user_id = %s
            ORDER BY v.upload_date DESC
            """,
            (user_id,),
        )
        language_scores = self.database.fetch_all(
            """
            SELECT h.target_language,
                   AVG(h.transcription_accuracy) AS avg_transcription_accuracy,
                   AVG(h.translation_accuracy) AS avg_translation_accuracy,
                   AVG(h.dubbing_quality) AS avg_dubbing_quality
            FROM LocalizationHistory h
            JOIN Videos v ON v.video_id = h.video_id
            WHERE v.user_id = %s
            GROUP BY h.target_language
            ORDER BY h.target_language ASC
            """,
            (user_id,),
        )
        status_breakdown = self.database.fetch_all(
            "SELECT status, COUNT(*) AS total FROM Videos WHERE user_id = %s GROUP BY status",
            (user_id,),
        )

        measured_items = [item for item in videos if item.get("accuracy_score") is not None]
        summary = {
            "videos_processed": len(videos),
            "completed_videos": sum(1 for item in videos if item["status"] == "completed"),
            "average_accuracy": round(
                sum((item.get("accuracy_score") or 0) for item in measured_items) / max(1, len(measured_items)),
                3,
            ),
            "average_processing_time": round(
                sum((item.get("processing_time") or 0) for item in measured_items) / max(1, len(measured_items)),
                1,
            ),
        }

        return {
            "summary": summary,
            "video_metrics": [self._serialize_video_metric(item) for item in videos],
            "language_pairs": [
                {
                    "target_language": item["target_language"],
                    "transcription_accuracy": round(item["avg_transcription_accuracy"] or 0, 3),
                    "translation_accuracy": round(item["avg_translation_accuracy"] or 0, 3),
                    "dubbing_quality": round(item["avg_dubbing_quality"] or 0, 3),
                }
                for item in language_scores
            ],
            "activity_breakdown": [{"status": item["status"], "total": item["total"]} for item in status_breakdown],
        }

    @staticmethod
    def serialize(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        breakdown = row.get("language_breakdown_json")
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except json.JSONDecodeError:
                breakdown = []
        return {
            "analytics_id": row["analytics_id"],
            "video_id": row["video_id"],
            "processing_time": row["processing_time"],
            "word_count": row["word_count"],
            "accuracy_score": row["accuracy_score"],
            "storage_size": row["storage_size"],
            "last_updated": row["last_updated"],
            "language_breakdown": breakdown or [],
        }

    def _serialize_video_metric(self, row: dict[str, Any]) -> dict[str, Any]:
        breakdown = row.get("language_breakdown_json")
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except json.JSONDecodeError:
                breakdown = []
        return {
            "video_id": row["video_id"],
            "video_title": row["video_title"],
            "status": row["status"],
            "current_stage": row["current_stage"],
            "progress": row["progress"],
            "upload_date": row["upload_date"],
            "processing_time": row.get("processing_time") or 0,
            "word_count": row.get("word_count") or 0,
            "accuracy_score": row.get("accuracy_score") or 0,
            "storage_size": row.get("storage_size") or 0,
            "last_updated": row.get("last_updated"),
            "language_breakdown": breakdown or [],
        }
