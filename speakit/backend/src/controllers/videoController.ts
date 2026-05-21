import { Request, Response } from 'express';
import { uploadVideo, processVideo } from '../services/videoService';

export const uploadVideoController = async (req: Request, res: Response) => {
    try {
        const videoFile = req.file;
        const sourceLanguage = req.body.sourceLanguage;
        const targetLanguages = req.body.targetLanguages;

        if (!videoFile) {
            return res.status(400).json({ message: 'No video file uploaded.' });
        }

        const result = await uploadVideo(videoFile, sourceLanguage, targetLanguages);
        return res.status(200).json(result);
    } catch (error) {
        return res.status(500).json({ message: 'Error uploading video.', error });
    }
};

export const processVideoController = async (req: Request, res: Response) => {
    try {
        const videoId = req.params.id;
        const result = await processVideo(videoId);
        return res.status(200).json(result);
    } catch (error) {
        return res.status(500).json({ message: 'Error processing video.', error });
    }
};