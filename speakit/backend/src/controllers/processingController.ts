import { Request, Response } from 'express';
import { startTranscription, checkTranscriptionStatus } from '../services/transcriptionService';
import { startTranslation, checkTranslationStatus } from '../services/translationService';
import { startDubbing, checkDubbingStatus } from '../services/dubbingService';

export const processVideo = async (req: Request, res: Response) => {
    const { videoId, targetLanguages } = req.body;

    try {
        // Start the transcription process
        const transcriptionResult = await startTranscription(videoId);
        if (!transcriptionResult.success) {
            return res.status(400).json({ message: 'Transcription failed', error: transcriptionResult.error });
        }

        // Start the translation process
        const translationResult = await startTranslation(videoId, targetLanguages);
        if (!translationResult.success) {
            return res.status(400).json({ message: 'Translation failed', error: translationResult.error });
        }

        // Start the dubbing process
        const dubbingResult = await startDubbing(videoId);
        if (!dubbingResult.success) {
            return res.status(400).json({ message: 'Dubbing failed', error: dubbingResult.error });
        }

        return res.status(200).json({ message: 'Video processing started successfully' });
    } catch (error) {
        return res.status(500).json({ message: 'An error occurred during video processing', error });
    }
};

export const getProcessingStatus = async (req: Request, res: Response) => {
    const { videoId } = req.params;

    try {
        const transcriptionStatus = await checkTranscriptionStatus(videoId);
        const translationStatus = await checkTranslationStatus(videoId);
        const dubbingStatus = await checkDubbingStatus(videoId);

        return res.status(200).json({
            transcriptionStatus,
            translationStatus,
            dubbingStatus,
        });
    } catch (error) {
        return res.status(500).json({ message: 'An error occurred while checking processing status', error });
    }
};