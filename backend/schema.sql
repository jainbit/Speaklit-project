CREATE DATABASE IF NOT EXISTS speakit;
USE speakit;

CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    registration_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Videos (
    video_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    video_title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    upload_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    source_language VARCHAR(16) NOT NULL DEFAULT 'en',
    target_languages JSON NULL,
    original_filename VARCHAR(255) NULL,
    output_manifest JSON NULL,
    current_stage VARCHAR(64) NOT NULL DEFAULT 'uploaded',
    progress INT NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    processing_log LONGTEXT NULL,
    storage_size FLOAT NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_videos_user FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS LocalizationHistory (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL,
    source_language VARCHAR(16) NOT NULL,
    target_language VARCHAR(16) NOT NULL,
    transcription_accuracy FLOAT NOT NULL DEFAULT 0,
    translation_accuracy FLOAT NOT NULL DEFAULT 0,
    dubbing_quality FLOAT NOT NULL DEFAULT 0,
    completion_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transcript_text LONGTEXT NULL,
    translated_text LONGTEXT NULL,
    output_path VARCHAR(500) NULL,
    segments_json LONGTEXT NULL,
    CONSTRAINT fk_history_video FOREIGN KEY (video_id) REFERENCES Videos(video_id)
);

CREATE TABLE IF NOT EXISTS Feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    comments TEXT NULL,
    rating INT NOT NULL,
    feedback_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id) REFERENCES Users(user_id),
    CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS Analytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,
    video_id INT NOT NULL UNIQUE,
    processing_time INT NOT NULL DEFAULT 0,
    word_count INT NOT NULL DEFAULT 0,
    accuracy_score FLOAT NOT NULL DEFAULT 0,
    storage_size FLOAT NOT NULL DEFAULT 0,
    last_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    language_breakdown_json LONGTEXT NULL,
    CONSTRAINT fk_analytics_video FOREIGN KEY (video_id) REFERENCES Videos(video_id)
);
