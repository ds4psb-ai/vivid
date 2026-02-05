"use client";

import type { TabKey } from "../../constants";
import { PageHeader, ContentCard, NextStepButton } from "../shared";
import { useMDParse } from "../../hooks/useMDParse";
import { MDInput } from "./MDInput";
import { ImageAttachmentGuide } from "./ImageAttachmentGuide";
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
    setMdInput,
    setActiveType,
    setIsDragging,
    handleCopy,
    clearProgress,
    handleFileDrop,
  } = useMDParse();

  // 파일 드래그앤드롭 핸들러
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
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader title="파싱 + 복사" sub="MD 결과물 붙여넣기 → 씬별 프롬프트 복사" />

      {/* MD Input */}
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

      {/* Type Tabs */}
      {parseResult && (parseResult.hasOhmage || parseResult.hasVariation) && (
        <>
          <div className="flex items-center gap-4">
            {/* Type Tabs */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveType("ohmage")}
                disabled={!parseResult.hasOhmage}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeType === "ohmage"
                  ? "bg-purple-500 text-white"
                  : parseResult.hasOhmage
                    ? "bg-white/10 text-gray-400 hover:bg-white/20"
                    : "bg-white/5 text-gray-600 cursor-not-allowed"
                  }`}
              >
                🎭 오마주 ({parseResult.ohmageScenes.length})
              </button>
              <button
                onClick={() => setActiveType("variation")}
                disabled={!parseResult.hasVariation}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeType === "variation"
                  ? "bg-cyan-500 text-white"
                  : parseResult.hasVariation
                    ? "bg-white/10 text-gray-400 hover:bg-white/20"
                    : "bg-white/5 text-gray-600 cursor-not-allowed"
                  }`}
              >
                ✨ 변주 ({parseResult.variationScenes.length})
              </button>
            </div>

          </div>

          {/* Image Attachment Workflow Guide */}
          <ImageAttachmentGuide />

          {/* Anchor Guide Panel */}
          {parseResult.anchors.length > 0 && (
            <AnchorGuidePanel anchors={parseResult.anchors} />
          )}

          {/* Scene Cards */}
          <div className="space-y-4">
            {activeScenes?.map((scene) => (
              <SceneCard
                key={`${activeType}-${scene.sceneNum}`}
                scene={scene}
                copiedStates={copiedStates}
                completedPrompts={completedPrompts}
                onCopy={handleCopy}
                anchors={parseResult.anchors}
              />
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!parseResult && (
        <ContentCard>
          <div className="text-center py-8">
            <span className="material-symbols-outlined text-4xl text-gray-600 mb-4 block">content_paste</span>
            <p className="text-gray-500">MD 파일 내용을 위에 붙여넣으면 씬별로 파싱됩니다</p>
          </div>
        </ContentCard>
      )}

      <NextStepButton onClick={() => setActiveTab("tools")} label="외부 툴" />
    </div>
  );
}
