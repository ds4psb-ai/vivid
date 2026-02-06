"use client";

interface NextStepButtonProps {
  onClick: () => void;
  label: string;
}

export function NextStepButton({ onClick, label }: NextStepButtonProps) {
  return (
    <div className="mt-8 pt-6 border-t border-[var(--border-muted)]">
      <button
        onClick={onClick}
        className="w-full py-4 rounded-xl text-white font-bold text-lg transition-all flex items-center justify-center gap-3 shadow-[0_4px_20px_rgba(239,0,60,0.25)] group hover:opacity-95"
        style={{
          background:
            "linear-gradient(90deg, var(--color-brand-primary), var(--accent-2))",
        }}
      >
        <span>다음 단계:</span>
        <span className="text-white/85">{label}</span>
        <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
      </button>
    </div>
  );
}
