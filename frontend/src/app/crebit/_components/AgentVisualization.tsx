"use client";

import { motion } from "framer-motion";
import { Brain, Calculator, Sparkles, Zap, Network } from "lucide-react";
import React from "react";

/**
 * AgentVisualization - Full-screen background visualization
 * Shows the 4D Agent Workflow concept with a central node and 4 connected dimensions
 */
export function AgentVisualization() {
    return (
        <div className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none select-none z-0 opacity-40">
            {/* Grid Background */}
            <div className="absolute inset-0 bg-[url('/images/grid.svg')] opacity-5" />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80" />

            {/* Ambient Glow */}
            <div className="absolute top-[65%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[var(--layout-visual-xl)] h-[var(--layout-visual-xl)] bg-emerald-500/10 rounded-full blur-[120px]" />

            {/* Central Agent Node */}
            <div className="absolute top-[65%] left-1/2 -translate-x-1/2 -translate-y-1/2">
                <motion.div
                    animate={{
                        boxShadow: ["0 0 30px rgba(16, 185, 129, 0.2)", "0 0 60px rgba(16, 185, 129, 0.4)", "0 0 30px rgba(16, 185, 129, 0.2)"],
                    }}
                    transition={{ duration: 3, repeat: Infinity }}
                    className="w-28 h-28 rounded-full bg-black/80 backdrop-blur-lg border-2 border-emerald-500/50 flex items-center justify-center"
                >
                    <Network className="w-12 h-12 text-emerald-400" />
                </motion.div>
            </div>

            {/* 1D - Top */}
            <DimensionNode
                position="top"
                type="1D"
                icon={<Brain className="w-5 h-5" />}
                label="SUBCONSCIOUS"
                color="violet"
                delay={0}
            />

            {/* 2D - Right */}
            <DimensionNode
                position="right"
                type="2D"
                icon={<Calculator className="w-5 h-5" />}
                label="LOGIC"
                color="emerald"
                delay={0.2}
            />

            {/* 3D - Bottom */}
            <DimensionNode
                position="bottom"
                type="3D"
                icon={<Sparkles className="w-5 h-5" />}
                label="PROPENSITY"
                color="amber"
                delay={0.4}
            />

            {/* 4D - Left */}
            <DimensionNode
                position="left"
                type="4D"
                icon={<Zap className="w-5 h-5" />}
                label="FINE-TUNING"
                color="cyan"
                delay={0.6}
            />

            {/* Connection Lines */}
            <div className="absolute top-[65%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[var(--layout-visual-lg)] h-[var(--layout-visual-lg)]">
                <div className="absolute top-0 left-1/2 w-px h-[120px] bg-gradient-to-b from-violet-500/50 to-transparent" />
                <div className="absolute bottom-0 left-1/2 w-px h-[120px] bg-gradient-to-t from-amber-500/50 to-transparent" />
                <div className="absolute left-0 top-1/2 h-px w-[120px] bg-gradient-to-r from-cyan-500/50 to-transparent" />
                <div className="absolute right-0 top-1/2 h-px w-[120px] bg-gradient-to-l from-emerald-500/50 to-transparent" />
            </div>
        </div>
    );
}

interface DimensionNodeProps {
    position: "top" | "right" | "bottom" | "left";
    type: string;
    icon: React.ReactNode;
    label: string;
    color: "violet" | "emerald" | "amber" | "cyan";
    delay: number;
}

function DimensionNode({ position, type, icon, label, color, delay }: DimensionNodeProps) {
    const positionClasses = {
        top: "top-[55%] left-1/2 -translate-x-1/2",
        right: "top-[65%] right-[20%] -translate-y-1/2",
        bottom: "bottom-[10%] left-1/2 -translate-x-1/2",
        left: "top-[65%] left-[20%] -translate-y-1/2",
    };

    const colorClasses = {
        violet: "border-violet-500/40 text-violet-400 bg-violet-500/10",
        emerald: "border-emerald-500/40 text-emerald-400 bg-emerald-500/10",
        amber: "border-amber-500/40 text-amber-400 bg-amber-500/10",
        cyan: "border-cyan-500/40 text-cyan-400 bg-cyan-500/10",
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay, duration: 0.6, type: "spring" }}
            className={`absolute ${positionClasses[position]} flex flex-col items-center gap-2`}
        >
            <div className={`w-14 h-14 rounded-xl border-2 ${colorClasses[color]} backdrop-blur-md flex items-center justify-center`}>
                {icon}
            </div>
            <div className="flex flex-col items-center">
                <span className="text-[10px] font-mono text-white/60 font-bold">{type}</span>
                <span className="text-[9px] font-bold tracking-widest text-white/40 uppercase">{label}</span>
            </div>
        </motion.div>
    );
}
