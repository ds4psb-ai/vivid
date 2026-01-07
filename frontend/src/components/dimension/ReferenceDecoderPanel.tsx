"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import TeachingPanelLayout, { type ThemeColor } from "./DimensionPanelLayout";
import { useBYOK, getBYOKHeaders } from "@/hooks/useBYOK";
import { useCreditContextOptional } from "@/contexts/CreditContext";
import InsufficientCreditsModal from "./InsufficientCreditsModal";

const CREDIT_COST = 8;
const THEME_COLOR: ThemeColor = "amber";

interface AnalysisResult {
    composition?: string;
    lighting?: string;
    color?: string;
    movement?: string;
    narrative?: string;
    recommendations?: string[];
}

const FOCUS_AREAS = [
    { value: "composition", label: "구도" },
    { value: "lighting", label: "조명" },
    { value: "color", label: "색감" },
    { value: "movement", label: "카메라" },
    { value: "narrative", label: "내러티브" },
    { value: "pacing", label: "페이싱" },
];

const MODELS = [
    { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
    { value: "gemini-2.5-pro", label: "Pro (고품질)" },
];

export default function ReferenceDecoderPanel() {
    const [description, setDescription] = useState("");
    const [focusAreas, setFocusAreas] = useState<string[]>(["composition", "lighting", "color", "movement"]);
    const [model, setModel] = useState("gemini-3-flash-preview");

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
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

    const toggleFocusArea = (area: string) => {
        setFocusAreas((prev) =>
            prev.includes(area) ? prev.filter((a) => a !== area) : [...prev, area]
        );
    };

    const handleAnalyze = async () => {
        if (!description.trim()) {
            setError("영상 설명을 입력해주세요");
            return;
        }
        if (focusAreas.length === 0) {
            setError("최소 하나의 분석 영역을 선택해주세요");
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
                output: AnalysisResult;
                error?: string;
            }>("/api/dimension/4d/analyze", {
                video_description: description,
                focus_areas: focusAreas,
                model,
            }, getBYOKHeaders(byokKey));

            if (response.success) {
                setResult(response.output);
                // Refresh credit balance
                if (!byokKey && creditCtx) {
                    void creditCtx.refresh();
                }
            } else {
                setError(response.error || "분석 실패");
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

    const handleExportJson = () => {
        if (!result) return;
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "analysis_result.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    const SidebarContent = (
        <>
            {/* Description Input */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-amber-400/80 transition-colors">레퍼런스 영상 설명</label>
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="분석하고 싶은 영상의 장면이나 특징을 상세히 설명하세요..."
                    className="w-full h-32 px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-amber-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-amber-400/5 transition-all resize-none text-sm font-light leading-relaxed"
                />
            </div>

            {/* Focus Areas */}
            <div className="space-y-2 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-amber-400/80 transition-colors">분석 집중 영역</label>
                <div className="flex flex-wrap gap-2">
                    {FOCUS_AREAS.map((area) => (
                        <button
                            key={area.value}
                            onClick={() => toggleFocusArea(area.value)}
                            className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-all ${focusAreas.includes(area.value)
                                ? "bg-amber-400/20 border-amber-400/50 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.1)]"
                                : "bg-white/5 border-white/5 text-zinc-400 hover:bg-white/10 hover:text-white"
                                }`}
                        >
                            {area.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Model Select */}
            <div className="space-y-2 pt-4 border-t border-white/5 mt-4 group">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest ml-1 group-focus-within:text-amber-400/80 transition-colors">AI 모델</label>
                <div className="relative">
                    <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-amber-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-amber-400/5 transition-all appearance-none cursor-pointer hover:bg-white/[0.07]"
                    >
                        {MODELS.map((m) => (
                            <option key={m.value} value={m.value} className="bg-[#0F0F1A] text-white py-2">{m.label}</option>
                        ))}
                    </select>
                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-white/30 group-focus-within:text-amber-400/50">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                </div>
            </div>

            {/* Analyze Button */}
            <button
                onClick={handleAnalyze}
                disabled={isLoading || !description.trim() || focusAreas.length === 0}
                className="w-full py-4 mt-6 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-black font-bold text-base rounded-xl shadow-[0_0_30px_rgba(245,158,11,0.3)] hover:shadow-[0_0_50px_rgba(245,158,11,0.5)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group relative overflow-hidden"
            >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                <span className="relative flex items-center gap-2">
                    {isLoading ? (
                        <>
                            <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            <span>ANALYZING...</span>
                        </>
                    ) : (
                        <>
                            <span className="tracking-widest uppercase">레퍼런스 분석</span>
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
                title="레퍼런스 해석기"
                sidebarContent={SidebarContent}
                isLoading={isLoading}
                themeColor={THEME_COLOR}
            >
                {result ? (
                    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                                Analysis Report
                            </h3>
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

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Analysis Sections */}
                            {Object.entries(result).map(([key, value]) => {
                                if (key === "recommendations") return null;
                                const title = FOCUS_AREAS.find(f => f.value === key)?.label || key;

                                return (
                                    <div key={key} className="group relative">
                                        <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-zinc-100 whitespace-pre-wrap group-hover:border-amber-500/30 group-hover:bg-black/50 transition-all relative overflow-hidden">
                                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-500 to-orange-500 shadow-[0_0_20px_#f59e0b]"></div>
                                            <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-3 border-b border-white/5 pb-2 group-hover:text-amber-400/80 transition-colors">
                                                {title}
                                            </h4>
                                            <p className="text-white/90 text-sm leading-relaxed whitespace-pre-wrap">
                                                {value as string}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Recommendations */}
                        {result.recommendations && result.recommendations.length > 0 && (
                            <div className="group relative">
                                <div className="p-8 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_8px_32px_rgba(0,0,0,0.3)] font-mono text-base leading-relaxed text-zinc-100 whitespace-pre-wrap group-hover:border-amber-500/30 group-hover:bg-black/50 transition-all relative overflow-hidden">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-amber-500 to-orange-500 shadow-[0_0_20px_#f59e0b]"></div>
                                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest mb-4 flex items-center gap-2 group-hover:text-amber-400/80 transition-colors">
                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                        </svg>
                                        Key Recommendations
                                    </h4>
                                    <ul className="space-y-3">
                                        {result.recommendations.map((rec, idx) => (
                                            <li key={idx} className="flex items-start gap-3 text-sm text-zinc-200">
                                                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-500/50 flex-shrink-0"></span>
                                                <span className="leading-relaxed">{rec}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 space-y-8 animate-in fade-in zoom-in-95 duration-700">
                        <div className="relative group">
                            <div className="absolute inset-0 bg-amber-500/20 blur-[80px] rounded-full group-hover:bg-amber-500/30 transition-colors duration-1000" />
                            <div className="w-32 h-32 rounded-[2rem] bg-white/[0.02] border border-white/10 flex items-center justify-center shadow-[0_0_60px_rgba(0,0,0,0.3)] backdrop-blur-md relative transform group-hover:scale-105 transition-all duration-500 group-hover:border-amber-500/20">
                                <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent rounded-[2rem]" />
                                <svg className="w-12 h-12 text-white/20 group-hover:text-amber-400 transition-colors duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-b from-white to-white/40 tracking-tight">Ready to Analyze</h3>
                            <p className="text-sm text-zinc-500 max-w-xs mx-auto font-light leading-relaxed">
                                영상의 특징을 설명하고<br />
                                <span className="text-amber-500/80 font-medium">AI 기반의 심층 시네마틱 분석</span>을 받아보세요.
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
                onRetry={handleAnalyze}
            />
        </>
    );
}
