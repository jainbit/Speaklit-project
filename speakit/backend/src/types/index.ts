export interface Video {
    id: string;
    title: string;
    uploadDate: Date;
    status: 'pending' | 'transcribing' | 'transcribed' | 'translating' | 'translated' | 'dubbing' | 'dubbed';
    sourceLanguage: string;
    targetLanguages: string[];
}

export interface Transcription {
    videoId: string;
    text: string;
    progress: number; // percentage of transcription completed
}

export interface Translation {
    videoId: string;
    language: string;
    text: string;
}

export interface Dubbing {
    videoId: string;
    language: string;
    audioUrl: string;
}