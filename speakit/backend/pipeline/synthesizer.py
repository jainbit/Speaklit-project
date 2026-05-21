from __future__ import annotations

import logging
from pathlib import Path

from pipeline.common import create_tone_wav


LOGGER = logging.getLogger(__name__)
GTTS_LANG = {
    "es": "es",
    "fr": "fr",
    "de": "de",
    "hi": "hi",
    "it": "it",
    "pt": "pt",
    "ja": "ja",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "ar": "ar",
    "en": "en",
}


class SpeechSynthesizer:
    def __init__(self, config: dict):
        self.config = config

    def synthesize(self, text: str | list[dict], target_language: str, output_path: str) -> dict:
        if isinstance(text, list):
            text = " ".join((item.get("translated_text") or item.get("text") or "") for item in text).strip()

        if self.config.get("DEMO_PIPELINE", False) or not self.config.get("USE_REAL_PIPELINE", False):
            demo_audio_path = str(Path(output_path).with_suffix(".wav"))
            create_tone_wav(demo_audio_path, duration_seconds=3.0)
            return {
                "audio_path": demo_audio_path,
                "engine": "demo-fallback",
                "warning": "Demo audio marker generated because real TTS is not enabled.",
            }

        try:
            from gtts import gTTS  # type: ignore

            tts = gTTS(text=text or " ", lang=GTTS_LANG.get(target_language, "en"), slow=False)
            tts.save(output_path)
            return {"audio_path": output_path, "engine": "gtts"}
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            LOGGER.exception("Speech synthesis failed for target %s", target_language)
            demo_audio_path = str(Path(output_path).with_suffix(".wav"))
            create_tone_wav(demo_audio_path, duration_seconds=3.0)
            return {
                "audio_path": demo_audio_path,
                "engine": "demo-fallback",
                "warning": f"TTS fallback used: {exc}",
            }
