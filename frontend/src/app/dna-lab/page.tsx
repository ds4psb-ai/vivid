"use client";

/**
 * DNA Lab Hub - Integrated Workflow Mega App
 *
 * 2026 UX Enhancement:
 * - Step-based workflow (not tab-based)
 * - Chain data flow between steps
 * - Non-sequential access supported
 * - AI inference for missing data
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
 *
 * Migration Note (2026.01):
 * Using UnifiedWorkflowShell instead of DNALabWorkflowShell
 * for consistent cross-MegaApp behavior.
 */

import { UnifiedWorkflowShell } from "@/components/workflow";
import { DNALabStepPanel, DNALabRunPipelineButton, type DNALabStepId } from "@/components/dna-lab";

// Import existing panels
import AestheticDirectorPanel from "@/components/dimension/AestheticDirectorPanel";
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";
import QualityDirectorPanel from "@/components/dimension/QualityDirectorPanel";
import VPEPanel from "@/components/dimension/VPEPanel";

export default function DNALabPage() {
  return (
    <UnifiedWorkflowShell
      appId="dna-lab"
      showAurora={true}
      showWorkflowProgress={true}
      showChainSummary={true}
      headerRight={<DNALabRunPipelineButton className="hidden sm:flex" />}
    >
      {(currentStepId) => (
        <StepContent stepId={currentStepId as DNALabStepId} />
      )}
    </UnifiedWorkflowShell>
  );
}

/**
 * Step content renderer
 * Wraps each panel with DNALabStepPanel for chain data integration
 */
function StepContent({ stepId }: { stepId: DNALabStepId }) {
  switch (stepId) {
    case "vpe":
      return (
        <DNALabStepPanel stepId="vpe" showInputBanner={false}>
          <div className="p-4">
            <VPEPanel />
          </div>
        </DNALabStepPanel>
      );

    case "ad":
      return (
        <DNALabStepPanel stepId="ad">
          <AestheticDirectorPanel />
        </DNALabStepPanel>
      );

    case "mirror":
      return (
        <DNALabStepPanel stepId="mirror">
          <AbyssMirrorPanel />
        </DNALabStepPanel>
      );

    case "qc":
      return (
        <DNALabStepPanel stepId="qc">
          <QualityDirectorPanel />
        </DNALabStepPanel>
      );

    default:
      return (
        <div className="p-8 text-center text-white/40">
          Unknown step: {stepId}
        </div>
      );
  }
}
