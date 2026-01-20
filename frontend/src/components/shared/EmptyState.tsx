/**
 * Empty State Component
 * 
 * Display when a list or section has no content.
 */

import { LucideIcon, Inbox } from "lucide-react";
import { ReactNode } from "react";

interface EmptyStateProps {
    icon?: LucideIcon;
    title: string;
    description?: string;
    action?: ReactNode;
}

export function EmptyState({
    icon: Icon = Inbox,
    title,
    description,
    action,
}: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="p-4 bg-[var(--surface-2)]/60 rounded-full mb-4 border border-white/5">
                <Icon className="w-12 h-12 text-[var(--fg-subtle)]" />
            </div>
            <h3 className="text-lg font-medium text-[var(--fg-0)] mb-1">{title}</h3>
            {description && (
                <p className="text-[var(--fg-subtle)] max-w-sm">{description}</p>
            )}
            {action && <div className="mt-4">{action}</div>}
        </div>
    );
}

export default EmptyState;
