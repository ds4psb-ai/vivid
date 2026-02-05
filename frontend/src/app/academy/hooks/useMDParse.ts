"use client";

import { useState, useEffect, useCallback } from "react";
import { parseBuilder2Output, type Builder2ParseResult } from "@/lib/builder2-md-parser";

interface UseMDParseReturn {
  // State
  mdInput: string;
  parseResult: Builder2ParseResult | null;
  activeType: "ohmage" | "variation";
  copiedStates: Record<string, boolean>;
  completedPrompts: Set<string>;
  isDragging: boolean;

  // Computed
  activeScenes: Builder2ParseResult["ohmageScenes"] | undefined;
  totalPrompts: number;
  completedCount: number;

  // Actions
  setMdInput: (input: string) => void;
  setActiveType: (type: "ohmage" | "variation") => void;
  setIsDragging: (dragging: boolean) => void;
  handleCopy: (key: string, text: string) => Promise<void>;
  clearProgress: () => void;
  handleFileDrop: (files: FileList) => Promise<void>;
}

export function useMDParse(): UseMDParseReturn {
  const [mdInput, setMdInput] = useState("");
  const [parseResult, setParseResult] = useState<Builder2ParseResult | null>(null);
  const [activeType, setActiveType] = useState<"ohmage" | "variation">("ohmage");
  const [copiedStates, setCopiedStates] = useState<Record<string, boolean>>({});
  const [completedPrompts, setCompletedPrompts] = useState<Set<string>>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('academy_parse_progress');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    }
    return new Set();
  });
  const [isDragging, setIsDragging] = useState(false);

  // Parse MD when input changes
  useEffect(() => {
    if (mdInput.trim()) {
      const result = parseBuilder2Output(mdInput);
      setParseResult(result);
      // Auto-select type based on what's available
      if (result.hasVariation && !result.hasOhmage) {
        setActiveType("variation");
      } else {
        setActiveType("ohmage");
      }
    } else {
      setParseResult(null);
    }
  }, [mdInput]);

  const activeScenes = activeType === "ohmage" ? parseResult?.ohmageScenes : parseResult?.variationScenes;

  const totalPrompts = activeScenes?.reduce((acc, scene) => {
    let count = 0;
    if (scene.imagePrompts.nanoBanana) count++;
    if (scene.imagePrompts.midjourney) count++;
    if (scene.motionPrompts.kling) count++;
    if (scene.motionPrompts.veo) count++;
    return acc + count;
  }, 0) || 0;

  const completedCount = activeScenes?.reduce((acc, scene) => {
    let count = 0;
    if (completedPrompts.has(`${scene.sceneNum}-nanoBanana`)) count++;
    if (completedPrompts.has(`${scene.sceneNum}-midjourney`)) count++;
    if (completedPrompts.has(`${scene.sceneNum}-kling`)) count++;
    if (completedPrompts.has(`${scene.sceneNum}-veo`)) count++;
    return acc + count;
  }, 0) || 0;

  const handleCopy = useCallback(async (key: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedStates(prev => ({ ...prev, [key]: true }));

    // 진행도 저장
    const newCompleted = new Set(completedPrompts).add(key);
    setCompletedPrompts(newCompleted);
    localStorage.setItem('academy_parse_progress', JSON.stringify([...newCompleted]));

    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [key]: false }));
    }, 2000);
  }, [completedPrompts]);

  const clearProgress = useCallback(() => {
    setCompletedPrompts(new Set());
    localStorage.removeItem('academy_parse_progress');
  }, []);

  const handleFileDrop = useCallback(async (files: FileList) => {
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.md') || file.type === 'text/markdown' || file.type === 'text/plain') {
        const text = await file.text();
        setMdInput(text);
      }
    }
  }, []);

  return {
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
  };
}
