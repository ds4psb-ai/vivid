"use client";

/**
 * Portfolio Item for masonry grid
 */

import Image from "next/image";
import { motion } from "framer-motion";
import { PlayCircle } from "lucide-react";

interface PortfolioItemProps {
    img: string;
    tag: string;
    title: string;
    desc: string;
    delay: number;
    color: string;
    height?: string;
    onClick?: () => void;
}

export function PortfolioItem({ img, tag, title, desc, delay, color, height = "h-[400px]", onClick }: PortfolioItemProps) {
    const colors = {
        purple: 'bg-[var(--color-brand-primary)]',
        pink: 'bg-rose-500',
        sky: 'bg-sky-500',
        emerald: 'bg-emerald-500',
        violet: 'bg-violet-500',
        amber: 'bg-amber-500',
        cyan: 'bg-cyan-500',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay, duration: 0.6 }}
            onClick={onClick}
            className={`card-premium group relative w-full ${height} overflow-hidden cursor-pointer transition-all duration-500`}
        >
            <Image
                src={img}
                alt={title}
                fill
                className="object-cover transition-transform duration-700 group-hover:scale-105 opacity-70 group-hover:opacity-100 grayscale group-hover:grayscale-0"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[var(--overlay-backdrop)] via-[var(--overlay-backdrop)] to-transparent opacity-60 group-hover:opacity-80 transition-opacity" />

            <div className="absolute inset-x-0 bottom-0 p-8 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-500 ease-out z-10">
                <div className="flex items-center gap-3 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 transform -translate-y-2 group-hover:translate-y-0 delay-75">
                    <span className={`w-1.5 h-1.5 rounded-full ${colors[color as keyof typeof colors]}`} />
                    <span className="text-[10px] font-bold text-[var(--fg-muted)] tracking-[0.2em] uppercase font-mono">
                        {tag}
                    </span>
                </div>
                <h3 className="text-3xl md:text-4xl font-black text-[var(--fg-on-emphasis)] mb-2 tracking-tighter uppercase italic leading-none">
                    {title}
                </h3>
                <div className="h-0 group-hover:h-auto overflow-hidden transition-all duration-500">
                    <p className="text-[var(--fg-subtle)] text-sm font-mono pt-2 border-t border-[var(--border-subtle)] mt-2">
                        {desc}
                    </p>
                </div>
            </div>

            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full border border-[var(--border-subtle)] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 scale-90 group-hover:scale-100 backdrop-blur-sm bg-[var(--surface-2)]">
                <PlayCircle className="w-8 h-8 text-[var(--fg-on-emphasis)] drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]" />
            </div>
        </motion.div>
    );
}
