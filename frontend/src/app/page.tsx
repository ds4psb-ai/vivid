"use client";

/**
 * Home Page - Unified Home
 * 
 * Combines TemplateRail, DimensionGrid, and WorkflowCTA
 * into a single cohesive landing page.
 */

import { Suspense, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Globe } from "lucide-react";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TemplateRail, DimensionGrid, WorkflowCTA } from "@/components/home";
import { useLanguage } from "@/contexts/LanguageContext";
import { useSessionContext } from "@/contexts/SessionContext";

function HomePageContent() {
  const router = useRouter();
  const { language, setLanguage } = useLanguage();
  const { isAuthenticated, isLoading: isSessionLoading } = useSessionContext();

  // Authenticated users go to studio
  useEffect(() => {
    if (isSessionLoading) return;
    if (isAuthenticated) {
      router.replace("/studio");
    }
  }, [isAuthenticated, isSessionLoading, router]);

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background */}
      <AuroraBackground />

      <div className="relative z-10 min-h-screen">
        {/* Hero Section - Minimal */}
        <section className="pt-8 pb-4 px-6" />

        {/* Main Content */}
        <div className="px-6 pb-20 space-y-12">
          <div className="mx-auto max-w-7xl space-y-12">
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

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-violet-400 border-t-transparent" />
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
