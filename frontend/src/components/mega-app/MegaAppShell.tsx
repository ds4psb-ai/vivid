"use client";

import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import { MegaAppHeader } from "./MegaAppHeader";
import { MegaAppTabs } from "./MegaAppTabs";
import { WorkflowProgress } from "./WorkflowProgress";
import { MegaAppAurora } from "./MegaAppAurora";
import { useMegaAppTab } from "./hooks/useMegaAppTab";
import type { MegaAppShellProps } from "./types";

/**
 * MegaAppShell - Unified shell component for mega apps
 *
 * Features:
 * - Glass morphism header with theme glow
 * - URL-synchronized tabs
 * - Optional workflow progress navigation
 * - Optional aurora background
 * - Built-in Suspense boundary
 * - Responsive design
 *
 * @example
 * ```tsx
 * <MegaAppShell
 *   appId="dna-lab"
 *   title="DNA Lab"
 *   subtitle="거장 DNA 분석 및 오케스트레이션"
 *   icon={Dna}
 *   tabs={TABS}
 *   defaultTab="vpe"
 * >
 *   {(activeTab) => (
 *     <>
 *       {activeTab === "vpe" && <VPEPanel />}
 *       {activeTab === "ad" && <AestheticDirectorPanel />}
 *     </>
 *   )}
 * </MegaAppShell>
 * ```
 */
export function MegaAppShell({
  appId,
  title,
  subtitle,
  icon,
  tabs,
  defaultTab,
  children,
  headerRight,
  showAurora = false,
  showWorkflowProgress = true,
  tabParamName = "tab",
}: MegaAppShellProps) {
  return (
    <Suspense fallback={<MegaAppLoading title={title} />}>
      <MegaAppShellContent
        appId={appId}
        title={title}
        subtitle={subtitle}
        icon={icon}
        tabs={tabs}
        defaultTab={defaultTab}
        headerRight={headerRight}
        showAurora={showAurora}
        showWorkflowProgress={showWorkflowProgress}
        tabParamName={tabParamName}
      >
        {children}
      </MegaAppShellContent>
    </Suspense>
  );
}

/**
 * Loading state for MegaAppShell
 */
function MegaAppLoading({ title }: { title: string }) {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center bg-black">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-white/60" />
          <p className="text-sm text-white/40">Loading {title}...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * Inner content component that uses hooks
 */
function MegaAppShellContent({
  appId,
  title,
  subtitle,
  icon,
  tabs,
  defaultTab,
  children,
  headerRight,
  showAurora,
  showWorkflowProgress,
  tabParamName,
}: MegaAppShellProps) {
  const { activeTab, setActiveTab } = useMegaAppTab({
    tabs,
    defaultTab,
    paramName: tabParamName,
  });

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex flex-col bg-black relative">
        {/* Aurora Background */}
        {showAurora && <MegaAppAurora appId={appId} />}

        {/* Workflow Progress */}
        {showWorkflowProgress && <WorkflowProgress currentAppId={appId} />}

        {/* Header */}
        <MegaAppHeader
          appId={appId}
          title={title}
          subtitle={subtitle}
          icon={icon}
          headerRight={headerRight}
        />

        {/* Tabs */}
        <MegaAppTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {/* Content */}
        <div className="flex-1 overflow-auto relative">{children(activeTab)}</div>
      </div>
    </AppShell>
  );
}
