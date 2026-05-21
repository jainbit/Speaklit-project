from __future__ import annotations

from pathlib import Path


class WhisperTranscriber:
    def __init__(self, config: dict):
        self.config = config

    def transcribe(self, audio_path: str, source_language: str) -> dict:
        try:
            import whisper  # type: ignore

            model = whisper.load_model(self.config["WHISPER_MODEL_SIZE"])
            result = model.transcribe(audio_path, language=source_language)
            segments = [
                {"start": segment["start"], "end": segment["end"], "text": segment["text"].strip()}
                for segment in result.get("segments", [])
            ]
            return {
                "engine": f"whisper-{self.config['WHISPER_MODEL_SIZE']}",
                "text": result.get("text", "").strip(),
                "segments": segments,
            }
        except Exception as exc:
            if not self.config["DEMO_PIPELINE"]:
                raise
            title = Path(audio_path).stem.replace("_", " ").replace("-", " ").title()
            segments = [
                {
                    "start": 0.0,
                    "end": 2.2,
                    "text": f"Welcome to SpeakIt. This demo transcript was generated for {title}.",
                },
                {
                    "start": 2.2,
                    "end": 4.8,
                    "text": "Your video can be transcribed, translated, and dubbed into multiple languages.",
                },
            ]
            return {
                "engine": "demo-fallback",
                "warning": f"Whisper fallback used: {exc}",
                "text": " ".join(item["text"] for item in segments),
                "segments": segments,
            }
