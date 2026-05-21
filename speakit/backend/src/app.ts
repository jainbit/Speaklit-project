import express from 'express';
import bodyParser from 'body-parser';
import videoRoutes from './routes/videoRoutes';
import processingRoutes from './routes/processingRoutes';
import { authenticate } from './middleware/auth';

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(bodyParser.json());
app.use(authenticate);

// Routes
app.use('/api/videos', videoRoutes);
app.use('/api/processing', processingRoutes);

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});