"use client";

interface ContentCardProps {
  children: React.ReactNode;
  highlight?: boolean;
}

export function ContentCard({ children, highlight }: ContentCardProps) {
  return (
    <div className={`p-6 rounded-2xl border ${highlight ? 'border-purple-500/30 bg-purple-500/5' : 'border-white/10 bg-white/5'}`}>
      {children}
    </div>
  );
}
