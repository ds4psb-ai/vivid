"use client";

import { motion } from "framer-motion";
import {
    Clock,
    CheckCircle,
    FileText,
    DollarSign,
    User,
    Send,
    Shield,
    Upload,
    Play,
} from "lucide-react";

export interface EvidenceLog {
    id: string;
    event_type: string;
    title: string;
    description?: string;
    actor_role: string;
    attachments: string[];
    created_at: string;
}

const EVENT_CONFIG: Record<string, { icon: React.ElementType; tone: "info" | "accent" | "success" | "warning" | "neutral" }> = {
    // Status Updates
    status_update: { icon: Clock, tone: "info" },
    assignment_created: { icon: User, tone: "accent" },
    work_started: { icon: Play, tone: "info" },

    // File / Delivery
    file_upload: { icon: Upload, tone: "success" },
    delivery_submitted: { icon: Send, tone: "warning" },

    // Financial / Contract
    escrow_secured: { icon: Shield, tone: "success" },
    payment_released: { icon: DollarSign, tone: "success" },
    approval: { icon: CheckCircle, tone: "success" },

    // Default
    default: { icon: FileText, tone: "neutral" },
};

function EvidenceItem({ log, index, isLast }: { log: EvidenceLog; index: number; isLast: boolean }) {
    const config = EVENT_CONFIG[log.event_type] || EVENT_CONFIG.default;
    const Icon = config.icon;
    const toneText = `event-tone-${config.tone}`;
    const toneBg = `event-bg-${config.tone}`;
    const toneBorder = `event-border-${config.tone}`;

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="relative pl-8 pb-8 last:pb-0"
        >
            {/* Timeline Line */}
            {!isLast && (
                <div className="absolute left-[11px] top-8 bottom-0 w-[2px] bg-[var(--border-subtle)]" />
            )}

            {/* Icon Dot */}
            <div className={`absolute left-0 top-0 w-6 h-6 rounded-full flex items-center justify-center border-2 ${toneBorder} ${toneBg}`}>
                <Icon className={`w-3 h-3 ${toneText}`} />
            </div>

            {/* Content */}
            <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${toneText}`}>
                        {log.title}
                    </span>
                    <span className="text-xs text-[var(--fg-muted)]">
                        {new Date(log.created_at).toLocaleString([], {
                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                        })}
                    </span>
                </div>

                {log.description && (
                    <p className="text-sm text-[var(--fg-muted)]">
                        {log.description}
                    </p>
                )}

                {/* Attachments */}
                {log.attachments && log.attachments.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                        {log.attachments.map((file, i) => (
                            <a
                                key={i}
                                href={file}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 px-2 py-1 bg-[var(--surface-2)] rounded text-xs text-[var(--fg-muted)] hover:text-[var(--fg-0)] transition-colors"
                            >
                                <Upload className="w-3 h-3" />
                                File {i + 1}
                            </a>
                        ))}
                    </div>
                )}

                {/* Actor Badge */}
                <div className="mt-1">
                    <span className="evidence-badge" data-actor={log.actor_role}>
                        {log.actor_role.toUpperCase()}
                    </span>
                </div>
            </div>
        </motion.div>
    );
}

export default function EvidenceTimeline({ logs }: { logs: EvidenceLog[] }) {
    if (!logs || logs.length === 0) {
        return (
            <div className="text-center py-8 text-[var(--fg-muted)] text-sm">
                No evidence recorded yet.
            </div>
        );
    }

    return (
        <div className="py-4">
            {logs.map((log, index) => (
                <EvidenceItem
                    key={log.id}
                    log={log}
                    index={index}
                    isLast={index === logs.length - 1}
                />
            ))}
        </div>
    );
}
