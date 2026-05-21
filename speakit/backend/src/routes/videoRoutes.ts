import { Router } from 'express';
import { uploadVideo, getVideoStatus } from '../controllers/videoController';

const router = Router();

// Route for uploading a video
router.post('/upload', uploadVideo);

// Route for checking the status of a video processing
router.get('/status/:videoId', getVideoStatus);

export default router;