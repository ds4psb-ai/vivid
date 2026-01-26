"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Layers, Wand2, FileCode, Loader2 } from "lucide-react";

// Import existing panels
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";
import PromptGeneratorPanel from "@/components/dimension/PromptGeneratorPanel";

/**
 * Story Engine Hub - Mega App for System Prompt Generation
 *
 * Consolidates:
 * - Story (Story Architect)
 * - Prompt (Prompt Alchemy / Generator)
 * - System Prompt Generator - NEW
 *
 * Workflow: Logic Vector → Story Structure → System Prompt for VEO/Kling
 */

interface TabConfig {
  value: string;
  label: string;
  labelEn: string;
  icon: React.ReactNode;
  description: string;
  isNew?: boolean;
}

const TAB_CONFIG: TabConfig[] = [
  {
    value: "story",
    label: "시나리오 생성기",
    labelEn: "Story Architect",
    icon: <Layers className="w-4 h-4" />,
    description: "DNA와 스타일을 결합한 시나리오 작성",
  },
  {
    value: "prompt",
    label: "프롬프트 연금술",
    labelEn: "Prompt Alchemy",
    icon: <Wand2 className="w-4 h-4" />,
    description: "AI 비디오 프롬프트 생성",
  },
  {
    value: "system-prompt",
    label: "시스템 프롬프트",
    labelEn: "System Prompt",
    icon: <FileCode className="w-4 h-4" />,
    description: "Logic Vector → VEO/Kling용 System Prompt 변환",
    isNew: true,
  },
];

/**
 * StoryEnginePage - Wrapper with Suspense boundary
 */
export default function StoryEnginePage() {
  return (
    <Suspense fallback={<StoryEngineLoading />}>
      <StoryEngineContent />
    </Suspense>
  );
}

/**
 * Loading state for StoryEnginePage
 */
function StoryEngineLoading() {
  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading Story Engine...</p>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * StoryEngineContent - Actual content with useSearchParams
 */
function StoryEngineContent() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState(tabParam || "story");

  // Sync with URL params
  useEffect(() => {
    if (tabParam && TAB_CONFIG.find((t) => t.value === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  return (
    <AppShell showTopBar={false}>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <BookOpen className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Story Engine</h1>
                <p className="text-sm text-muted-foreground">
                  스토리 구성 및 System Prompt 생성
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col"
        >
          <div className="flex-shrink-0 border-b bg-muted/50">
            <div className="container">
              <TabsList className="h-auto p-1 bg-transparent gap-1">
                {TAB_CONFIG.map((tab) => (
                  <TabsTrigger
                    key={tab.value}
                    value={tab.value}
                    className="flex items-center gap-2 px-4 py-2.5 data-[state=active]:bg-background"
                  >
                    {tab.icon}
                    <span className="hidden sm:inline">{tab.label}</span>
                    {tab.isNew && (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        NEW
                      </Badge>
                    )}
                  </TabsTrigger>
                ))}
              </TabsList>
            </div>
          </div>

          {/* Tab Contents */}
          <div className="flex-1 overflow-auto">
            {/* Story - Story Architect */}
            <TabsContent value="story" className="h-full m-0">
              <StoryArchitectPanel />
            </TabsContent>

            {/* Prompt - Prompt Alchemy */}
            <TabsContent value="prompt" className="h-full m-0">
              <PromptGeneratorPanel />
            </TabsContent>

            {/* System Prompt Generator */}
            <TabsContent value="system-prompt" className="h-full m-0 p-4">
              <SystemPromptPanel />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </AppShell>
  );
}

/**
 * System Prompt Panel
 * Converts Logic Vector + Story Structure → Platform-specific System Prompt
 */
function SystemPromptPanel() {
  const [logicVectorJson, setLogicVectorJson] = useState("");
  const [storyStructure, setStoryStructure] = useState("");
  const [targetPlatform, setTargetPlatform] = useState("veo");
  const [isLoading, setIsLoading] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!logicVectorJson) return;

    setIsLoading(true);
    try {
      let logicVector;
      try {
        logicVector = JSON.parse(logicVectorJson);
      } catch {
        alert("Logic Vector JSON 형식이 올바르지 않습니다.");
        return;
      }

      const response = await fetch("/api/story-engine/system-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          logic_vector: logicVector,
          story_structure: storyStructure ? JSON.parse(storyStructure) : undefined,
          target_platform: targetPlatform,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setSystemPrompt(data.system_prompt);
      }
    } catch (error) {
      console.error("System prompt generation failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCode className="w-5 h-5" />
            System Prompt Generator
          </CardTitle>
          <CardDescription>
            DNA Lab에서 추출한 Logic Vector를 VEO, Kling, Sora 등의 플랫폼에서
            사용할 수 있는 System Prompt로 변환합니다.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Logic Vector (JSON)
              <span className="text-muted-foreground ml-2">
                DNA Lab에서 복사
              </span>
            </label>
            <textarea
              placeholder={`{
  "auteur_id": "bong",
  "camera_grammar": { "dolly": 0.35, "handheld": 0.15 },
  "lighting_physics": { "key_light": "low_key" },
  ...
}`}
              value={logicVectorJson}
              onChange={(e) => setLogicVectorJson(e.target.value)}
              className="w-full h-40 px-3 py-2 border rounded-md bg-background font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Story Structure (선택, JSON)
            </label>
            <textarea
              placeholder={`{
  "hook": "A mysterious figure enters",
  "build": "Tension rises",
  "climax": "The revelation"
}`}
              value={storyStructure}
              onChange={(e) => setStoryStructure(e.target.value)}
              className="w-full h-24 px-3 py-2 border rounded-md bg-background font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">대상 플랫폼</label>
            <select
              value={targetPlatform}
              onChange={(e) => setTargetPlatform(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background"
            >
              <option value="veo">VEO 3.1</option>
              <option value="kling">Kling 2.6</option>
              <option value="sora">Sora 2 Pro</option>
              <option value="runway">Runway Gen-3</option>
            </select>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!logicVectorJson || isLoading}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {isLoading ? "생성 중..." : "System Prompt 생성"}
          </button>
        </CardContent>
      </Card>

      {systemPrompt && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              생성된 System Prompt
              <button
                onClick={() => navigator.clipboard.writeText(systemPrompt)}
                className="text-sm px-3 py-1 bg-muted rounded-md hover:bg-muted/80"
              >
                복사
              </button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="p-4 bg-muted rounded-md overflow-auto text-sm whitespace-pre-wrap">
              {systemPrompt}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
