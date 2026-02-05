"use client";

interface NextStepButtonProps {
  onClick: () => void;
  label: string;
}

export function NextStepButton({ onClick, label }: NextStepButtonProps) {
  return (
    <div className="mt-8 pt-6 border-t border-white/10">
      <button
        onClick={onClick}
        className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold text-lg hover:from-purple-700 hover:to-indigo-700 transition-all flex items-center justify-center gap-3 shadow-[0_4px_20px_rgba(168,85,247,0.3)] group"
      >
        <span>다음 단계:</span>
        <span className="text-purple-200">{label}</span>
        <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
      </button>
    </div>
  );
}
