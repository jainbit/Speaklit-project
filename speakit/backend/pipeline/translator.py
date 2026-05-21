from __future__ import annotations

import logging
import re
from typing import Any

from pipeline.common import SUPPORTED_LANGUAGES


LOGGER = logging.getLogger(__name__)
MARIAN_MODELS = {
    "es": "Helsinki-NLP/opus-mt-en-es",
    "fr": "Helsinki-NLP/opus-mt-en-fr",
    "de": "Helsinki-NLP/opus-mt-en-de",
    "hi": "Helsinki-NLP/opus-mt-en-hi",
    "it": "Helsinki-NLP/opus-mt-en-it",
    "pt": "Helsinki-NLP/opus-mt-en-pt",
    "ja": "Helsinki-NLP/opus-mt-en-jap",
    "zh": "Helsinki-NLP/opus-mt-en-zh",
    "ar": "Helsinki-NLP/opus-mt-en-ar",
}
DEMO_PREFIX = {
    "es": "Demo Spanish",
    "fr": "Demo French",
    "de": "Demo German",
    "hi": "Demo Hindi",
    "it": "Demo Italian",
    "pt": "Demo Portuguese",
    "ja": "Demo Japanese",
    "zh": "Demo Chinese",
    "ar": "Demo Arabic",
}
DEMO_TRANSLATIONS = {
    "fr": [
        "Bienvenue sur SpeakIt. Ceci est une transcription de demonstration generee pour votre video.",
        "Votre video peut etre transcrite, traduite et doublee dans plusieurs langues.",
    ],
    "es": [
        "Bienvenido a SpeakIt. Esta es una transcripcion de demostracion generada para tu video.",
        "Tu video puede transcribirse, traducirse y doblarse a varios idiomas.",
    ],
    "de": [
        "Willkommen bei SpeakIt. Dies ist eine Demo-Transkription, die fuer Ihr Video erstellt wurde.",
        "Ihr Video kann in mehrere Sprachen transkribiert, uebersetzt und synchronisiert werden.",
    ],
    "hi": [
        "SpeakIt mein aapka swagat hai. Yah aapke video ke liye banaya gaya demo transcript hai.",
        "Aapka video kai bhashaon mein transcribe, translate aur dub kiya ja sakta hai.",
    ],
    "ja": [
        "SpeakIt e youkoso. Kore wa anata no douga no tame ni sakusei sareta demo transcript desu.",
        "Anata no douga wa fukusuu no gengo ni mojiokoshi, honyaku, dubbing dekimasu.",
    ],
}
_TRANSLATION_CACHE: dict[str, dict[str, Any]] = {}


def _split_sentences(text: str) -> list[str]:
    normalized = (text or "").strip()
    if not normalized:
        return []
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()]
    return sentences or [normalized]


def _batched(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def get_translator(target_lang: str) -> dict[str, Any] | None:
    if target_lang not in MARIAN_MODELS:
        return None

    if target_lang not in _TRANSLATION_CACHE:
        from transformers import MarianMTModel, MarianTokenizer  # type: ignore

        model_name = MARIAN_MODELS[target_lang]
        _TRANSLATION_CACHE[target_lang] = {
            "tokenizer": MarianTokenizer.from_pretrained(model_name),
            "model": MarianMTModel.from_pretrained(model_name),
        }
    return _TRANSLATION_CACHE[target_lang]


class MarianTranslator:
    def __init__(self, config: dict):
        self.config = config

    def translate(self, text: str, target_lang: str) -> dict[str, Any]:
        if self.config.get("DEMO_PIPELINE", False) or not self.config.get("USE_REAL_PIPELINE", False):
            return self._demo_translation(text, target_lang, "Translation fallback used because demo pipeline mode is enabled.")

        translator = get_translator(target_lang)
        if translator is None:
            warning = f"Unsupported translation language '{target_lang}'. Returning original text."
            LOGGER.warning(warning)
            return {"engine": "identity", "warning": warning, "translated_text": text or ""}

        try:
            tokenizer = translator["tokenizer"]
            model = translator["model"]
            sentences = _split_sentences(text)
            if not sentences:
                return {"engine": MARIAN_MODELS[target_lang], "translated_text": ""}

            translated_sentences: list[str] = []
            for batch in _batched(sentences, 5):
                tokenized = tokenizer(
                    batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
                )
                generated = model.generate(**tokenized, max_length=512)
                translated_sentences.extend(
                    tokenizer.decode(item, skip_special_tokens=True) for item in generated
                )
            return {
                "engine": MARIAN_MODELS[target_lang],
                "translated_text": " ".join(item.strip() for item in translated_sentences if item.strip()),
            }
        except Exception as exc:  # pragma: no cover - runtime dependent
            LOGGER.exception("Translation failed for target %s", target_lang)
            return self._demo_translation(text, target_lang, f"Translation fallback used: {exc}")

    def translate_segments(self, segments: list[dict], target_language: str) -> dict[str, Any]:
        if not segments:
            return {"engine": "identity", "translated_text": "", "segments": []}

        translated_segments = []
        warnings: list[str] = []
        engine = "identity"
        demo_texts = DEMO_TRANSLATIONS.get(target_language, [])
        for index, segment in enumerate(segments):
            result = self.translate(segment.get("text", ""), target_language)
            if self.config.get("DEMO_PIPELINE", False) and index < len(demo_texts):
                result["translated_text"] = demo_texts[index]
            engine = result.get("engine", engine)
            if result.get("warning"):
                warnings.append(result["warning"])
            translated_segments.append({**segment, "translated_text": result.get("translated_text", "")})

        payload = {
            "engine": engine,
            "translated_text": " ".join(item["translated_text"] for item in translated_segments).strip(),
            "segments": translated_segments,
        }
        if warnings:
            payload["warning"] = warnings[-1]
        return payload

    def _demo_translation(self, text: str, target_lang: str, warning: str) -> dict[str, Any]:
        prefix = DEMO_PREFIX.get(target_lang, "Demo Translation")
        return {
            "engine": "demo-fallback",
            "warning": warning,
            "translated_text": f"{prefix}: {text}".strip(": ").strip(),
        }
