'use client';

/**
 * A2UI Widget Catalog and Renderer
 * 
 * Declarative JSON → Native React Component mapping
 * Following Google A2UI specification for agent-driven UIs
 */

import React from 'react';
import Link from 'next/link';
import { LucideIcon, Sparkles, LayoutGrid, Image, Eye, Fingerprint } from 'lucide-react';
import type { A2UIMessage, A2UIPayload } from './types';

// ============================================
// Widget Component Registry
// ============================================

export type WidgetRenderer = (
    message: A2UIMessage,
    resolveChildren: (ids: string[]) => React.ReactNode[]
) => React.ReactNode;

const widgetRegistry: Map<string, WidgetRenderer> = new Map();

/**
 * Register a widget renderer for a specific type
 */
export function registerWidget(type: string, renderer: WidgetRenderer) {
    widgetRegistry.set(type, renderer);
}

/**
 * Get a widget renderer by type
 */
export function getWidget(type: string): WidgetRenderer | undefined {
    return widgetRegistry.get(type);
}

// ============================================
// Core Widgets
// ============================================

// Card Widget
registerWidget('Card', (message, resolveChildren) => {
    const { title, description, href } = message.props || {};
    const children = message.children ? resolveChildren(message.children) : null;

    const baseClasses = "relative overflow-hidden rounded-[2rem] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-8 backdrop-blur-2xl hover:bg-[var(--surface-2)] transition-all duration-700";

    const content = (
        <div className={baseClasses}>
            {typeof title === 'string' && <h2 className="text-2xl font-bold text-[var(--fg-0)] mb-4">{title}</h2>}
            {typeof description === 'string' && <p className="text-sm text-[var(--fg-muted)]">{description}</p>}
            {children}
        </div>
    );

    if (typeof href === 'string') {
        return <Link key={message.id} href={href}>{content}</Link>;
    }

    return <div key={message.id}>{content}</div>;
});

// Button Widget
registerWidget('Button', (message) => {
    const { label, variant = 'primary' } = message.props || {};
    const variantStr = typeof variant === 'string' ? variant : 'primary';

    const variants: Record<string, string> = {
        primary: "btn btn-primary btn-size-default",
        secondary: "btn btn-secondary btn-size-default",
        ghost: "btn btn-ghost btn-size-default"
    };

    return (
        <button
            key={message.id}
            className={`${variants[variantStr] || variants.primary} inline-flex items-center gap-2 px-6 py-3 rounded-full text-sm font-medium transition-all duration-300`}
        >
            {typeof label === 'string' ? label : ''}
        </button>
    );
});

// Progress Widget
registerWidget('Progress', (message) => {
    const { value = 0, max = 100, label } = message.props || {};
    const numValue = typeof value === 'number' ? value : 0;
    const numMax = typeof max === 'number' ? max : 100;
    const percentage = (numValue / numMax) * 100;

    return (
        <div key={message.id} className="w-full space-y-2">
            {typeof label === 'string' && (
                <div className="flex justify-between text-xs text-[var(--fg-muted)]">
                    <span>{label}</span>
                    <span>{Math.round(percentage)}%</span>
                </div>
            )}
            <div className="h-2 bg-[var(--border-subtle)] rounded-full overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
});

// DimensionCard Widget (Vivid-specific)
registerWidget('DimensionCard', (message) => {
    const {
        title,
        description,
        essence,
        href,
        iconName,
        borderColor,
        activeBg
    } = message.props || {};

    const iconMap: Record<string, LucideIcon> = {
        sparkles: Sparkles,
        layoutGrid: LayoutGrid,
        image: Image,
        eye: Eye,
        fingerprint: Fingerprint
    };

    const iconKey = typeof iconName === 'string' ? iconName : 'sparkles';
    const Icon = iconMap[iconKey] || Sparkles;
    const hrefStr = typeof href === 'string' ? href : '#';
    const borderColorStr = typeof borderColor === 'string' ? borderColor : 'border-violet-500';
    const activeBgStr = typeof activeBg === 'string' ? activeBg : 'bg-violet-500';

    return (
        <Link key={message.id} href={hrefStr}>
            <div className="group relative overflow-hidden rounded-[2rem] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-8 backdrop-blur-2xl hover:bg-[var(--surface-2)] transition-all duration-700 hover:-translate-y-2 min-h-[var(--layout-min-height-xl)]">
                {/* Border reveal */}
                <div className={`absolute inset-0 rounded-[2rem] border-2 ${borderColorStr} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

                <div className="relative flex flex-col h-full justify-between">
                    <div className="flex items-start justify-between">
                        <h2 className="text-2xl font-bold text-[var(--fg-0)]">{typeof title === 'string' ? title : ''}</h2>
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--surface-2)] border border-[var(--border-subtle)]">
                            <Icon className="h-5 w-5 text-[var(--fg-muted)]" />
                        </div>
                    </div>

                    <div className="space-y-4 mt-auto">
                        <p className="text-xs font-medium uppercase tracking-widest text-[var(--fg-subtle)]">
                            {typeof essence === 'string' ? essence : ''}
                        </p>
                        <p className="text-sm text-[var(--fg-muted)]">{typeof description === 'string' ? description : ''}</p>
                        <div className="inline-flex items-center gap-3 px-5 py-2 rounded-full border border-[var(--border-subtle)] bg-[var(--surface-2)] group-hover:bg-[var(--surface-1)] group-hover:text-[var(--fg-0)] transition-all duration-300">
                            <span className="text-[10px] font-bold tracking-widest uppercase">EXPLORE</span>
                            <div className={`h-1.5 w-1.5 rounded-full ${activeBgStr}`} />
                        </div>
                    </div>
                </div>
            </div>
        </Link>
    );
});

// ============================================
// A2UI Renderer Component
// ============================================

interface A2UIRendererProps {
    payload: A2UIPayload;
    className?: string;
}

export function A2UIRenderer({ payload, className = '' }: A2UIRendererProps) {
    const messageMap = new Map<string, A2UIMessage>();
    payload.messages.forEach(msg => messageMap.set(msg.id, msg));

    const resolveChildren = (ids: string[]): React.ReactNode[] => {
        return ids.map(id => {
            const childMsg = messageMap.get(id);
            if (!childMsg) return null;
            return renderMessage(childMsg);
        }).filter(Boolean);
    };

    const renderMessage = (message: A2UIMessage): React.ReactNode => {
        const renderer = getWidget(message.type);
        if (!renderer) {
            console.warn(`Unknown A2UI widget type: ${message.type}`);
            return null;
        }
        return renderer(message, resolveChildren);
    };

    // Find root messages (not referenced as children)
    const childIds = new Set<string>();
    payload.messages.forEach(msg => {
        msg.children?.forEach(id => childIds.add(id));
    });

    const rootMessages = payload.messages.filter(msg => !childIds.has(msg.id));

    return (
        <div className={className}>
            {rootMessages.map(renderMessage)}
        </div>
    );
}
