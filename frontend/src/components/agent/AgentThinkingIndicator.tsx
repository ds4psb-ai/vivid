"use client";

const DOT_DELAYS = [0, 150, 300];

export default function AgentThinkingIndicator({
  label = "Thinking",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={`flex items-center gap-2 text-xs text-slate-400 ${className ?? ""}`}
      aria-live="polite"
    >
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400/60" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-sky-300 shadow-[0_0_8px_rgba(56,189,248,0.7)]" />
      </span>
      <span className="uppercase tracking-[0.3em]">{label}</span>
      <div className="flex items-center gap-1">
        {DOT_DELAYS.map((delay, index) => (
          <span
            key={`dot-${index}`}
            className="h-1.5 w-1.5 rounded-full bg-slate-500/80 animate-bounce"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
