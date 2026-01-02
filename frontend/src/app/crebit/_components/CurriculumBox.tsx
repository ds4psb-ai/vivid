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
}

export function CurriculumBox({ section, title, items }: CurriculumBoxProps) {
    const [isOpen, setIsOpen] = React.useState(section === "01");

    return (
        <div className="bg-[#0A0A0A] border border-white/5 overflow-hidden group hover:border-[#4200FF]/50 transition-colors duration-300">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between h-24 px-8 text-left"
            >
                <div className="flex items-center gap-8">
                    <span className="text-[#4200FF] text-xs font-mono font-bold tracking-widest border border-[#4200FF]/30 px-3 py-1.5 rounded bg-[#4200FF]/5">SECTION {section}</span>
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
                        className="overflow-hidden bg-[#050505] border-t border-white/5"
                    >
                        <ul className="space-y-4 px-8 py-10">
                            {items.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-4 text-[15px] text-slate-300 font-light leading-relaxed">
                                    <div className="w-1 h-1 rounded-full bg-[#4200FF] mt-2.5 shrink-0" />
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
