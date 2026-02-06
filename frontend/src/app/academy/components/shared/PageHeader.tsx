"use client";

interface PageHeaderProps {
  title: string;
  sub?: string;
}

export function PageHeader({ title, sub }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <h2 className="text-3xl font-bold text-[var(--fg-0)] mb-2">{title}</h2>
      {sub ? <p className="text-[var(--fg-muted)]">{sub}</p> : null}
    </div>
  );
}
