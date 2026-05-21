# SpeakIt

SpeakIt is a full-stack video localization app for uploading English source videos, translating them into target languages, and generating localized preview/download outputs. The app includes a React frontend, a Flask API, authentication, analytics, feedback, and a media-processing pipeline with demo fallbacks for local development.

## Features

- Upload videos by browsing or drag and drop
- Register/login flow with JWT-style authentication
- Select source and target languages for localization
- Track processing status, stages, progress, and logs
- Preview source videos, dubbed audio, translated text, and localized outputs
- View analytics for processed videos and language pairs
- Submit and view user feedback
- Run in lightweight demo mode with SQLite and placeholder media outputs

## Tech Stack

- Frontend: React 17, TypeScript, Create React App
- Backend: Python, Flask
- Database: SQLite by default, optional MySQL configuration
- Pipeline: extraction, transcription, translation, synthesis, and merge modules
- Optional AI/media dependencies: Whisper, Transformers/MarianMT, MoviePy, gTTS, ffmpeg, pydub

## Project Structure

```text
.
├── package.json              # Root workspace scripts
├── scripts/                  # Helpers for starting/testing the app
├── speakit/
│   ├── backend/              # Flask API, database models, routes, pipeline
│   └── frontend/             # React + TypeScript frontend
└── backend/                  # Secondary backend copy used for local reference/work
```

The root npm scripts currently run the app from `speakit/backend` and `speakit/frontend`.

## Prerequisites

- Node.js and npm
- Python 3.10+ and pip
- Optional: ffmpeg and heavier AI dependencies if you want real media processing instead of demo outputs

## Getting Started

Install backend dependencies:

```bash
python3 -m pip install -r speakit/backend/requirements.txt
```

Install frontend dependencies:

```bash
npm --prefix speakit/frontend install
```

Start the backend and frontend together:

```bash
npm start
```

Then open:

- Frontend: `http://localhost:3000`
- Backend health check: `http://localhost:5000/health`

By default, the app uses SQLite and demo pipeline mode, so you can exercise the full product flow without installing heavyweight ML/media packages.

## Useful Commands

```bash
npm start
```

Starts both the Flask backend and React frontend.

```bash
npm run start:backend
```

Starts only the Flask backend from `speakit/backend`.

```bash
npm run start:frontend
```

Starts only the React frontend from `speakit/frontend`.

```bash
npm run test:backend
```

Runs the backend unittest suite.

```bash
npm run build:frontend
```

Builds the production frontend bundle.

## Configuration

The backend reads configuration from environment variables. Common options:

| Variable | Default | Description |
| --- | --- | --- |
| `SPEAKIT_PORT` | `5000` | Flask API port |
| `SPEAKIT_DEBUG` | `true` | Enables Flask debug mode |
| `SPEAKIT_SECRET_KEY` | `speakit-dev-secret` | Flask secret key |
| `SPEAKIT_JWT_SECRET` | `speakit-dev-jwt-secret` | JWT signing secret |
| `SPEAKIT_DB_DRIVER` | `sqlite` | Database driver, usually `sqlite` or `mysql` |
| `SQLITE_PATH` | `speakit/backend/data/speakit.db` | SQLite database path |
| `SPEAKIT_CORS_ORIGIN` | `http://localhost:3000` | Allowed frontend origin |
| `SPEAKIT_DEMO_PIPELINE` | `true` | Enables placeholder/demo pipeline outputs |
| `USE_REAL_PIPELINE` | `false` | Enables real pipeline behavior where implemented |
| `USE_REAL_WHISPER` | `false` | Enables real Whisper transcription where available |
| `SPEAKIT_WHISPER_MODEL` | `base` | Whisper model size |

For MySQL, also configure:

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=speakit
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

## API Overview

Base API URL: `http://localhost:5000/api`

Main endpoints:

- `POST /api/auth/register` - create an account
- `POST /api/auth/login` - log in and receive a token
- `GET /api/auth/profile` - get the current user profile and feedback
- `GET /api/videos` - list uploaded videos
- `POST /api/videos/upload` - upload a source video
- `POST /api/videos/:id/process` - start localization processing
- `GET /api/videos/:id/status` - check processing status
- `GET /api/videos/:id` - get video details, histories, analytics, and preview URLs
- `GET /api/videos/:id/source` - stream the original uploaded video
- `GET /api/videos/:id/output?language=fr` - download a localized video
- `GET /api/videos/:id/audio?language=fr` - stream dubbed audio
- `GET /api/analytics/:user_id` - view dashboard analytics
- `POST /api/feedback` - submit feedback

Protected endpoints require an `Authorization: Bearer <token>` header.

## Supported Local Video Types

The backend accepts:

- `mp4`
- `mov`
- `mkv`
- `webm`
- `avi`
- `m4v`

The current MVP expects English source videos and supports target languages defined by the pipeline/frontend language list.

## Development Notes

- Uploaded videos are stored under `speakit/backend/uploads`.
- Generated outputs are stored under `speakit/backend/outputs`.
- Temporary audio/media files are stored under `speakit/backend/temp`.
- SQLite data is stored under `speakit/backend/data`.
- Demo mode creates placeholder transcript, audio, and video artifacts when real processing dependencies are unavailable.

## Testing

Run backend tests from the repository root:

```bash
npm run test:backend
```

You can also run them directly:

```bash
cd speakit/backend
python3 -m unittest discover tests
```

## Building

Create a production frontend build:

```bash
npm run build:frontend
```

The build output is written to `speakit/frontend/build`.
