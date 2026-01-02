"use client";

/**
 * Track Selection Card
 */

import { Calendar, Users, Film } from "lucide-react";

interface TrackCardProps {
    type: string;
    title: string;
    badge: string;
    schedule: string;
    desc: string;
    color: string;
}

export function TrackCard({ type, title, badge, schedule, desc, color }: TrackCardProps) {
    return (
        <div className="group relative p-10 bg-[#0A0A0A] border border-white/5 hover:border-white/20 transition-all duration-300 hover:-translate-y-2 overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <Film className="w-32 h-32 text-white" />
            </div>

            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded border border-white/10 bg-white/5 text-[11px] font-bold text-slate-300 mb-8 tracking-widest uppercase font-mono">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                {badge}
            </div>

            <div className="text-[12rem] font-black absolute -top-10 -right-4 font-mono select-none pointer-events-none text-[#ffffff] opacity-[0.02]">
                {type}
            </div>

            <div className="relative z-10">
                <h3 className="text-3xl font-black text-white mb-3 tracking-tight">{title}</h3>
                <p className="text-slate-400 mb-8 font-light leading-relaxed">{desc}</p>

                <div className="space-y-4 border-t border-white/5 pt-8">
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-slate-400 border border-white/5">
                            <Calendar className="w-4 h-4" />
                        </div>
                        <span className="text-slate-300 font-mono text-sm">{schedule}</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-slate-400 border border-white/5">
                            <Users className="w-4 h-4" />
                        </div>
                        <span className="text-slate-300 text-sm font-mono tracking-tight">정원 20명 소수정예</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
