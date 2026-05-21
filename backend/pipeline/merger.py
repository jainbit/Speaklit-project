from __future__ import annotations

import shutil
from pathlib import Path


class VideoMerger:
    def __init__(self, config: dict):
        self.config = config

    def merge(self, video_path: str, dubbed_audio_path: str, output_path: str) -> dict:
        try:
            from moviepy.editor import AudioFileClip, VideoFileClip  # type: ignore

            video = VideoFileClip(video_path)
            audio = AudioFileClip(dubbed_audio_path)
            merged = video.set_audio(audio)
            merged.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            video.close()
            audio.close()
            merged.close()
            return {"output_path": output_path, "engine": "moviepy"}
        except Exception as exc:
            if not self.config["DEMO_PIPELINE"]:
                raise
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(video_path, output_path)
            return {
                "output_path": output_path,
                "engine": "demo-copy",
                "warning": f"Video merge fallback used: {exc}",
            }
