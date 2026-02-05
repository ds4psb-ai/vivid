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

export type VariationOption = 'A' | 'B' | 'AB';

export interface VariationData {
  personaJson: File | null;
  personaContent: object | null;
  bestComment: string;
  variationOption: VariationOption | null;
}
