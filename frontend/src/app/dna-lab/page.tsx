"use client";

/**
 * DNA Lab Hub - Integrated Workflow Mega App
 *
 * 2026 UX Enhancement:
 * - Smart Onboarding: 3 entry options (IP select, URL input, Quick start)
 * - Step-based workflow (not tab-based)
 * - Chain data flow between steps
 * - Non-sequential access supported
 * - AI inference for missing data
 * - Phase 3: IP-based chain data initialization
 *
 * Workflow:
 * VPE (영상분석) → AD (미학적용) → Mirror (창작DNA) → QC (품질검증)
 *     │              │               │              │
 *     v              v               v              v
 * LogicVector → AestheticGuidelines → PersonaDNA → QualityReport
 *
 * URL Parameters:
 * - step: Current step (vpe, ad, mirror, qc)
 * - master: Auteur key for AD/VPE (bong, epoch, wong, etc.)
 * - ip: IP slug for chain data persistence
 * - url: Video URL for direct analysis
 * - mode: Entry mode (quick for quick start)
 *
 * Entry Flow:
 * /dna-lab → DNALabOnboarding (3 options) → Workflow
 * /dna-lab?ip=xxx → Skip onboarding, direct workflow with IP data
 * /dna-lab?url=xxx → Skip onboarding, analyze URL
 * /dna-lab?master=xxx&mode=quick → Quick start with master style
 *
 * Phase 3 Enhancement (2026.01):
 * - useIPChainData hook for IP + chain data integration
 * - Auto session restore per IP
 * - IP-based suggested defaults for MissingDataBanner
 *
 * Migration Note (2026.01):
 * Using UnifiedWorkflowShell instead of DNALabWorkflowShell
 * for consistent cross-MegaApp behavior.
 */

import { useState, useEffect, Suspense, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Database } from "lucide-react";
import { UnifiedWorkflowShell, MissingDataBanner, useIPChainData, DNALabOverview } from "@/components/workflow";
import { DNALabStepPanel, DNALabRunPipelineButton, DNALabOnboarding, type DNALabStepId } from "@/components/dna-lab";
import AppShell from "@/components/AppShell";

// Import existing panels
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";
import QualityDirectorPanel from "@/components/dimension/QualityDirectorPanel";
import UnifiedAnalysisPanel from "@/components/dimension/UnifiedAnalysisPanel";

export default function DNALabPage() {
  return (
    <Suspense fallback={<DNALabLoadingFallback />}>
      <DNALabPageContent />
    </Suspense>
  );
}

/**
 * Loading fallback for Suspense
 */
function DNALabLoadingFallback() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center bg-black">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-white/60" />
          <p className="text-sm text-white/40">Loading DNA Lab...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * Main content with URL parameter handling
 *
 * Phase 6 Routing Logic:
 * - /dna-lab (no params, no session) → Onboarding
 * - /dna-lab?ip=slug → Overview (IP connected)
 * - /dna-lab?step=overview → Overview (explicit)
 * - /dna-lab?step=vpe → Step detail
 * - /dna-lab (has session) → Overview
 */
function DNALabPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Check for URL parameters
  const step = searchParams?.get("step");
  const ipSlug = searchParams?.get("ip");
  const videoUrl = searchParams?.get("url");
  const masterKey = searchParams?.get("master");

  // Manual dismissal state for onboarding
  const [manuallyDismissed, setManuallyDismissed] = useState(false);

  // Check for existing session (simple check - any chain data present)
  // This is a lightweight check; full session restoration happens in useIPChainData
  const [hasExistingSession, setHasExistingSession] = useState(false);

  useEffect(() => {
    // Check localStorage for any DNA Lab session data
    if (typeof window !== "undefined") {
      const sessionKeys = Object.keys(localStorage).filter(
        (key) => key.startsWith("dna-lab-session") || key.startsWith("chain-data-dna-lab")
      );
      setHasExistingSession(sessionKeys.length > 0);
    }
  }, []);

  // Determine view mode
  const hasEntryParams = !!(ipSlug || videoUrl || masterKey);
  const isStepDetail = step && step !== "overview";
  const isExplicitOverview = step === "overview";

  // 1. Onboarding: No params + no session + not manually dismissed
  const showOnboarding = !hasEntryParams && !step && !hasExistingSession && !manuallyDismissed;

  // 2. Overview: step=overview OR (no step + (ipSlug OR hasSession OR manuallyDismissed))
  const showOverview = isExplicitOverview || (!isStepDetail && !showOnboarding && (ipSlug || hasExistingSession || manuallyDismissed));

  // Onboarding handlers
  const handleSelectIP = (slug: string) => {
    if (slug) {
      router.push(`/dna-lab?ip=${slug}`);
    } else {
      // Navigate to main page IP gallery
      router.push("/?section=ip");
    }
  };

  const handleEnterURL = (url: string) => {
    router.push(`/dna-lab?url=${encodeURIComponent(url)}`);
  };

  const handleQuickStart = (master: string) => {
    router.push(`/dna-lab?master=${master}&mode=quick`);
  };

  const handleManualStart = () => {
    setManuallyDismissed(true);
  };

  // Overview navigation handler
  const handleStepClick = (stepId: string) => {
    const params = new URLSearchParams();
    params.set("step", stepId);
    if (ipSlug) params.set("ip", ipSlug);
    router.push(`/dna-lab?${params.toString()}`);
  };

  // 1. Show Onboarding
  if (showOnboarding) {
    return (
      <AppShell showTopBar={false} showNavbar={false}>
        <DNALabOnboarding
          onSelectIP={handleSelectIP}
          onEnterURL={handleEnterURL}
          onQuickStart={handleQuickStart}
          onManualStart={handleManualStart}
        />
      </AppShell>
    );
  }

  // 2. Show Overview
  if (showOverview) {
    return (
      <UnifiedWorkflowShell
        appId="dna-lab"
        showAurora={true}
        showWorkflowProgress={false}
        showChainSummary={false}
        headerRight={
          <div className="flex items-center gap-3">
            {ipSlug && (
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-500/10 text-violet-400 text-xs">
                <Database className="w-3.5 h-3.5" />
                <span className="font-medium">{ipSlug}</span>
              </div>
            )}
            <DNALabRunPipelineButton className="hidden sm:flex" />
          </div>
        }
      >
        {() => (
          <DNALabOverview
            ipSlug={ipSlug}
            onStepClick={handleStepClick}
          />
        )}
      </UnifiedWorkflowShell>
    );
  }

  // 3. Show Step Detail (original workflow)
  return (
    <UnifiedWorkflowShell
      appId="dna-lab"
      showAurora={true}
      showWorkflowProgress={true}
      showChainSummary={true}
      headerRight={
        <div className="flex items-center gap-3">
          {/* IP indicator when connected */}
          {ipSlug && (
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-violet-500/10 text-violet-400 text-xs">
              <Database className="w-3.5 h-3.5" />
              <span className="font-medium">{ipSlug}</span>
            </div>
          )}
          <DNALabRunPipelineButton className="hidden sm:flex" />
        </div>
      }
    >
      {(currentStepId, disclosureLevel) => (
        <StepContent
          stepId={currentStepId as DNALabStepId}
          ipSlug={ipSlug}
          disclosureLevel={disclosureLevel}
        />
      )}
    </UnifiedWorkflowShell>
  );
}

/** Disclosure level for progressive UI complexity */
type DisclosureLevel = "basic" | "intermediate" | "advanced";

/**
 * Step content renderer
 * Wraps each panel with DNALabStepPanel for chain data integration
 *
 * Phase 3: Enhanced with IP-based suggested defaults
 * Phase 2-1: Added disclosureLevel prop for progressive disclosure
 */
interface StepContentProps {
  stepId: DNALabStepId;
  ipSlug: string | null;
  disclosureLevel?: DisclosureLevel;
}

