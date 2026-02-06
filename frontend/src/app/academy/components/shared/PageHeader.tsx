"use client";

interface PageHeaderProps {
  title: string;
  sub?: string;
}

export function PageHeader({ title, sub }: PageHeaderProps) {
  return (
    <div className="mb-4">
      <h2 className="font-korean text-2xl font-semibold tracking-tight text-[var(--fg-0)] md:text-[28px]">
        {title}
      </h2>
      {sub ? <p className="mt-1 text-sm text-[var(--fg-muted)]">{sub}</p> : null}
    </div>
  );
}
