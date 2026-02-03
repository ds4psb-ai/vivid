export type OutputMode = 'MINIMAL' | 'EXPERT' | 'BOTH' | 'NANOBANANA' | 'MIDJOURNEY_V8';

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
