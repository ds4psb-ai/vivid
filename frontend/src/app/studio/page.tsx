"use client";

/**
 * Studio Page - Unified Home for Authenticated Users
 * 
 * Combines:
 * - TemplateRail: Horizontal scroll of recommended templates
 * - DimensionGrid: Grid of all dimension tools with stage filters
 * - WorkflowCTA: Call-to-action for custom workflow creation
 */

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TemplateRail, DimensionGrid, WorkflowCTA } from "@/components/home";
import { useLanguage } from "@/contexts/LanguageContext";

export default function StudioPage() {
    const { language } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            {/* Aurora Background */}
            <AuroraBackground />

            <div className="relative z-10 min-h-screen">
                {/* Hero Section - Minimal */}
                <section className="pt-8 pb-4 px-6" />

                {/* Main Content */}
                <div className="px-6 pb-20 space-y-10">
                    <div className="mx-auto max-w-7xl space-y-10">
                        {/* Template Rail */}
                        <motion.section
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <TemplateRail maxItems={6} />
                        </motion.section>

                        {/* Dimension Grid */}
                        <motion.section
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            <DimensionGrid showTitle={true} showFilters={true} />
                        </motion.section>

                        {/* Workflow CTA */}
                        <motion.section
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                        >
                            <WorkflowCTA />
                        </motion.section>
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
