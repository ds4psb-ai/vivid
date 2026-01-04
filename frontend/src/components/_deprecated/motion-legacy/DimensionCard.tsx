'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { LucideIcon } from 'lucide-react';
import { SPRING, STAGGER, TIMING } from '@/lib/animation';

export interface DimensionItemData {
    href: string;
    icon: LucideIcon;
    dimensionLabel: string;
    sensoryName: string;
    titleKo: string;
    titleEn: string;
    descKo: string;
    descEn: string;
    essenceKo: string;
    essenceEn: string;
    portalColor: string;
    borderColor: string;
    glowClass: string;
    activeBg: string;
    activeText: string;
}

interface DimensionCardProps {
    dimension: DimensionItemData;
    index: number;
    language: 'ko' | 'en';
}

/**
 * DimensionCard with Motion layoutId for smooth Morph transitions.
 * Each card has a unique layoutId based on its dimensionLabel.
 */
export function DimensionCard({ dimension, index, language }: DimensionCardProps) {
    const Icon = dimension.icon;

    return (
        <motion.div
            layoutId={`dimension-card-${dimension.dimensionLabel}`}
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9, transition: { duration: TIMING.fast } }}
            transition={{
                ...SPRING.default,
                delay: index * STAGGER.normal,
            }}
            whileHover={{ y: -8, transition: { duration: TIMING.fast } }}
            className="group relative"
        >
            <Link
                href={dimension.href}
                className="block relative overflow-hidden rounded-[2rem] border border-white/5 bg-black/40 p-8 backdrop-blur-2xl hover:bg-white/[0.03] transition-colors duration-700"
            >
                {/* Colored Border Reveal on Hover */}
                <div
                    className={`absolute inset-0 rounded-[2rem] border-2 ${dimension.borderColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                />

                {/* Portal Ring Effect */}
                <div
                    className={`absolute -right-20 -top-20 h-64 w-64 rounded-full border-[1px] ${dimension.portalColor} ${dimension.glowClass} blur-[60px] opacity-20 group-hover:opacity-40 transition-opacity duration-700`}
                />

                <div className="relative flex items-start justify-between h-full flex-col gap-16 min-h-[320px]">
                    <div className="w-full flex items-start justify-between z-10">
                        <div className="flex flex-col gap-1">
                            <motion.h2
                                className="text-2xl font-bold text-white group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-white group-hover:to-white/70 transition-all duration-500"
                                layoutId={`dimension-title-${dimension.dimensionLabel}`}
                            >
                                {language === 'ko' ? dimension.titleKo : dimension.titleEn}
                            </motion.h2>
                        </div>

                        <motion.div
                            className={`flex h-12 w-12 items-center justify-center rounded-full bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-500 group-hover:scale-110 group-hover:bg-white/10 group-hover:border-white/20 group-hover:rotate-12`}
                            layoutId={`dimension-icon-${dimension.dimensionLabel}`}
                        >
                            <Icon
                                className={`h-5 w-5 text-white/80 ${dimension.sensoryName === 'SOUL' ? 'text-lime-400' : ''}`}
                                aria-hidden="true"
                            />
                        </motion.div>
                    </div>

                    <div className="space-y-6 z-10 mt-auto">
                        <div className="space-y-2">
                            <p className={`text-xs font-medium uppercase tracking-widest ${dimension.sensoryName === 'SOUL' ? 'text-lime-400' : 'text-zinc-500 group-hover:text-zinc-400'} transition-colors`}>
                                {language === 'ko' ? dimension.essenceKo : dimension.essenceEn}
                            </p>
                            <p className="text-sm text-[var(--fg-muted)] leading-relaxed line-clamp-2 mix-blend-plus-lighter">
                                {language === 'ko' ? dimension.descKo : dimension.descEn}
                            </p>
                        </div>

                        {/* Action Button */}
                        <div>
                            <div className="inline-flex items-center gap-3 px-5 py-2 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm group-hover:bg-white group-hover:text-black transition-all duration-300">
                                <span className="text-[10px] font-bold tracking-[0.15em] uppercase">
                                    {language === 'ko' ? '차원 진입' : 'EXPLORE'}
                                </span>
                                <div className={`h-1.5 w-1.5 rounded-full ${dimension.activeBg} opacity-80`} />
                            </div>
                        </div>
                    </div>
                </div>
            </Link>
        </motion.div>
    );
}

/**
 * Container component with stagger animation for child cards.
 */
export function DimensionCardGrid({ children }: { children: React.ReactNode }) {
    return (
        <motion.div
            initial="hidden"
            animate="visible"
            variants={{
                visible: {
                    transition: { staggerChildren: STAGGER.normal },
                },
            }}
        >
            {children}
        </motion.div>
    );
}
