"use client";

import type { TabKey } from "../../constants";
import { PageHeader, ContentCard, NextStepButton } from "../shared";
import { useMDParse } from "../../hooks/useMDParse";
import { MDInput } from "./MDInput";
import { AnchorGuidePanel } from "./AnchorGuidePanel";
import { SceneCard } from "./SceneCard";

interface ParseContentProps {
  setActiveTab: (tab: TabKey) => void;
}

export function ParseContent({ setActiveTab }: ParseContentProps) {
  const {
    mdInput,
    parseResult,
    activeType,
    copiedStates,
    completedPrompts,
    isDragging,
    activeScenes,
    totalPrompts,
    completedCount,
    warnings,
    getWarningsForScene,
    setMdInput,
    setActiveType,
    setIsDragging,
    handleCopy,
    clearProgress,
    handleFileDrop,
  } = useMDParse();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    await handleFileDrop(e.dataTransfer.files);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const text = await files[0].text();
      setMdInput(text);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[var(--academy-content-max)] space-y-4">
      <PageHeader title="파싱" sub="붙여넣고 복사" />

      <MDInput
        mdInput={mdInput}
        setMdInput={setMdInput}
        parseResult={parseResult}
        isDragging={isDragging}
        totalPrompts={totalPrompts}
        completedCount={completedCount}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onFileSelect={handleFileSelect}
        onClearProgress={clearProgress}
      />

      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <>
          <div className="grid grid-cols-2 gap-2 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-1">
            <button
              type="button"
              onClick={() => setActiveType("ohmage")}
              disabled={!parseResult.hasOhmage}
              className={`min-h-11 rounded-lg px-3 text-sm font-medium transition-colors ${
                activeType === "ohmage"
                  ? "bg-[var(--color-brand-primary)] text-white"
                  : parseResult.hasOhmage
                    ? "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
                    : "text-[var(--fg-muted)]/50"
              }`}
            >
              오마주 ({parseResult.ohmageScenes.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveType("variation")}
              disabled={!parseResult.hasVariation}
              className={`min-h-11 rounded-lg px-3 text-sm font-medium transition-colors ${
                activeType === "variation"
                  ? "bg-[var(--color-brand-primary)] text-white"
                  : parseResult.hasVariation
                    ? "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
                    : "text-[var(--fg-muted)]/50"
              }`}
            >
              변주 ({parseResult.variationScenes.length})
            </button>
          </div>

          {parseResult.anchors.length > 0 && (
            <AnchorGuidePanel anchors={parseResult.anchors} />
          )}

          {warnings.length > 0 && (
            <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-xs font-medium text-yellow-700 dark:text-yellow-200">
              경고 {warnings.length}개
            </div>
          )}

          <div className="space-y-3">
            {activeScenes?.map((scene) => (
              <SceneCard
                key={`${activeType}-${scene.sceneNum}`}
                scene={scene}
                copiedStates={copiedStates}
                completedPrompts={completedPrompts}
                onCopy={handleCopy}
                anchors={parseResult.anchors}
                warnings={getWarningsForScene(scene.sceneNum)}
              />
            ))}
          </div>
        </>
      )}

      {!parseResult && (
        <ContentCard>
          <div className="py-8 text-center text-sm text-[var(--fg-muted)]">MD 붙여넣기</div>
        </ContentCard>
      )}

      <NextStepButton onClick={() => setActiveTab("tools")} label="다음: 툴" />
    </div>
  );
}
