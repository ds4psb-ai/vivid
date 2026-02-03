import React from 'react';
import { Loader2, BrainCircuit } from 'lucide-react';

interface ProcessingOverlayProps {
  status: string;
}

export const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({ status }) => {
  return (
    <div className="w-full bg-gray-900 rounded-xl border border-gray-800 p-8 flex flex-col items-center justify-center min-h-[400px] relative overflow-hidden animate-in fade-in">
      {/* Background effect */}
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[length:20px_20px]" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-900/50 to-gray-900 pointer-events-none" />

      <div className="relative z-10 flex flex-col items-center">
        <div className="mb-6 p-4 rounded-full bg-gray-800/50 border border-gray-700 shadow-2xl relative">
          <BrainCircuit className="w-12 h-12 text-accent-purple animate-pulse" />
          <div className="absolute inset-0 rounded-full border-2 border-accent-purple/30 animate-ping" />
        </div>

        <h3 className="text-2xl font-bold text-white mb-2">
          AI가 분석 중입니다...
        </h3>
        <p className="text-gray-400 font-mono text-sm animate-pulse">
          Gemini 3 Pro Preview가 영상을 시청하고 있습니다. 잠시만 기다려주세요.
        </p>
        
        <div className="mt-8 flex gap-2">
           <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce delay-0"></div>
           <div className="w-2 h-2 bg-accent-purple rounded-full animate-bounce delay-100"></div>
           <div className="w-2 h-2 bg-accent-cyan rounded-full animate-bounce delay-200"></div>
        </div>
      </div>
    </div>
  );
};