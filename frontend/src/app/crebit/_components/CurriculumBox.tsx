"use client";

/**
 * Curriculum Accordion Box
 */

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown } from "lucide-react";

interface CurriculumBoxProps {
    section: string;
    title: string;
    items: string[];
    active?: boolean; // Added active prop to support the new div's conditional styling
}

export function CurriculumBox({ section, title, items, active }: CurriculumBoxProps) {
    const [isOpen, setIsOpen] = React.useState(section === "01");

    return (
        <div className={`relative z-10 card-premium rounded-xl p-6 flex flex-col items-start gap-4 transition-all duration-300 group hover:-translate-y-2 ${active ? 'border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.2)] bg-emerald-500/5' : 'border-white/10 hover:border-white/30'}`}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between h-24 text-left" // Removed px-8 from button as parent div now has p-6
            >
                <div className="flex items-center gap-8">
                    <span className="text-emerald-500 text-xs font-mono font-bold tracking-widest border border-emerald-500/30 px-3 py-1.5 rounded bg-emerald-500/5">SECTION {section}</span>
                    <h3 className={`text-xl md:text-2xl font-bold transition-colors ${isOpen ? 'text-white' : 'text-slate-400 group-hover:text-white'}`}>{title}</h3>
                </div>
                <div className={`text-slate-500 transition-transform duration-300 ${isOpen ? 'rotate-180 text-white' : ''}`}>
                    <ChevronDown className="w-6 h-6" />
                </div>
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden bg-transparent border-t border-white/5"
                    >
                        <ul className="space-y-4 px-8 py-10">
                            {items.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-4 text-[15px] text-slate-300 font-light leading-relaxed py-3 border-b border-white/5 last:border-0 group/item hover:text-white transition-colors">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2.5 shrink-0 group-hover/item:shadow-[0_0_8px_#10B981] transition-all" />
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
