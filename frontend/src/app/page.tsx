"use client";

/**
 * Home Page - Unified Home
 * 
 * Combines TemplateRail, DimensionGrid, and WorkflowCTA
 * into a single cohesive landing page.
 */

import React, { Suspense, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TemplateRail, DimensionGrid, WorkflowCTA } from "@/components/home";
import HomeRailSection from "@/components/home/HomeRailSection";
import { useSessionContext } from "@/contexts/SessionContext";
import { useLanguage } from "@/contexts/LanguageContext";

interface RailItem {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  thumbnail_url: string | null;
  license_status: string;
  preset_count: number;
}

interface RailSection {
  section_id: string;
  title_ko: string;
  title_en: string;
  items: RailItem[];
  has_more: boolean;
}

function HomePageContent() {
  const router = useRouter();
  const { language } = useLanguage();
  const { isAuthenticated, isLoading: isSessionLoading } = useSessionContext();
  const [ipRails, setIpRails] = useState<RailSection[]>([]);

  // Fetch IP rails
  useEffect(() => {
    async function fetchIPRails() {
      try {
        const response = await fetch("/api/v1/ip/home/rails");
        if (response.ok) {
          const data = await response.json();
          setIpRails(data.sections || []);
        }
      } catch (err) {
        console.error("Failed to fetch IP rails:", err);
      }
    }
    fetchIPRails();
  }, []);

  // Authenticated users go to studio
  useEffect(() => {
    if (isSessionLoading) return;
    if (isAuthenticated) {
      router.replace("/studio");
    }
  }, [isAuthenticated, isSessionLoading, router]);

  const handleIPItemClick = (item: { slug: string }) => {
    router.push("/ip/" + item.slug);
  };

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
            {/* IP Rails - IP-First UX */}
            {ipRails.length > 0 && (
              <motion.section
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="space-y-8">
                  {ipRails.slice(0, 2).map((section) => (
                    <HomeRailSection
                      key={section.section_id}
                      sectionId={section.section_id}
                      titleKo={section.title_ko}
                      titleEn={section.title_en}
                      items={section.items}
                      hasMore={section.has_more}
                      onSeeMore={() => router.push("/ip")}
                      onItemClick={handleIPItemClick}
                    />
                  ))}
                </div>
              </motion.section>
            )}

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
        <div className="min-h-screen flex items-center justify-center bg-[var(--bg-0)]">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
