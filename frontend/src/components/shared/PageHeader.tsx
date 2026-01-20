/**
 * Page Header Component
 * 
 * Standard page header with back button, title, and optional actions.
 */

"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, LucideIcon } from "lucide-react";

interface PageHeaderProps {
    title: string;
    subtitle?: string;
    icon?: LucideIcon;
    backHref?: string;
    backLabel?: string;
    actions?: ReactNode;
}

export function PageHeader({
    title,
    subtitle,
    icon: Icon,
    backHref,
    backLabel = "Back",
    actions,
}: PageHeaderProps) {
    const router = useRouter();

    const handleBack = () => {
        if (backHref) {
            router.push(backHref);
        } else {
            router.back();
        }
    };

    return (
        <div className="border-b border-white/5 bg-[var(--surface-1)]/80 backdrop-blur-sm sticky top-0 z-10">
            <div className="max-w-7xl mx-auto px-6 py-4">
                {backLabel && (
                    <button
                        onClick={handleBack}
                        className="flex items-center gap-2 text-[var(--fg-subtle)] hover:text-[var(--fg-0)] mb-3 text-sm transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        {backLabel}
                    </button>
                )}

                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl md:text-2xl font-bold text-[var(--fg-0)] flex items-center gap-2">
                            {Icon && <Icon className="w-5 h-5 md:w-6 md:h-6 text-violet-400" />}
                            {title}
                        </h1>
                        {subtitle && (
                            <p className="text-[var(--fg-muted)] text-sm mt-1">{subtitle}</p>
                        )}
                    </div>

                    {actions && <div className="flex items-center gap-3">{actions}</div>}
                </div>
            </div>
        </div>
    );
}

export default PageHeader;
