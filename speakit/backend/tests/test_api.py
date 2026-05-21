from __future__ import annotations

import io
import tempfile
import time
import unittest
from pathlib import Path

from app import create_app


class SpeakItApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.app = create_app(
            {
                "TESTING": True,
                "DEBUG": False,
                "DB_DRIVER": "sqlite",
                "SQLITE_PATH": str(root / "speakit-test.db"),
                "UPLOAD_FOLDER": str(root / "uploads"),
                "OUTPUT_FOLDER": str(root / "outputs"),
                "TEMP_FOLDER": str(root / "temp"),
                "AUTO_INIT_DB": True,
                "DEMO_PIPELINE": True,
                "JWT_SECRET": "test-secret",
                "SECRET_KEY": "test-secret",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _register(self):
        response = self.client.post(
            "/api/auth/register",
            json={"username": "ava", "email": "ava@example.com", "password": "secret123"},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        return payload["token"], payload["user"]["user_id"]

    def test_end_to_end_demo_pipeline(self):
        token, user_id = self._register()
        headers = {"Authorization": f"Bearer {token}"}

        upload_response = self.client.post(
            "/api/videos/upload",
            data={
                "video_title": "Quarterly Update",
                "source_language": "en",
                "target_languages": '["fr","hi"]',
                "video": (io.BytesIO(b"fake video payload"), "quarterly-update.mp4"),
            },
            headers=headers,
            content_type="multipart/form-data",
        )
        self.assertEqual(upload_response.status_code, 201)
        video_id = upload_response.get_json()["video"]["video_id"]

        process_response = self.client.post(f"/api/videos/{video_id}/process", headers=headers)
        self.assertEqual(process_response.status_code, 202)

        deadline = time.time() + 5
        final_status = None
        while time.time() < deadline:
            status_response = self.client.get(f"/api/videos/{video_id}/status", headers=headers)
            self.assertEqual(status_response.status_code, 200)
            final_status = status_response.get_json()["video"]
            if final_status["status"] == "completed":
                break
            time.sleep(0.2)

        self.assertIsNotNone(final_status)
        self.assertEqual(final_status["status"], "completed")

        detail_response = self.client.get(f"/api/videos/{video_id}", headers=headers)
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.get_json()
        self.assertEqual(len(detail_payload["histories"]), 2)
        self.assertIsNotNone(detail_payload["analytics"])

        analytics_response = self.client.get(f"/api/analytics/{user_id}", headers=headers)
        self.assertEqual(analytics_response.status_code, 200)
        self.assertGreaterEqual(analytics_response.get_json()["summary"]["videos_processed"], 1)

        feedback_response = self.client.post(
            "/api/feedback",
            headers=headers,
            json={"rating": 5, "comments": "Great localization flow."},
        )
        self.assertEqual(feedback_response.status_code, 201)

    def test_upload_accepts_webm_video(self):
        token, _user_id = self._register()

        upload_response = self.client.post(
            "/api/videos/upload",
            data={
                "video_title": "Browser Recording",
                "source_language": "en",
                "target_languages": '["fr"]',
                "video": (io.BytesIO(b"fake webm payload"), "browser-recording.webm"),
            },
            headers={"Authorization": f"Bearer {token}"},
            content_type="multipart/form-data",
        )

        self.assertEqual(upload_response.status_code, 201)
        self.assertEqual(upload_response.get_json()["video"]["original_filename"], "browser-recording.webm")


if __name__ == "__main__":
    unittest.main()
