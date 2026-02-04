import React from 'react';
import { Film, Zap } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-tr from-accent-blue to-accent-purple p-2 rounded-lg">
            <Film className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            Builder 1 <span className="text-accent-cyan font-mono text-sm">V7.2</span>
          </h1>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
          <span className="flex items-center gap-1">
            <Zap className="w-3 h-3 text-yellow-500" />
            POWERED BY GEMINI 3 PRO
          </span>
          <span className="hidden sm:inline-block px-2 py-1 bg-gray-800 rounded text-gray-300">
            5-STEP (프레임 검증 포함)
          </span>
        </div>
      </div>
    </header>
  );
};