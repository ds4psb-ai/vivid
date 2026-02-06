"use client";

interface NextStepButtonProps {
  onClick: () => void;
  label: string;
}

export function NextStepButton({ onClick, label }: NextStepButtonProps) {
  return (
    <div className="pt-2">
      <button
        type="button"
        onClick={onClick}
        className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-brand-primary)] px-4 text-sm font-semibold text-white transition-opacity hover:opacity-90"
      >
        <span>{label}</span>
        <span className="material-symbols-outlined text-[18px]" aria-hidden>
          arrow_forward
        </span>
      </button>
    </div>
  );
}
