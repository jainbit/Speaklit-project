from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


SUPPORTED_LANGUAGES = {
    "en": {"label": "English", "tts_code": "en", "model": None},
    "es": {"label": "Spanish", "tts_code": "es", "model": "Helsinki-NLP/opus-mt-en-es"},
    "fr": {"label": "French", "tts_code": "fr", "model": "Helsinki-NLP/opus-mt-en-fr"},
    "de": {"label": "German", "tts_code": "de", "model": "Helsinki-NLP/opus-mt-en-de"},
    "hi": {"label": "Hindi", "tts_code": "hi", "model": "Helsinki-NLP/opus-mt-en-hi"},
    "ja": {"label": "Japanese", "tts_code": "ja", "model": "Helsinki-NLP/opus-mt-en-jap"},
    "it": {"label": "Italian", "tts_code": "it", "model": "Helsinki-NLP/opus-mt-en-it"},
    "pt": {"label": "Portuguese", "tts_code": "pt", "model": "Helsinki-NLP/opus-mt-en-pt"},
    "zh": {"label": "Chinese", "tts_code": "zh-CN", "model": "Helsinki-NLP/opus-mt-en-zh"},
    "ar": {"label": "Arabic", "tts_code": "ar", "model": "Helsinki-NLP/opus-mt-en-ar"},
}


def create_tone_wav(destination: str, duration_seconds: float = 3.0, sample_rate: int = 16000) -> str:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for index in range(frames):
            amplitude = int(1200 * math.sin(2.0 * math.pi * 440.0 * (index / sample_rate)))
            handle.writeframes(struct.pack("<h", amplitude))
    return str(path)


def create_silent_wav(destination: str, duration_seconds: float = 3.0, sample_rate: int = 16000) -> str:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration_seconds * sample_rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)
    return str(path)
