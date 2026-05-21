from __future__ import annotations

from pathlib import Path

from pipeline.common import create_silent_wav


class AudioExtractor:
    def __init__(self, config: dict):
        self.config = config

    def extract(self, video_path: str, audio_path: str) -> dict:
        try:
            from moviepy.editor import VideoFileClip  # type: ignore

            clip = VideoFileClip(video_path)
            if clip.audio is None:
                raise RuntimeError("Uploaded video does not contain an audio track.")
            clip.audio.write_audiofile(audio_path, fps=16000, codec="pcm_s16le", logger=None)
            clip.close()
            return {"audio_path": audio_path, "engine": "moviepy"}
        except Exception as exc:
            if not self.config["DEMO_PIPELINE"]:
                raise
            create_silent_wav(audio_path, duration_seconds=4.0)
            return {
                "audio_path": str(Path(audio_path)),
                "engine": "demo-fallback",
                "warning": f"Audio extraction fallback used: {exc}",
            }
