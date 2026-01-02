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
        <div className={`relative z-10 bg-[#0A0A0A] border rounded-lg p-5 flex flex-col items-start gap-4 transition-all duration-300 group hover:-translate-y-1 ${active ? 'border-[#4200FF] shadow-[0_0_20px_rgba(66,0,255,0.2)]' : 'border-white/10 hover:border-white/30'}`}>
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[#1a1a1c] border border-white/20" />
            <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-[#1a1a1c] border border-white/20 group-hover:bg-[#4200FF] transition-colors" />

            <div className="flex justify-between items-center w-full border-b border-white/5 pb-3">
                <span className="text-[10px] font-mono text-slate-500 bg-white/5 px-2 py-0.5 rounded">{type}</span>
                <span className="text-[10px] font-mono text-[#4200FF] font-bold">NODE_{step}</span>
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
