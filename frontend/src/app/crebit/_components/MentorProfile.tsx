"use client";

/**
 * Mentor Profile Card
 */

import Image from "next/image";

interface MentorProfileProps {
    img: string;
    name: string;
    role: string;
    tags: string[];
}

export function MentorProfile({ img, name, role, tags }: MentorProfileProps) {
    return (
        <div className="bg-[#151515] p-6 border border-white/5 hover:border-white/20 transition-all hover:bg-[#1a1a1c] flex items-center gap-6 group">
            <div className="w-20 h-20 bg-slate-800 shrink-0 overflow-hidden relative grayscale group-hover:grayscale-0 transition-all duration-500">
                <Image src={img} alt={name} fill className="object-cover" />
            </div>
            <div>
                <h4 className="text-lg font-bold text-white mb-1 group-hover:text-[#4200FF] transition-colors">{name}</h4>
                <p className="text-sm text-slate-500 mb-3">{role}</p>
                <div className="flex flex-wrap gap-2">
                    {tags.map((tag, i) => (
                        <span key={i} className="text-[10px] text-slate-400 bg-white/5 px-2 py-0.5 border border-white/5">{tag}</span>
                    ))}
                </div>
            </div>
        </div>
    );
}
