"use client";

/**
 * UnifiedWorkflowShell - Adaptive Layout Engine
 *
 * Single shell component that adapts to each Mega App's configuration.
 * Replaces DNALabWorkflowShell and MegaAppShell with unified behavior.
 *
 * 2026 Pattern: "One Shell, Many Behaviors"
 * - Config determines appearance and features
 * - Same component, different experiences
 */

import { Suspense, useEffect, useState } from "react";
import { Loader2, ChevronRight, PanelRightClose, PanelRightOpen } from "lucide-react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { MegaAppHeader } from "@/components/mega-app/MegaAppHeader";
import { MegaAppAurora } from "@/components/mega-app/MegaAppAurora";
import { WorkflowProgress } from "@/components/mega-app/WorkflowProgress";
import { UnifiedChainSidebar } from "./UnifiedChainSidebar";
import { UnifiedWorkflowProgress } from "./UnifiedWorkflowProgress";
import { UnifiedStepNav } from "./UnifiedStepNav";
import { MissingDataBanner } from "./MissingDataBanner";
import { useUnifiedWorkflow } from "./hooks/useUnifiedWorkflow";
import { getWorkflowConfig, CHAIN_DATA_SOURCE_MAP } from "./workflow-configs";
import { cn } from "@/lib/utils";
import type { MegaAppId, UnifiedWorkflowShellProps } from "./types";

/**
 * UnifiedWorkflowShell - Main adaptive shell component
 *
 * @example
 * ```tsx
 * <UnifiedWorkflowShell appId="dna-lab">
 *   {(currentStepId) => <StepPanel stepId={currentStepId} />}
 * </UnifiedWorkflowShell>
 * ```
 */
export function UnifiedWorkflowShell({
  appId,
  children,
  showAurora = true,
  showWorkflowProgress = true,
  showChainSummary = true,
  headerRight,
}: UnifiedWorkflowShellProps) {
  return (
    <Suspense fallback={<UnifiedLoading appId={appId} />}>
      <UnifiedWorkflowShellContent
        appId={appId}
        showAurora={showAurora}
        showWorkflowProgress={showWorkflowProgress}
        showChainSummary={showChainSummary}
        headerRight={headerRight}
      >
        {children}
      </UnifiedWorkflowShellContent>
    </Suspense>
  );
}

/**
 * Loading state
 */
function UnifiedLoading({ appId }: { appId: MegaAppId }) {
  const config = getWorkflowConfig(appId);

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center bg-black">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-white/60" />
          <p className="text-sm text-white/40">Loading {config.title}...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * Inner content component
 */
function UnifiedWorkflowShellContent({
  appId,
  children,
  showAurora,
  showWorkflowProgress,
  showChainSummary,
  headerRight,
}: UnifiedWorkflowShellProps) {
  const config = getWorkflowConfig(appId);
  const workflow = useUnifiedWorkflow(config);
  const { currentStepId, currentStep } = workflow;
  const chain = useDimensionChainOptional();
  const searchParams = useSearchParams();

  // Sidebar state (respect config default)
  const [sidebarOpen, setSidebarOpen] = useState(!config.sidebar.defaultCollapsed);

  // Auto-load chain data from session if ipSlug is provided
  useEffect(() => {
    const ipSlug = searchParams?.get("ip");
    if (ipSlug && chain?.hasSessionData(ipSlug) && Object.keys(chain.chainData).length === 0) {
      chain.loadFromSession(ipSlug);
    }
  }, [searchParams, chain]);

  // Auto-sync to session when chain data changes
  useEffect(() => {
    const ipSlug = searchParams?.get("ip");
    if (!ipSlug || !chain || Object.keys(chain.chainData).length === 0) return;

    const timeoutId = setTimeout(() => {
      chain.syncToSession(ipSlug);
    }, 1000);

    return () => clearTimeout(timeoutId);
  }, [searchParams, chain, chain?.chainData]);

  // Check for missing required chain data (from previous apps)
  const missingRequiredData = config.requiredChainData?.filter(
    (key) => !chain?.chainData[key]
  ) || [];

  // Navigation handler for missing data
  const handleGoToSource = (key: string) => {
    const source = CHAIN_DATA_SOURCE_MAP[key];
    if (!source) return;
    const stepParam = "step";
    window.location.href = `/${source.app}?${stepParam}=${source.step}`;
  };

  const CurrentIcon = currentStep.icon;

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex flex-col bg-black relative">
        {/* Aurora Background */}
        {showAurora && <MegaAppAurora appId={appId} />}

        {/* Global Workflow Progress (DNA Lab → Story Engine → Production) */}
        {showWorkflowProgress && <WorkflowProgress currentAppId={appId} />}

        {/* Header */}
        <MegaAppHeader
          appId={appId}
          title={config.title}
          subtitle={config.subtitle}
          icon={config.icon}
          headerRight={
            <div className="flex items-center gap-4">
              {headerRight}
              {/* Sidebar toggle (desktop) - only if collapsible */}
              {showChainSummary && config.sidebar.collapsible && (
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="hidden lg:flex items-center gap-2 px-3 py-1.5 text-sm text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                >
                  {sidebarOpen ? (
                    <>
                      <PanelRightClose className="w-4 h-4" />
                      <span>요약 닫기</span>
                    </>
                  ) : (
                    <>
                      <PanelRightOpen className="w-4 h-4" />
                      <span>체인 요약</span>
                    </>
                  )}
                </button>
              )}
            </div>
          }
        />

        {/* Step Progress */}
        <div className="px-4 py-3 border-b border-white/10">
          <UnifiedWorkflowProgress workflow={workflow} config={config} />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Panel Content */}
          <div
            className={cn(
              "flex-1 flex flex-col overflow-hidden",
              sidebarOpen && showChainSummary && "lg:pr-80"
            )}
          >
            {/* Current step indicator */}
            <div className="px-4 py-2 flex items-center gap-2 text-sm text-white/60 border-b border-white/5">
              <CurrentIcon className="w-4 h-4" />
              <span>{currentStep.label}</span>
              <ChevronRight className="w-3 h-3" />
              <span className="text-white/40">{currentStep.description}</span>
            </div>

            {/* Missing required data banner */}
            {missingRequiredData.length > 0 && (
              <div className="px-4 py-3 border-b border-white/5">
                <MissingDataBanner
                  missingKeys={missingRequiredData}
                  onGoToSource={handleGoToSource}
                  message={`${config.title}을 사용하려면 이전 단계의 데이터가 필요합니다.`}
                  variant="warning"
                />
              </div>
            )}

            {/* Panel content */}
            <div className="flex-1 overflow-auto">{children(currentStepId)}</div>

            {/* Step Navigation */}
            <UnifiedStepNav workflow={workflow} />
          </div>

          {/* Chain Summary Sidebar (desktop) */}
          {showChainSummary && (
            <div
              className={cn(
                "hidden lg:block fixed right-0 top-0 bottom-0 w-80 transform transition-transform duration-300",
                sidebarOpen ? "translate-x-0" : "translate-x-full",
                // Non-collapsible sidebar is always visible
                !config.sidebar.collapsible && "translate-x-0"
              )}
              style={{ marginTop: showWorkflowProgress ? "40px" : "0" }}
            >
              <UnifiedChainSidebar
                mode={config.sidebar.mode}
                workflow={workflow}
                config={config}
                onClose={config.sidebar.collapsible ? () => setSidebarOpen(false) : undefined}
              />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
