"use client";

import { useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  ExternalLink,
  FlaskConical,
  BookOpen,
  Clapperboard,
  Palette,
} from "lucide-react";
import { useDNACardContext } from "@/stores/dnaCardContextStore";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { SidePanelHeader } from "./SidePanelHeader";
import { SidePanelContent } from "./SidePanelContent";
import { DNA_CARD_CONFIG } from "../constants";
import type {
  DNACardType,
  MasterDNAMetadata,
  MasterpieceDNAMetadata,
  CharacterDNAMetadata,
} from "@/types/dna-card";

// Type-specific action configurations (2026 best practice)
// Tab values must match actual Mega App tabs:
// - DNA Lab: vpe, ad, mirror, qc
// - Story Engine: story, prompt, system-prompt
// - Production: veo, kling, suno, imagen
interface ActionConfig {
  label: string;
  icon: React.ReactNode;
  app: string;
  tab: string;
  primary?: boolean;
}

const TYPE_ACTIONS: Record<DNACardType, ActionConfig[]> = {
  master: [
    {
      label: "DNA Lab - Aesthetic",
      icon: <FlaskConical className="w-4 h-4" />,
      app: "dna-lab",
      tab: "ad",
      primary: true,
    },
    {
      label: "Story Engine",
      icon: <BookOpen className="w-4 h-4" />,
      app: "story-engine",
      tab: "story",
    },
  ],
  masterpiece: [
    {
      label: "DNA Lab - VPE",
      icon: <FlaskConical className="w-4 h-4" />,
      app: "dna-lab",
      tab: "vpe",
      primary: true,
    },
    {
      label: "Story Engine",
      icon: <BookOpen className="w-4 h-4" />,
      app: "story-engine",
      tab: "story",
    },
    {
      label: "Production - VEO",
      icon: <Clapperboard className="w-4 h-4" />,
      app: "production",
      tab: "veo",
    },
  ],
  character: [
    {
      label: "DNA Lab - Mirror",
      icon: <Palette className="w-4 h-4" />,
      app: "dna-lab",
      tab: "mirror",
      primary: true,
    },
    {
      label: "Story Engine",
      icon: <BookOpen className="w-4 h-4" />,
      app: "story-engine",
      tab: "story",
    },
  ],
};

export function DNACardSidePanel() {
  const router = useRouter();
  const { activeCard, isSidePanelOpen, closeSidePanel, setActiveCard } =
    useDNACardContext();

  // Focus trap for accessibility (2026 best practice)
  const { containerRef } = useFocusTrap<HTMLDivElement>({
    isActive: isSidePanelOpen,
    onEscape: closeSidePanel,
  });

  // Prevent body scroll when panel is open
  useEffect(() => {
    if (isSidePanelOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isSidePanelOpen]);

  // Navigate to specific app with unified URL parameters
  // Uses standard params (master, cardType, cardId) instead of _ctx snapshot
  const navigateToApp = useCallback(
    (app: string, tab: string) => {
      if (!activeCard) return;

      // Build URL with standard params (compatible with useDNACardContextConsumer)
      const params = new URLSearchParams({ tab });

      // Add type-specific context params
      if (activeCard.type === "master") {
        const metadata = activeCard.metadata as MasterDNAMetadata;
        params.set("master", metadata.auteurKey);
      } else if (activeCard.type === "masterpiece") {
        const metadata = activeCard.metadata as MasterpieceDNAMetadata;
        params.set("ipId", metadata.ipId);
      } else if (activeCard.type === "character") {
        const metadata = activeCard.metadata as CharacterDNAMetadata;
        params.set("characterId", metadata.characterId);
      }

      // Standard context identifiers
      params.set("cardType", activeCard.type);
      params.set("cardId", activeCard.id);

      // Add preloadParams if any
      if (activeCard.megaAppEntry.preloadParams) {
        Object.entries(activeCard.megaAppEntry.preloadParams).forEach(
          ([key, value]) => {
            params.set(key, value);
          }
        );
      }

      const href = `/${app}?${params.toString()}`;

      // Set context in store for immediate access in Mega App
      setActiveCard(activeCard);
      closeSidePanel();
      router.push(href);
    },
    [activeCard, setActiveCard, closeSidePanel, router]
  );

  // Primary action handler (first action in list)
  const handlePrimaryAction = useCallback(() => {
    if (!activeCard) return;
    const actions = TYPE_ACTIONS[activeCard.type];
    const primary = actions.find((a) => a.primary) || actions[0];
    navigateToApp(primary.app, primary.tab);
  }, [activeCard, navigateToApp]);

  // Get type-specific actions
  const actions = useMemo(() => {
    if (!activeCard) return [];
    return TYPE_ACTIONS[activeCard.type] || [];
  }, [activeCard]);

  if (!activeCard) return null;

  const config = DNA_CARD_CONFIG[activeCard.type];

  return (
    <AnimatePresence>
      {isSidePanelOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeSidePanel}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
            aria-hidden="true"
          />

          {/* Side Panel */}
          <motion.div
            ref={containerRef}
            initial={{ opacity: 0, x: "100%" }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-screen w-[440px] max-w-[90vw] z-[61] flex flex-col bg-[var(--surface-1)] border-l border-[var(--border-muted)] shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="side-panel-title"
          >
            {/* Header */}
            <SidePanelHeader card={activeCard} onClose={closeSidePanel} />

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
              <SidePanelContent card={activeCard} />
            </div>

            {/* Actions - Type-specific (2026 best practice) */}
            <div className="p-4 border-t border-[var(--border-muted)] bg-[var(--surface-1)] space-y-2">
              {/* Primary Action */}
              <button
                onClick={handlePrimaryAction}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white transition-all hover:opacity-90"
                style={{
                  background: `linear-gradient(135deg, oklch(0.55 0.2 ${activeCard.hue ?? config.hue}), oklch(0.45 0.15 ${(activeCard.hue ?? config.hue) + 30}))`,
                }}
              >
                {actions.find((a) => a.primary)?.icon || (
                  <FlaskConical className="w-4 h-4" />
                )}
                {actions.find((a) => a.primary)?.label || "DNA Lab"}
              </button>

              {/* Secondary Actions */}
              <div className="flex gap-2">
                {actions
                  .filter((a) => !a.primary)
                  .map((action, idx) => (
                    <button
                      key={idx}
                      onClick={() => navigateToApp(action.app, action.tab)}
                      className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium text-[var(--fg-muted)] hover:text-[var(--fg-default)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border-muted)] transition-all"
                      title={action.label}
                    >
                      {action.icon}
                      <span className="hidden sm:inline truncate">
                        {action.label.split(" - ")[1] || action.label}
                      </span>
                    </button>
                  ))}

                {/* View Full Detail */}
                <button
                  onClick={() =>
                    navigateToApp(
                      activeCard.megaAppEntry.app,
                      activeCard.megaAppEntry.tab
                    )
                  }
                  className="flex items-center justify-center px-3 py-2.5 rounded-xl text-[var(--fg-muted)] hover:text-[var(--fg-default)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border-muted)] transition-all"
                  title="View Full Detail"
                >
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

/**
 * Portal component to render Side Panel at root level
 * Add this to app/layout.tsx
 */
export function DNACardSidePanelPortal() {
  return <DNACardSidePanel />;
}
