"use client";

import { Dna, Video, Palette, Brain, CheckCircle } from "lucide-react";
import { MegaAppShell, type MegaAppTab } from "@/components/mega-app";

// Import existing panels
import AestheticDirectorPanel from "@/components/dimension/AestheticDirectorPanel";
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";
import QualityDirectorPanel from "@/components/dimension/QualityDirectorPanel";
import VPEPanel from "@/components/dimension/VPEPanel";

/**
 * DNA Lab Hub - Mega App for Auteur DNA Orchestration
 *
 * Consolidates:
 * - VPE (Video Parsing Engine) - Extracts Logic Vector from video
 * - AD (Aesthetic Director)
 * - Mirror (Abyss Mirror)
 * - QC (Quality Director)
 */

const TABS: MegaAppTab[] = [
  {
    value: "vpe",
    label: "비디오 파싱",
    labelEn: "Video Parsing",
    icon: <Video className="w-4 h-4" />,
    description: "영상 분석으로 Logic Vector 추출",
    isNew: true,
  },
  {
    value: "ad",
    label: "미학 디렉터",
    labelEn: "Aesthetic Director",
    icon: <Palette className="w-4 h-4" />,
    description: "거장들의 미학을 적용합니다",
  },
  {
    value: "mirror",
    label: "심연의 거울",
    labelEn: "Abyss Mirror",
    icon: <Brain className="w-4 h-4" />,
    description: "나만의 취향과 창작 DNA 분석",
  },
  {
    value: "qc",
    label: "퀄리티 디렉터",
    labelEn: "Quality Director",
    icon: <CheckCircle className="w-4 h-4" />,
    description: "시각적 일관성 및 품질 검수",
  },
];

export default function DNALabPage() {
  return (
    <MegaAppShell
      appId="dna-lab"
      title="DNA Lab"
      subtitle="거장 DNA 분석 및 오케스트레이션"
      icon={Dna}
      tabs={TABS}
      defaultTab="vpe"
    >
      {(activeTab) => (
        <>
          {activeTab === "vpe" && (
            <div className="p-4">
              <VPEPanel />
            </div>
          )}
          {activeTab === "ad" && <AestheticDirectorPanel />}
          {activeTab === "mirror" && <AbyssMirrorPanel />}
          {activeTab === "qc" && <QualityDirectorPanel />}
        </>
      )}
    </MegaAppShell>
  );
}