function StepContent({ stepId, ipSlug, disclosureLevel = "intermediate" }: StepContentProps) {
  // Phase 3: IP + Chain Data integration
  const {
    ipData,
    ipLoading,
    hasMissingData,
    missingKeys,
    ipDefaults,
    applySuggestion,
    goToSource,
    saveToIP,
    sessionRestored,
    hasExistingSession,
  } = useIPChainData({
    ipSlug,
    requiredKeys: getRequiredKeysForStep(stepId),
    autoRestoreSession: true,
    autoFetchIP: true,
  });

  // Auto-save chain data to session when it changes (debounced)
  useEffect(() => {
    if (!ipSlug) return;

    const timer = setTimeout(() => {
      saveToIP();
    }, 1000); // Debounce 1s

    return () => clearTimeout(timer);
  }, [ipSlug, saveToIP]);

  // Handler for dismissing suggestions (optional logging)
  const handleDismissSuggestion = useCallback((key: string) => {
    console.log(`[DNALab] User dismissed suggestion for: ${key}`);
  }, []);

  // Show loading indicator while IP data is being fetched
  if (ipSlug && ipLoading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-violet-400" />
        <p className="text-sm text-white/50">
          프로젝트 데이터 로딩 중...
        </p>
      </div>
    );
  }

  // Session restoration indicator
  const showSessionBadge = ipSlug && sessionRestored && hasExistingSession;

  // Step-specific content with IP-aware MissingDataBanner
  const renderStepContent = () => {
    // Show MissingDataBanner with suggested defaults if data is missing
    const showMissingBanner = hasMissingData && stepId !== "analysis"; // analysis is start step

    switch (stepId) {
      case "analysis":
        return (
          <DNALabStepPanel stepId="analysis" showInputBanner={false}>
            <div className="p-4">
              {/* IP info header when connected */}
              {ipData && (
                <IPContextHeader
                  ipData={ipData}
                  sessionRestored={sessionRestored}
                />
              )}
              <UnifiedAnalysisPanel disclosureLevel={disclosureLevel} />
            </div>
          </DNALabStepPanel>
        );

      case "mirror":
        return (
          <DNALabStepPanel stepId="mirror">
            {showMissingBanner && (
              <div className="mb-4">
                <MissingDataBanner
                  missingKeys={missingKeys}
                  onGoToSource={goToSource}
                  suggestedDefaults={ipDefaults}
                  onApplySuggestion={applySuggestion}
                  onDismissSuggestion={handleDismissSuggestion}
                  variant="info"
                />
              </div>
            )}
            <AbyssMirrorPanel />
          </DNALabStepPanel>
        );

      case "qc":
        return (
          <DNALabStepPanel stepId="qc">
            {showMissingBanner && (
              <div className="mb-4">
                <MissingDataBanner
                  missingKeys={missingKeys}
                  onGoToSource={goToSource}
                  suggestedDefaults={ipDefaults}
                  onApplySuggestion={applySuggestion}
                  onDismissSuggestion={handleDismissSuggestion}
                  variant="warning"
                />
              </div>
            )}
            <QualityDirectorPanel />
          </DNALabStepPanel>
        );

      default:
        // Fallback to analysis for unknown steps
        return (
          <DNALabStepPanel stepId="analysis" showInputBanner={false}>
            <div className="p-4">
              {ipData && (
                <IPContextHeader
                  ipData={ipData}
                  sessionRestored={sessionRestored}
                />
              )}
              <UnifiedAnalysisPanel disclosureLevel={disclosureLevel} />
            </div>
          </DNALabStepPanel>
        );
    }
  };

  return renderStepContent();
}

/**
 * IP Context Header - Shows IP info when connected
 */
function IPContextHeader({
  ipData,
  sessionRestored,
}: {
  ipData: { name_ko: string; slug: string; genre?: string[] };
  sessionRestored: boolean;
}) {
  return (
    <div className="mb-4 p-3 rounded-lg bg-violet-500/5 border border-violet-500/10">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-violet-400" />
          <span className="text-sm font-medium text-white">
            {ipData.name_ko}
          </span>
          {ipData.genre && ipData.genre.length > 0 && (
            <span className="text-xs text-white/40">
              {ipData.genre[0]}
            </span>
          )}
        </div>
        {sessionRestored && (
          <span className="text-xs text-emerald-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            세션 복원됨
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Get required chain data keys for each step
 * Phase 1-2: Updated for merged analysis step
 *
 * Note: Uses "analysis" key for unified VPE+AD output
 */
function getRequiredKeysForStep(stepId: DNALabStepId): string[] {
  switch (stepId) {
    case "analysis":
      return []; // Analysis (VPE+AD merged) is the starting step, no requirements
    case "mirror":
      return ["analysis"]; // Mirror requires analysis output
    case "qc":
      return ["analysis", "mirror"]; // QC requires all previous
    default:
      return [];
  }
}
