"use client";

interface ContentCardProps {
  children: React.ReactNode;
  highlight?: boolean;
}

export function ContentCard({ children, highlight }: ContentCardProps) {
  return (
    <div
      className={`rounded-[var(--academy-radius)] border p-[var(--academy-card-padding)] ${
        highlight
          ? "border-[var(--color-brand-primary)]/35 bg-[var(--surface-2)]"
          : "border-[var(--border-muted)] bg-[var(--surface-1)]"
      }`}
    >
      {children}
    </div>
  );
}
