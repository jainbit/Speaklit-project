from __future__ import annotations

from pipeline.common import SUPPORTED_LANGUAGES


DEMO_PREFIX = {
    "es": "Traduccion demo",
    "fr": "Traduction demo",
    "de": "Demo Ubersetzung",
    "hi": "डेमो अनुवाद",
    "ja": "デモ翻訳",
}


class MarianTranslator:
    def __init__(self, config: dict):
        self.config = config
        self._cache = {}

    def translate_segments(self, segments: list[dict], target_language: str) -> dict:
        model_name = SUPPORTED_LANGUAGES[target_language]["model"]
        if not model_name:
            translated = [{**segment, "translated_text": segment["text"]} for segment in segments]
            return {
                "engine": "identity",
                "translated_text": " ".join(item["translated_text"] for item in translated),
                "segments": translated,
            }

        try:
            from transformers import MarianMTModel, MarianTokenizer  # type: ignore

            if model_name not in self._cache:
                tokenizer = MarianTokenizer.from_pretrained(model_name)
                model = MarianMTModel.from_pretrained(model_name)
                self._cache[model_name] = (tokenizer, model)
            tokenizer, model = self._cache[model_name]

            translated_segments = []
            for segment in segments:
                batch = tokenizer([segment["text"]], return_tensors="pt", padding=True)
                generated = model.generate(**batch)
                translated_text = tokenizer.decode(generated[0], skip_special_tokens=True)
                translated_segments.append({**segment, "translated_text": translated_text})
            return {
                "engine": model_name,
                "translated_text": " ".join(item["translated_text"] for item in translated_segments),
                "segments": translated_segments,
            }
        except Exception as exc:
            if not self.config["DEMO_PIPELINE"]:
                raise
            prefix = DEMO_PREFIX.get(target_language, "Demo Translation")
            translated_segments = [
                {**segment, "translated_text": f"{prefix}: {segment['text']}"}
                for segment in segments
            ]
            return {
                "engine": "demo-fallback",
                "warning": f"Translation fallback used: {exc}",
                "translated_text": " ".join(item["translated_text"] for item in translated_segments),
                "segments": translated_segments,
            }
