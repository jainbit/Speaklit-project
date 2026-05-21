from __future__ import annotations

import logging
import os
import wave
from pathlib import Path
from typing import Any


LOGGER = logging.getLogger(__name__)
_WHISPER_MODELS: dict[str, Any] = {}
_WHISPER_IMPORT_ERROR: Exception | None = None


def _get_whisper_model(model_size: str):
    global _WHISPER_IMPORT_ERROR

    if model_size in _WHISPER_MODELS:
        return _WHISPER_MODELS[model_size]

    try:
        import whisper  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime installation
        _WHISPER_IMPORT_ERROR = exc
        raise

    model = whisper.load_model(model_size)
    _WHISPER_MODELS[model_size] = model
    return model


def _maybe_preload_default_model() -> None:
    if os.getenv("USE_REAL_WHISPER", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return

    try:
        _get_whisper_model(os.getenv("SPEAKIT_WHISPER_MODEL", "base"))
    except Exception as exc:  # pragma: no cover - best effort preload
        LOGGER.warning("Unable to preload Whisper model at import time: %s", exc)


def _load_audio_for_whisper(audio_path: str):
    if Path(audio_path).suffix.lower() != ".wav":
        return audio_path

    try:
        import numpy as np  # type: ignore

        with wave.open(audio_path, "rb") as audio_file:
            channels = audio_file.getnchannels()
            sample_width = audio_file.getsampwidth()
            frame_rate = audio_file.getframerate()
            frames = audio_file.readframes(audio_file.getnframes())

        if sample_width != 2 or frame_rate <= 0:
            return audio_path

        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
        return audio
    except Exception as exc:  # pragma: no cover - fallback to file path
        LOGGER.warning("Falling back to Whisper file-path loading for %s: %s", audio_path, exc)
        return audio_path


class WhisperTranscriber:
    def __init__(self, config: dict):
        self.config = config

    def transcribe(self, audio_path: str, source_language: str) -> dict:
        use_real_whisper = (
            self.config.get("USE_REAL_WHISPER", False) or self.config.get("USE_REAL_PIPELINE", False)
        ) and not self.config.get("DEMO_PIPELINE", False)
        if not use_real_whisper:
            return self._demo_transcript(audio_path, "Whisper fallback used because demo pipeline mode is enabled.")

        try:
            model = _get_whisper_model(self.config["WHISPER_MODEL_SIZE"])
            audio_input = _load_audio_for_whisper(audio_path)
            result = model.transcribe(audio_input, language=source_language)
            segments = [
                {
                    "start": float(segment.get("start", 0.0)),
                    "end": float(segment.get("end", 0.0)),
                    "text": (segment.get("text") or "").strip(),
                }
                for segment in result.get("segments", [])
            ]
            return {
                "engine": f"whisper-{self.config['WHISPER_MODEL_SIZE']}",
                "text": (result.get("text") or "").strip(),
                "segments": segments,
                "language": result.get("language", source_language or "en"),
            }
        except Exception as exc:  # pragma: no cover - runtime dependent
            LOGGER.exception("Real Whisper transcription failed for %s", audio_path)
            return {
                "engine": "whisper-error",
                "warning": f"Real Whisper transcription failed: {exc}",
                "text": "",
                "segments": [],
                "language": "en",
            }

    def _demo_transcript(self, audio_path: str, warning: str) -> dict:
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
            "warning": warning,
            "text": " ".join(item["text"] for item in segments),
            "segments": segments,
            "language": "en",
        }


_maybe_preload_default_model()
