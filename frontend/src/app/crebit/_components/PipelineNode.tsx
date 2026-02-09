"use client";

/**
 * Pipeline Node for System section
 */

interface PipelineNodeProps {
    step: string;
    type: string;
    label: string;
    desc: string;
    tags: string[];
    active?: boolean;
}

export function PipelineNode({ step, type, label, desc, tags, active }: PipelineNodeProps) {
    return (
        <div className={`relative z-10 card-premium rounded-xl p-6 flex flex-col items-start gap-4 transition-all duration-300 group hover:-translate-y-2 ${active ? "border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)]/5 shadow-xl" : "border-white/10 hover:border-white/30"}`}>
            {/* Top Dot for Horizontal Flow Connection */}
            <div className={`hidden md:block absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full border border-white/20 z-20 transition-colors ${active ? "bg-[var(--color-brand-primary)]" : "bg-[#1a1a1c] group-hover:bg-[var(--color-brand-primary)]"}`} />

            {/* Mobile Vertical Dot */}
            <div className="md:hidden absolute -left-1.5 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-[#1a1a1c] border border-white/20" />

            <div className="flex justify-between items-center w-full border-b border-white/5 pb-3">
                <span className="text-[10px] font-mono text-slate-500 bg-white/5 px-2 py-0.5 rounded">{type}</span>
                <span className="text-[10px] font-mono text-[var(--color-brand-primary)] font-bold">NODE_{step}</span>
            </div>

            <div>
                <h4 className={`text-lg font-bold mb-2 ${active ? 'text-white' : 'text-slate-300 group-hover:text-white'}`}>{label}</h4>
                <p className="text-xs text-slate-500 leading-relaxed font-mono">{desc}</p>
            </div>

            <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((tag, i) => (
                    <span key={i} className="text-[9px] text-slate-400 bg-white/5 px-1.5 py-0.5 border border-white/5 rounded-sm">{tag}</span>
                ))}
            </div>
        </div>
    );
}
