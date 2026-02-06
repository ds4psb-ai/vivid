"use client";

interface ContentCardProps {
  children: React.ReactNode;
  highlight?: boolean;
}

export function ContentCard({ children, highlight }: ContentCardProps) {
  return (
    <div
      className={`p-6 rounded-2xl border ${
        highlight
          ? "border-[var(--color-brand-primary)]/30 bg-[var(--surface-2)]"
          : "border-[var(--border-muted)] bg-[var(--surface-1)]"
      }`}
    >
      {children}
    </div>
  );
}
