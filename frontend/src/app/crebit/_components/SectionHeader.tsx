"use client";

/**
 * Section Header
 * Common header for landing page sections
 */

import { motion } from "framer-motion";

interface SectionHeaderProps {
    title: string;
    subtitle: string;
    desc?: string;
    color?: string;
}

export function SectionHeader({ title, subtitle, desc, color = 'text-[#4200FF]' }: SectionHeaderProps) {
    return (
        <div className="text-center space-y-4">
            <motion.span
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className={`font-bold tracking-[0.2em] uppercase text-sm ${color}`}
            >
                {title}
            </motion.span>
            <motion.h2
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="text-4xl md:text-5xl font-bold text-white leading-tight"
            >
                {subtitle}
            </motion.h2>
            {desc && (
                <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className="text-[#9CA3AF] text-lg max-w-2xl mx-auto"
                >
                    {desc}
                </motion.p>
            )}
        </div>
    );
}
