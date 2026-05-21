# SpeakIt Backend

This backend runs as a Flask REST API with a MySQL-first schema and a SQLite fallback for local development and tests.

## What It Includes

- JWT-style authentication for register/login flows
- Video upload, status polling, pipeline trigger, preview/download endpoints
- Localization history, analytics, and feedback APIs
- AVLA pipeline modules for extraction, transcription, translation, dubbing, and merge
- Safe demo fallbacks when Whisper, MoviePy, MarianMT, gTTS, or MySQL are not available yet

## Run Locally

```bash
cd speakit/backend
python3 -m pip install -r requirements.txt
python3 app.py
```

From the repository root, you can also run:

```bash
npm run start:backend
npm run test:backend
```

For lightweight development, keep:

- `SPEAKIT_DB_DRIVER=sqlite`
- `SPEAKIT_DEMO_PIPELINE=true`

That mode still exercises the full product flow, but uses placeholder transcript/translation/audio/video outputs whenever the heavyweight dependencies are missing.
