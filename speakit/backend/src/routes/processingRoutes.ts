import { Router } from 'express';
import { processVideo, checkProcessingStatus } from '../controllers/processingController';

const router = Router();

// Route to process a video
router.post('/process', processVideo);

// Route to check the status of video processing
router.get('/status/:id', checkProcessingStatus);

export default router;