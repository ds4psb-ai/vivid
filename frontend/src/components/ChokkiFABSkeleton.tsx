"use client";

/**
 * Skeleton placeholder for Chokki FAB while the full AgentChatAccordion loads
 */
export function ChokkiFABSkeleton() {
    return (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[60]">
            {/* Skeleton FAB */}
            <div className="relative">
                {/* Glow Effect - Static */}
                <div className="absolute inset-0 rounded-full blur-xl bg-violet-500/30" />

                {/* Placeholder Circle */}
                <div className="relative h-16 w-16 rounded-full overflow-hidden border-2 border-violet-400/30 shadow-[0_10px_40px_rgba(0,0,0,0.5)] bg-black/50 animate-pulse">
                    {/* Inner shimmer */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
                </div>

                {/* Status Indicator - Static */}
                <span className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4">
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-zinc-600 border-2 border-black" />
                </span>
            </div>
        </div>
    );
}
