# SpeakIt Project

SpeakIt is a full-stack web application designed to automate the transcription, translation, and dubbing of videos into multiple languages. This project leverages modern technologies to provide a seamless user experience for video localization.

## Features

- **Video Uploading**: Users can upload videos via drag-and-drop functionality.
- **Transcription**: Automatic transcription of audio from uploaded videos.
- **Translation**: Users can select target languages for translation of the transcribed text.
- **Dubbing**: Dubbed audio can be generated and played alongside the original video for comparison.
- **Project Dashboard**: Users can view their projects and track the status of video processing in real-time.
- **Results Page**: Users can preview localized videos, download them, and view transcriptions and translations.

## Tech Stack

- **Frontend**: React, TypeScript
- **Backend**: Flask
- **Database**: SQLite for local development, with optional MySQL support
- **Pipeline**: Demo fallbacks by default, with optional Whisper, MarianMT, MoviePy, and gTTS integrations

## Setup Instructions

### Prerequisites

- Node.js and npm installed
- Python 3 and pip installed

### Run The Full App

From the repository root:

1. Install Python backend dependencies:
   ```
   python3 -m pip install -r speakit/backend/requirements.txt
   ```

2. Install frontend dependencies if `node_modules` is missing:
   ```
   cd speakit/frontend
   npm install
   cd ../..
   ```

3. Start both servers:
   ```
   npm start
   ```

The React app runs at `http://localhost:3000` and the Flask API runs at `http://localhost:5000`.

### Useful Commands

- `npm run start:backend` starts only the Flask backend.
- `npm run start:frontend` starts only the React frontend.
- `npm run test:backend` runs the Flask API tests.
- `npm run build:frontend` creates a production frontend build.

The default demo mode uses SQLite and placeholder media/transcript outputs, so heavyweight AI packages are not required just to run the product flow.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
