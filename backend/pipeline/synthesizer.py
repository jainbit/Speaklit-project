from __future__ import annotations

from pathlib import Path

from pipeline.common import SUPPORTED_LANGUAGES, create_silent_wav


class SpeechSynthesizer:
    def __init__(self, config: dict):
        self.config = config

    def synthesize(self, segments: list[dict], target_language: str, output_path: str) -> dict:
        try:
            from gtts import gTTS  # type: ignore
            from pydub import AudioSegment  # type: ignore

            combined = AudioSegment.silent(duration=0)
            current_length = 0
            temp_root = Path(self.config["TEMP_FOLDER"]) / "tts_segments"
            temp_root.mkdir(parents=True, exist_ok=True)

            for index, segment in enumerate(segments):
                start_ms = int(float(segment["start"]) * 1000)
                if start_ms > current_length:
                    combined += AudioSegment.silent(duration=start_ms - current_length)
                    current_length = len(combined)

                temp_file = temp_root / f"{Path(output_path).stem}_{index}.mp3"
                tts = gTTS(text=segment["translated_text"], lang=SUPPORTED_LANGUAGES[target_language]["tts_code"])
                tts.save(str(temp_file))
                spoken = AudioSegment.from_file(temp_file)
                combined += spoken
                current_length = len(combined)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            combined.export(output_path, format="mp3")
            return {"audio_path": output_path, "engine": "gtts+pydub"}
        except Exception as exc:
            if not self.config["DEMO_PIPELINE"]:
                raise
            total_duration = max([float(item["end"]) for item in segments] + [3.0])
            create_silent_wav(output_path, duration_seconds=total_duration)
            return {
                "audio_path": output_path,
                "engine": "demo-fallback",
                "warning": f"TTS fallback used: {exc}",
            }
