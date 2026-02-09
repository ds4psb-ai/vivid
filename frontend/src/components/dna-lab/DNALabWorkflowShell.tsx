"use client";

/**
 * DNALabWorkflowShell - Main Container for DNA Lab Workflow
 *
 * Replaces MegaAppShell with integrated workflow semantics:
 * - Step-based navigation (not tab-based)
 * - Chain data flow visualization
 * - Non-sequential access support
 * - Mobile-responsive layout
 *
 * 2026 Trends:
 * - "Value Before Step" pattern
 * - Intent-driven entry points
 * - Parallel preview capability
 */

import { Suspense, useEffect, useState } from "react";
import { Loader2, Dna, ChevronRight, PanelRightClose, PanelRightOpen } from "lucide-react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { useDimensionChainOptional } from "@/contexts/DimensionChainContext";
import { MegaAppHeader } from "@/components/mega-app/MegaAppHeader";
import { MegaAppAurora } from "@/components/mega-app/MegaAppAurora";
import { WorkflowProgress } from "@/components/mega-app/WorkflowProgress";
import { DNALabWorkflowProgress } from "./DNALabWorkflowProgress";
import { DNALabChainSummary } from "./DNALabChainSummary";
import { DNALabStepNav, DNALabRunPipelineButton } from "./DNALabStepNav";
import { useDNALabWorkflow } from "./hooks/useDNALabWorkflow";
import { DNA_LAB_STEPS_MAP, type DNALabStepId } from "./constants";
import { cn } from "@/lib/utils";

interface DNALabWorkflowShellProps {
  /** Children render function receives current step ID */
  children: (stepId: DNALabStepId) => React.ReactNode;
  /** Show aurora background */
  showAurora?: boolean;
  /** Show global workflow progress (DNA Lab → Story Engine → Production) */
  showWorkflowProgress?: boolean;
  /** Show chain summary sidebar */
  showChainSummary?: boolean;
  /** Header right slot */
  headerRight?: React.ReactNode;
}

/**
 * DNA Lab Workflow Shell
 *
 * Provides integrated workflow experience with step navigation,
 * chain data visualization, and responsive layout.
 */
export function DNALabWorkflowShell({
  children,
  showAurora = true,
  showWorkflowProgress = true,
  showChainSummary = true,
  headerRight,
}: DNALabWorkflowShellProps) {
  return (
    <Suspense fallback={<DNALabLoading />}>
      <DNALabWorkflowShellContent
        showAurora={showAurora}
        showWorkflowProgress={showWorkflowProgress}
        showChainSummary={showChainSummary}
        headerRight={headerRight}
      >
        {children}
      </DNALabWorkflowShellContent>
    </Suspense>
  );
}

/**
 * Loading state
 */
function DNALabLoading() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center bg-stitch-dark">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-white/60" />
          <p className="text-sm text-white/40">Loading DNA Lab...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * Inner content component
 */
function DNALabWorkflowShellContent({
  children,
  showAurora,
  showWorkflowProgress,
  showChainSummary,
  headerRight,
}: DNALabWorkflowShellProps) {
  const workflow = useDNALabWorkflow();
  const { currentStepId, currentStep } = workflow;
  const chain = useDimensionChainOptional();
  const searchParams = useSearchParams();

  // Sidebar state
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex flex-col bg-stitch-dark relative">
        {/* Aurora Background */}
        {showAurora && <MegaAppAurora appId="dna-lab" />}

        {/* Global Workflow Progress (DNA Lab → Story Engine → Production) */}
        {showWorkflowProgress && <WorkflowProgress currentAppId="dna-lab" />}

        {/* Header */}
        <MegaAppHeader
          appId="dna-lab"
          title="DNA Lab"
          subtitle="통합 워크플로우"
          icon={Dna}
          headerRight={
            <div className="flex items-center gap-4">
              {/* Run Pipeline Button */}
              <DNALabRunPipelineButton className="hidden sm:flex" />
              {headerRight}
              {/* Sidebar toggle (desktop) */}
              {showChainSummary && (
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
          <DNALabWorkflowProgress />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex overflow-hidden">
          {/* Panel Content */}
          <div className={cn("flex-1 flex flex-col overflow-hidden", sidebarOpen && "lg:pr-80")}>
            {/* Current step indicator */}
            <div className="px-4 py-2 flex items-center gap-2 text-sm text-white/60 border-b border-white/5">
              <currentStep.icon className="w-4 h-4" />
              <span>{currentStep.label}</span>
              <ChevronRight className="w-3 h-3" />
              <span className="text-white/40">{currentStep.description}</span>
            </div>

            {/* Panel content */}
            <div className="flex-1 overflow-auto">{children(currentStepId)}</div>

            {/* Step Navigation */}
            <DNALabStepNav />
          </div>

          {/* Chain Summary Sidebar (desktop) */}
          {showChainSummary && (
            <div
              className={cn(
                "hidden lg:block fixed right-0 top-0 bottom-0 w-80 transform transition-transform duration-300",
                sidebarOpen ? "translate-x-0" : "translate-x-full"
              )}
              style={{ marginTop: showWorkflowProgress ? "40px" : "0" }}
            >
              <DNALabChainSummary onClose={() => setSidebarOpen(false)} />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
