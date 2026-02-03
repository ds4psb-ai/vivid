export type OutputMode = 'MINIMAL' | 'EXPERT' | 'BOTH';
export type ParodyMode = 'KOREAN' | 'JAPANESE' | 'CUSTOM';

export type AppStatus = 'IDLE' | 'UPLOADING' | 'THINKING' | 'WAITING_USER' | 'COMPLETE' | 'ERROR';

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
  step?: number;
}

export interface AnalysisResult {
  markdown: string;
}

export interface ProcessingState {
  currentStage: number;
  message: string;
}

export interface PersonaConfig {
  ethnicity: string;
  era: string;
  style: string;
  characters: {
    main_child?: { age: number; hair: string; features: string };
    mother?: { clothing: string };
    father?: { clothing: string };
  };
}

export interface UploadedFiles {
  video: File | null;
  rawMd: File | null;
  persona: File | null;
  comments: File | null;
}
