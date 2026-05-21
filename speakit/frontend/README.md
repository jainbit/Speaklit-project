# SpeakIt Frontend Documentation

## Overview
SpeakIt is a web application designed to automate the transcription, translation, and dubbing of videos into multiple languages. The frontend is built using React and TypeScript, providing a user-friendly interface for managing video localization tasks.

## Features
- **Video Uploading**: Users can easily upload video files through a drag-and-drop interface.
- **Transcription Display**: View real-time transcription progress of the uploaded videos.
- **Translation Selector**: Choose from multiple target languages for translation.
- **Dubbing Player**: Play dubbed audio alongside the original video for comparison.
- **Dashboard**: Monitor the status of user projects and receive real-time updates.
- **Results Page**: Preview localized videos, download them, and view transcriptions and translations.

## Getting Started

### Prerequisites
- Node.js (version 14 or higher)
- npm (Node Package Manager)

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the frontend directory:
   ```
   cd speakit/frontend
   ```
3. Install dependencies:
   ```
   npm install
   ```

### Running the Application
To start the frontend development server, run:
```
npm start
```
The application will be available at `http://localhost:3000`.

From the repository root, `npm start` starts both the Flask backend and this frontend together.

## Folder Structure
- **App.tsx**: Main application component and API integration.
- **index.tsx**: Entry point of the React application.
- **styles.css**: Application styles.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
