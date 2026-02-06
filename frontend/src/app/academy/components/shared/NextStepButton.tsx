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
        className="w-full py-4 rounded-xl bg-[var(--color-brand-primary)] text-white font-bold text-lg transition-all flex items-center justify-center gap-2 hover:opacity-90"
      >
        <span>{label}</span>
        <span className="material-symbols-outlined">arrow_forward</span>
      </button>
    </div>
  );
}
