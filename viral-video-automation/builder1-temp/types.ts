export type OutputMode = 'MINIMAL' | 'EXPERT' | 'BOTH';

export type AppStatus = 'IDLE' | 'THINKING' | 'WAITING_USER' | 'COMPLETE' | 'ERROR';

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
