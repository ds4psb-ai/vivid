"use client";

import React from "react";

/**
 * Stat Item for hero section
 */

interface StatItemProps {
    label: string;
    value: string;
    highlight?: boolean;
    badge?: string;
    urgent?: boolean;
    icon?: React.ReactNode;
}

export function StatItem({ label, value, highlight, badge, urgent, icon }: StatItemProps) {
    return (
        <div className="flex flex-col items-center">
            <div className="flex items-center gap-2 text-[var(--fg-muted)] text-xs font-bold tracking-widest uppercase mb-2">
                {icon}
                <span>{label}</span>
            </div>
            <div className="flex items-center gap-2">
                <span className={`text-xl md:text-2xl font-bold ${highlight ? "text-[var(--color-brand-primary)]" : "text-white"}`}>
                    {value}
                </span>
                {badge && (
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border ${urgent ? "border-[var(--color-brand-primary)]/30 bg-[var(--color-brand-primary)]/10 text-[var(--color-brand-primary)]" : "border-white/20 bg-white/5 text-slate-300"}`}>
                        {urgent && (
                            <span className="relative flex h-1.5 w-1.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--color-brand-primary)] opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[var(--color-brand-primary)]"></span>
                            </span>
                        )}
                        <span className="text-[11px] font-bold tracking-tight leading-none">{badge}</span>
                    </div>
                )}
            </div>
        </div>
    );
}
