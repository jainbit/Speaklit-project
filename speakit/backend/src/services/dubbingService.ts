import { TextToSpeechClient } from '@google-cloud/text-to-speech';
import { Readable } from 'stream';
import { promises as fs } from 'fs';

const client = new TextToSpeechClient();

export const synthesizeDubbing = async (text: string, languageCode: string): Promise<Buffer> => {
    const request = {
        input: { text },
        voice: { languageCode, ssmlGender: 'NEUTRAL' },
        audioConfig: { audioEncoding: 'MP3' },
    };

    const [response] = await client.synthesizeSpeech(request);
    return Buffer.from(response.audioContent, 'binary');
};

export const saveDubbingToFile = async (audioBuffer: Buffer, outputPath: string): Promise<void> => {
    await fs.writeFile(outputPath, audioBuffer);
};