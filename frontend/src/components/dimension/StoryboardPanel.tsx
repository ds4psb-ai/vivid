"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import TeachingPanelLayout, { type ThemeColor } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

const CREDIT_COST = 10;
const THEME_COLOR: ThemeColor = "cyan";

interface StoryboardScene {
    scene_number: number;
    description: string;
    camera: string;
    duration: string;
    notes?: string;
    visual_prompt?: string;
    shot_type?: string;
    camera_movement?: string;
}

interface StoryboardResult {
    scenes: StoryboardScene[];
}

const SCENE_COUNTS = [3, 5, 7, 10, 15, 20];

const MODELS = [
    { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-2.5-pro", label: "Pro (고품질)" },
];

export default function StoryboardPanel() {
    const [script, setScript] = useState("");
    const [sceneCount, setSceneCount] = useState(5);
    const [language, setLanguage] = useState<"ko" | "en">("ko");
    const [model, setModel] = useState("gemini-3-flash-preview");

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<StoryboardResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);
    const [showCreditModal, setShowCreditModal] = useState(false);

    // BYOK and credits
    const { byokKey } = useBYOK();
    const creditCtx = useCreditContextOptional();

    const getErrorMessage = (err: unknown): string => {
        if (err instanceof Error) {
            const msg = err.message.toLowerCase();
            if (msg.includes("timeout")) return "요청 시간이 초과되었습니다. 다시 시도해주세요.";
            if (msg.includes("api key")) return "서비스 설정 오류입니다. 관리자에게 문의하세요.";
            if (msg.includes("network") || msg.includes("fetch")) return "네트워크 오류입니다. 인터넷 연결을 확인해주세요.";
            if (msg.includes("insufficient") || msg.includes("402")) return "크레딧이 부족합니다.";
            return err.message;
        }
        return "알 수 없는 오류가 발생했습니다.";
    };

    const handleGenerate = async () => {
        if (!script.trim()) {
            setError("스토리 컨셉을 입력해주세요");
            return;
        }

        // Credit check (only when not using BYOK)
        if (!byokKey && creditCtx && !creditCtx.hasEnoughCredits(CREDIT_COST)) {
            setShowCreditModal(true);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await api.post<{
                success: boolean;
                output: StoryboardResult;
                error?: string;
            }>("/api/dimension/2d/create", {
                concept: script,  // Map frontend 'script' to backend 'concept'
                scene_count: sceneCount,
                language,
                model,
            }, getBYOKHeaders(byokKey));

            if (response.success) {
                setResult(response.output);
                // Refresh credit balance
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(response.error || "생성 실패");
            }
        } catch (err) {
            const errorMsg = getErrorMessage(err);
            if (errorMsg.includes("크레딧")) {
                setShowCreditModal(true);
            } else {
                setError(errorMsg);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopy = async (text: string, field: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        } catch {
            setError("클립보드 복사에 실패했습니다.");
        }
    };

    const handleExportJson = () => {
        if (!result) return;
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "storyboard.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    const SidebarContent = (
        <>
            {/* Concept Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-cyan-400/80 transition-colors">스토리 개요 (Script)</label>
                <textarea
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    placeholder="영상의 전체적인 흐름이나 스크립트를 입력하세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-cyan-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
            </div>

            {/* Scene Count */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-cyan-400/80 transition-colors">장면 수</label>
                <div className="relative">
                    <select
                        value={sceneCount}
                        onChange={(e) => setSceneCount(Number(e.target.value))}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-cyan-400/5 transition-all appearance-none cursor-pointer hover:bg-white/[0.07]"
                    >
                        {SCENE_COUNTS.map((count) => (
                            <option key={count} value={count} className="bg-[#0F0F1A] text-white py-2">{count}개 장면</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30 group-focus-within:text-cyan-400/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Language */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-cyan-400/80 transition-colors">언어</label>
                <div className="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/10">
                    <button
                        onClick={() => setLanguage("ko")}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${language === "ko"
                            ? "bg-cyan-500 text-black shadow-sm"
                            : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                    >
                        KO
                    </button>
                    <button
                        onClick={() => setLanguage("en")}
                        className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${language === "en"
                            ? "bg-cyan-500 text-black shadow-sm"
                            : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                    >
                        EN
                    </button>
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-cyan-400/80 transition-colors">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-cyan-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-cyan-400/5 transition-all appearance-none cursor-pointer hover:bg-white/[0.07]"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-[#0F0F1A] text-white py-2">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30 group-focus-within:text-cyan-400/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate} // Changed handleCreate to handleGenerate
                disabled={isLoading || !script.trim()} // Changed concept to script
                className="w-full py-4 mt-6 bg-gradient-to-r from-cyan-500 to-sky-500 hover:from-cyan-400 hover:to-sky-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-black font-bold text-base rounded-xl shadow-[0_0_30px_rgba(6,182,212,0.3)] hover:shadow-[0_0_50px_rgba(6,182,212,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            <span>CREATING...</span>
                        </>
                    ) : (
                        <>
                            <span className="tracking-widest uppercase">Create Storyboard</span>
                            <div className="w-5 h-5 rounded-full bg-black/10 flex items-center justify-center">
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                            </div>
                        </>
                    )}
                </span>
            </button>

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs break-keep leading-relaxed animate-in fade-in slide-in-from-top-1">
                    {error}
                </div>
            )}
        </>
    );

    return (
        <>
            <TeachingPanelLayout
                title="스토리보드 생성기"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
            >
                {result ? (
                    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                                Generated Scenes ({result.scenes.length})
                            </h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={handleExportJson}
                                    className="px-3 py-1.5 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 text-white text-xs font-medium rounded-lg transition-all flex items-center gap-2"
                                >
                                    <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                    </svg>
                                    JSON Export
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 gap-4">
                            {result.scenes.map((scene, idx) => (
                                <div key={idx} className="group relative">
                                    <div className="absolute inset-0 bg-cyan-500/5 blur-xl rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                    <div className="relative h-full bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] p-6 hover:border-cyan-500/30 hover:bg-black/50 transition-all overflow-hidden flex flex-col">
                                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-cyan-500 to-sky-500 shadow-[0_0_20px_#06b6d4]"></div>

                                        <div className="flex items-center justify-between mb-4 pl-3">
                                            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                                                Scene {scene.scene_number}
                                            </h3>
                                            <span className="text-[10px] font-mono text-cyan-400/80 bg-cyan-500/10 px-2 py-1 rounded-md border border-cyan-500/20">
                                                {scene.duration || "5s"}
                                            </span>
                                        </div>

                                        <div className="space-y-4 pl-3 flex-1 flex flex-col">
                                            <div>
                                                <label className="text-[9px] font-bold text-zinc-600 uppercase tracking-wider mb-1 block">Description</label>
                                                <div className="flex items-start justify-between gap-4">
                                                    <p className="text-sm font-light leading-relaxed text-zinc-200">
                                                        {scene.description}
                                                    </p>
                                                    <button
                                                        onClick={() => handleCopy(scene.description, `scene-description-${idx}`)}
                                                        className={`flex-shrink-0 p-1.5 rounded-md transition-all opacity-0 group-hover:opacity-100 ${copiedField === `scene-description-${idx}`
                                                            ? "bg-green-500/10 text-green-400"
                                                            : "bg-white/5 text-zinc-500 hover:text-white hover:bg-white/10"
                                                            }`}
                                                        title="Copy Scene Description"
                                                    >
                                                        {copiedField === `scene-description-${idx}` ? (
                                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                            </svg>
                                                        ) : (
                                                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                            </svg>
                                                        )}
                                                    </button>
                                                </div>
                                            </div>

                                            {scene.visual_prompt && (
                                                <div>
                                                    <label className="text-[9px] font-bold text-zinc-600 uppercase tracking-wider mb-1 block group-hover:text-cyan-500/70 transition-colors">Visual Prompt</label>
                                                    <div className="p-3 bg-white/5 rounded-lg border border-white/5 text-xs font-mono text-zinc-400 leading-relaxed group-hover:border-cyan-500/20 transition-colors">
                                                        <div className="flex items-start justify-between gap-4">
                                                            <p>{scene.visual_prompt}</p>
                                                            <button
                                                                onClick={() => handleCopy(scene.visual_prompt!, `scene-visual-prompt-${idx}`)}
                                                                className={`flex-shrink-0 p-1.5 rounded-md transition-all opacity-0 group-hover:opacity-100 ${copiedField === `scene-visual-prompt-${idx}`
                                                                    ? "bg-green-500/10 text-green-400"
                                                                    : "bg-white/5 text-zinc-500 hover:text-white hover:bg-white/10"
                                                                    }`}
                                                                title="Copy Visual Prompt"
                                                            >
                                                                {copiedField === `scene-visual-prompt-${idx}` ? (
                                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                                    </svg>
                                                                ) : (
                                                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                                    </svg>
                                                                )}
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            <div className="pt-2 mt-auto border-t border-white/5 flex gap-2">
                                                <span className="px-2 py-1 bg-white/5 rounded text-[10px] text-zinc-500 font-mono border border-white/5">
                                                    {scene.shot_type || "Wide"}
                                                </span>
                                                <span className="px-2 py-1 bg-white/5 rounded text-[10px] text-zinc-500 font-mono border border-white/5">
                                                    {scene.camera_movement || "Static"}
                                                </span>
                                                {scene.notes && (
                                                    <span className="px-2 py-1 bg-blue-500/5 rounded text-[10px] text-blue-200 font-mono border border-blue-500/10">
                                                        {scene.notes}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-cyan-500/20 blur-[80px] rounded-full group-hover:bg-cyan-500/30 transition-colors duration-1000" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-cyan-500/20">
                                <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
                                <svg className="w-12 h-12 text-white/20 group-hover:text-cyan-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 tracking-tight">Ready to Create</h3>
                            <p className="text-sm text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                                스토리 아이디어를 입력하고<br />
                                <span className="text-cyan-500/80 font-medium">자동화된 씬 리스트</span>를 생성하세요.
                            </p>
                        </div>
                    </div>
                )}
            </TeachingPanelLayout>

            {/* Credit Modal */}
            <InsufficientCreditsModal
                isOpen={showCreditModal}
                onClose={() => setShowCreditModal(false)}
                requiredCredits={CREDIT_COST}
                currentBalance={creditCtx?.balance ?? 0}
                onRetry={handleGenerate}
            />
        </>
    );
}
