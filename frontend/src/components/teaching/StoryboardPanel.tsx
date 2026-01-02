"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import TeachingPanelLayout from "./TeachingPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

const CREDIT_COST = 10;

interface StoryboardScene {
    scene_number: number;
    description: string;
    camera: string;
    duration: string;
    notes?: string;
}

interface StoryboardResult {
    scenes: StoryboardScene[];
}

const SCENE_COUNTS = [3, 5, 7, 10, 15, 20];

const MODELS = [
    { value: "gemini-2.5-flash", label: "Flash (빠름)" },
    { value: "gemini-2.5-pro", label: "Pro (고품질)" },
];

export default function StoryboardPanel() {
    const [concept, setConcept] = useState("");
    const [sceneCount, setSceneCount] = useState(5);
    const [language, setLanguage] = useState<"ko" | "en">("ko");
    const [model, setModel] = useState("gemini-2.5-flash");

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
        if (!concept.trim()) {
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
            }>("/api/teaching/storyboard/create", {
                concept,
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
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">스토리 컨셉</label>
                <textarea
                    value={concept}
                    onChange={(e) => setConcept(e.target.value)}
                    placeholder="스토리의 핵심 아이디어나 줄거리를 입력하세요..."
                    className="w-full h-32 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/20 focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all resize-none text-sm leading-relaxed"
                />
            </div>

            {/* Scene Count */}
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">씬 개수</label>
                <div className="grid grid-cols-3 gap-2">
                    {SCENE_COUNTS.map((count) => (
                        <button
                            key={count}
                            onClick={() => setSceneCount(count)}
                            className={`py-2 text-xs font-medium rounded-lg border transition-all ${sceneCount === count
                                ? "bg-amber-400/10 border-amber-400/50 text-amber-400"
                                : "bg-white/5 border-white/5 text-zinc-400 hover:bg-white/10 hover:text-white"
                                }`}
                        >
                            {count} Scenes
                        </button>
                    ))}
                </div>
            </div>

            {/* Language */}
            <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">언어</label>
                <div className="flex gap-1 p-1 bg-white/5 rounded-lg border border-white/10">
                    <button
                        onClick={() => setLanguage("ko")}
                        className={`flex-1 py-1 rounded-md text-xs font-medium transition-all ${language === "ko"
                            ? "bg-amber-400 text-black shadow-sm"
                            : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                    >
                        KO
                    </button>
                    <button
                        onClick={() => setLanguage("en")}
                        className={`flex-1 py-1 rounded-md text-xs font-medium transition-all ${language === "en"
                            ? "bg-amber-400 text-black shadow-sm"
                            : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                    >
                        EN
                    </button>
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-2 border-t border-white/5">
                <label className="text-xs font-medium text-zinc-400 uppercase tracking-wider">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-2 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/20 transition-all appearance-none"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value}>{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-white/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Generate Button */}
            <button
                onClick={handleGenerate}
                disabled={isLoading || !concept.trim()}
                className="w-full py-3 mt-4 bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-[#121212] font-bold rounded-lg shadow-lg shadow-amber-500/10 transition-all hover:shadow-amber-500/20 active:scale-[0.98] flex items-center justify-center gap-2"
            >
                {isLoading ? (
                    <span className="flex items-center gap-2">Generating...</span>
                ) : (
                    "스토리보드 생성"
                )}
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
            >
                {result ? (
                    <div className="max-w-5xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
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
                                <div key={idx} className="group bg-[#18181b] border border-white/10 rounded-xl overflow-hidden hover:border-white/20 transition-all shadow-sm">
                                    <div className="flex flex-col md:flex-row">
                                        {/* Number Badge */}
                                        <div className="w-full md:w-16 bg-white/5 border-b md:border-b-0 md:border-r border-white/5 flex items-center justify-center py-2 md:py-0">
                                            <span className="text-xl font-bold text-white/20 group-hover:text-amber-400/50 transition-colors">
                                                #{scene.scene_number}
                                            </span>
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 p-5 space-y-3">
                                            <div className="flex items-start justify-between gap-4">
                                                <p className="text-white text-sm leading-relaxed">{scene.description}</p>
                                                <button
                                                    onClick={() => handleCopy(scene.description, `scene-${idx}`)}
                                                    className={`flex-shrink-0 p-1.5 rounded-md transition-all opacity-0 group-hover:opacity-100 ${copiedField === `scene-${idx}`
                                                        ? "bg-green-500/10 text-green-400"
                                                        : "bg-white/5 text-zinc-500 hover:text-white hover:bg-white/10"
                                                        }`}
                                                    title="Copy Scene Description"
                                                >
                                                    {copiedField === `scene-${idx}` ? (
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

                                            <div className="flex flex-wrap gap-2 pt-2">
                                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/5 border border-white/5">
                                                    <svg className="w-3.5 h-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                    </svg>
                                                    <span className="text-xs text-zinc-300 font-medium">{scene.camera}</span>
                                                </div>
                                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white/5 border border-white/5">
                                                    <svg className="w-3.5 h-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                    <span className="text-xs text-amber-500/80 font-mono">{scene.duration}</span>
                                                </div>
                                                {scene.notes && (
                                                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/5 border border-blue-500/10">
                                                        <svg className="w-3.5 h-3.5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                        </svg>
                                                        <span className="text-xs text-blue-200">{scene.notes}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-6">
                        <div className="w-24 h-24 rounded-3xl bg-white/[0.03] border border-white/5 flex items-center justify-center shadow-2xl">
                            <svg className="w-10 h-10 opacity-20 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                        </div>
                        <div className="text-center space-y-2">
                            <h3 className="text-lg font-medium text-white/40">Canvas Empty</h3>
                            <p className="text-sm text-zinc-600 max-w-xs mx-auto">
                                스토리 컨셉을 입력하여 AI가 제안하는<br />스토리보드 씬을 확인해보세요.
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
            />
        </>
    );
}
