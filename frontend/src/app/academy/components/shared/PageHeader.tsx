"use client";

interface PageHeaderProps {
  title: string;
  sub: string;
}

export function PageHeader({ title, sub }: PageHeaderProps) {
  return (
    <div className="mb-8">
      <h2 className="text-3xl font-bold text-white mb-2">{title}</h2>
      <p className="text-gray-400">{sub}</p>
    </div>
  );
}
