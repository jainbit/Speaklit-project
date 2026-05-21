from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_config(overrides: dict | None = None) -> dict:
    upload_dir = BASE_DIR / "uploads"
    output_dir = BASE_DIR / "outputs"
    temp_dir = BASE_DIR / "temp"
    data_dir = BASE_DIR / "data"

    for folder in (upload_dir, output_dir, temp_dir, data_dir):
        folder.mkdir(parents=True, exist_ok=True)

    config = {
        "APP_NAME": "SpeakIt",
        "DEBUG": _bool_env("SPEAKIT_DEBUG", True),
        "TESTING": False,
        "PORT": int(os.getenv("SPEAKIT_PORT", "5000")),
        "SECRET_KEY": os.getenv("SPEAKIT_SECRET_KEY", "speakit-dev-secret"),
        "JWT_SECRET": os.getenv("SPEAKIT_JWT_SECRET", "speakit-dev-jwt-secret"),
        "JWT_EXPIRY_SECONDS": int(os.getenv("SPEAKIT_JWT_EXPIRY_SECONDS", "86400")),
        "DB_DRIVER": os.getenv("SPEAKIT_DB_DRIVER", "sqlite").lower(),
        "MYSQL_HOST": os.getenv("MYSQL_HOST", "localhost"),
        "MYSQL_PORT": int(os.getenv("MYSQL_PORT", "3306")),
        "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE", "speakit"),
        "MYSQL_USER": os.getenv("MYSQL_USER", "root"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "SQLITE_PATH": os.getenv("SQLITE_PATH", str(data_dir / "speakit.db")),
        "UPLOAD_FOLDER": str(upload_dir),
        "OUTPUT_FOLDER": str(output_dir),
        "TEMP_FOLDER": str(temp_dir),
        "MAX_CONTENT_LENGTH": 1024 * 1024 * 1024,
        "ALLOWED_VIDEO_EXTENSIONS": {"mp4", "mov", "mkv", "webm", "avi", "m4v"},
        "CORS_ORIGIN": os.getenv("SPEAKIT_CORS_ORIGIN", "http://localhost:3000"),
        "AUTO_INIT_DB": _bool_env("SPEAKIT_AUTO_INIT_DB", True),
        "DEMO_PIPELINE": _bool_env("SPEAKIT_DEMO_PIPELINE", True),
        "USE_REAL_WHISPER": _bool_env("USE_REAL_WHISPER", False),
        "USE_REAL_PIPELINE": _bool_env("USE_REAL_PIPELINE", False),
        "WHISPER_MODEL_SIZE": os.getenv("SPEAKIT_WHISPER_MODEL", "base"),
    }

    if overrides:
        config.update(overrides)

    return config
