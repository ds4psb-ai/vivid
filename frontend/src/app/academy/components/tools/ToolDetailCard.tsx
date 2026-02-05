"use client";

interface ToolDetailCardProps {
  title: string;
  color: string;
  url: string;
  badge?: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const colorClasses: Record<string, { bg: string; border: string; text: string; hoverBorder: string }> = {
  orange: { bg: "bg-orange-500/10", border: "border-orange-500/20", text: "text-orange-400", hoverBorder: "hover:border-orange-500/50" },
  violet: { bg: "bg-violet-500/10", border: "border-violet-500/20", text: "text-violet-400", hoverBorder: "hover:border-violet-500/50" },
  cyan: { bg: "bg-cyan-500/10", border: "border-cyan-500/20", text: "text-cyan-400", hoverBorder: "hover:border-cyan-500/50" },
  red: { bg: "bg-red-500/10", border: "border-red-500/20", text: "text-red-400", hoverBorder: "hover:border-red-500/50" },
};

export function ToolDetailCard({
  title,
  color,
  url,
  badge,
  isOpen,
  onToggle,
  children,
}: ToolDetailCardProps) {
  const c = colorClasses[color] || colorClasses.violet;

  return (
    <div className={`rounded-xl border ${c.border} ${c.bg} mb-3 overflow-hidden transition-all ${c.hoverBorder}`}>
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <span className={`font-bold ${c.text}`}>{title}</span>
          {badge && (
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${c.bg} ${c.text} border ${c.border}`}>
              {badge}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold bg-white text-gray-900 hover:bg-gray-100 transition-colors flex items-center gap-1`}
          >
            열기
            <span className="material-symbols-outlined text-xs text-gray-500">open_in_new</span>
          </a>
          <span className={`material-symbols-outlined ${c.text} text-lg transition-transform ${isOpen ? 'rotate-180' : ''}`}>
            expand_more
          </span>
        </div>
      </button>
      {isOpen && (
        <div className="px-4 pb-4 pt-0 border-t border-white/5">
          {children}
        </div>
      )}
    </div>
  );
}
