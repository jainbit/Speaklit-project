import { Translate } from '@google-cloud/translate/build/src/v2';
import { Translation } from '../types/index';

const translateClient = new Translate();

export const translateText = async (text: string, targetLanguage: string): Promise<Translation> => {
    try {
        const [translation] = await translateClient.translate(text, targetLanguage);
        return { translatedText: translation, targetLanguage };
    } catch (error) {
        throw new Error(`Translation failed: ${error.message}`);
    }
};

export const detectLanguage = async (text: string): Promise<string> => {
    try {
        const [detection] = await translateClient.detect(text);
        return detection.language;
    } catch (error) {
        throw new Error(`Language detection failed: ${error.message}`);
    }
};