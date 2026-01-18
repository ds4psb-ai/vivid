"use client";

import { useState, Fragment, useTransition } from "react";
import { X, Plus, Sparkles, Loader2, CheckCircle, Github, Upload, FileArchive, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";

interface MiniAppSubmitModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const CATEGORIES = [
    { id: "video", label: "영상", icon: "🎬" },
    { id: "image", label: "이미지", icon: "🖼️" },
    { id: "audio", label: "음악/오디오", icon: "🎵" },
    { id: "text", label: "텍스트", icon: "📝" },
    { id: "other", label: "기타", icon: "✨" },
];

const AI_TOOLS = [
    { id: "antigravity", label: "Google Antigravity" },
    { id: "ai-studio", label: "Google AI Studio Build" },
    { id: "cursor", label: "Cursor" },
    { id: "other", label: "기타" },
];

export function MiniAppSubmitModal({ isOpen, onClose }: MiniAppSubmitModalProps) {
    const [step, setStep] = useState<"form" | "success">("form");
    const [isPending, startTransition] = useTransition();
    const [submitError, setSubmitError] = useState<string | null>(null);

    // Form state
    const [appName, setAppName] = useState("");
    const [category, setCategory] = useState("");
    const [sourceType, setSourceType] = useState<"github" | "zip">("github");
    const [githubUrl, setGithubUrl] = useState("");
    const [zipFile, setZipFile] = useState<File | null>(null);
    const [zipFileUri, setZipFileUri] = useState<string | null>(null);
    const [isUploadingZip, setIsUploadingZip] = useState(false);
    const [description, setDescription] = useState("");
    const [aiTool, setAiTool] = useState("");

    const handleZipUpload = async (file: File) => {
        setZipFile(file);
        setIsUploadingZip(true);
        setSubmitError(null);
        try {
            const result = await api.uploadFile(file);
            setZipFileUri(result.file_uri);
        } catch (error) {
            console.error("ZIP upload failed:", error);
            setZipFile(null);
            setSubmitError("파일 업로드에 실패했습니다. 다시 시도해주세요.");
        } finally {
            setIsUploadingZip(false);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitError(null);

        startTransition(async () => {
            try {
                await api.submitMiniApp({
                    app_name: appName,
                    category,
                    source_type: sourceType,
                    github_url: sourceType === "github" ? githubUrl : undefined,
                    zip_file_uri: sourceType === "zip" ? zipFileUri || undefined : undefined,
                    description,
                    ai_tool: aiTool || undefined,
                });
                setStep("success");
            } catch (error) {
                console.error("MiniApp submission failed:", error);
                setSubmitError(error instanceof Error ? error.message : "제출에 실패했습니다. 다시 시도해주세요.");
            }
        });
    };

    const handleClose = () => {
        setStep("form");
        setAppName("");
        setCategory("");
        setGithubUrl("");
        setZipFile(null);
        setZipFileUri(null);
        setIsUploadingZip(false);
        setDescription("");
        setAiTool("");
        setSubmitError(null);
        onClose();
    };

    const isFormValid = appName && category && description &&
        (sourceType === "github" ? githubUrl : (zipFile && zipFileUri && !isUploadingZip)) && !isPending;

    return (
        <AnimatePresence>
            {isOpen && (
                <Fragment>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={handleClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-md z-50"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
                    >
                        <div className="card-premium relative w-full max-w-xl bg-black/40 backdrop-blur-2xl border border-white/10 rounded-3xl overflow-hidden pointer-events-auto">
                            {/* Ambient Glow */}
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[var(--layout-visual-lg)] h-[var(--layout-visual-md)] bg-violet-500/20 blur-[100px] rounded-full pointer-events-none" />

                            {/* Header */}
                            <div className="relative px-8 pt-8 pb-4 border-b border-white/5">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30 flex items-center justify-center">
                                            <Plus className="h-5 w-5 text-violet-400" />
                                        </div>
                                        <div>
                                            <h2 className="text-xl font-bold text-white tracking-tight">새 차원문 제안</h2>
                                            <p className="text-xs text-zinc-500">당신만의 차원을 열어주세요</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleClose}
                                        className="h-8 w-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors"
                                    >
                                        <X className="h-4 w-4 text-zinc-400" />
                                    </button>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="relative px-8 py-6 max-h-[var(--layout-modal-max-height)] overflow-y-auto">
                                {step === "form" ? (
                                    <form onSubmit={handleSubmit} className="space-y-6">
                                        {/* App Name */}
                                        <div className="group">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block group-focus-within:text-violet-400 transition-colors">
                                                앱 이름 (차원문 명칭)
                                            </label>
                                            <input
                                                type="text"
                                                value={appName}
                                                onChange={(e) => setAppName(e.target.value)}
                                                placeholder="예: AI 이미지 편집기"
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm font-light text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all"
                                            />
                                        </div>

                                        {/* Category */}
                                        <div className="group">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block group-focus-within:text-violet-400 transition-colors">
                                                카테고리 (차원 유형)
                                            </label>
                                            <div className="flex flex-wrap gap-2">
                                                {CATEGORIES.map((cat) => (
                                                    <button
                                                        key={cat.id}
                                                        type="button"
                                                        onClick={() => setCategory(cat.id)}
                                                        className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${category === cat.id
                                                            ? "bg-violet-500/20 border-violet-500/50 text-violet-300 border"
                                                            : "bg-white/5 border border-white/10 text-zinc-400 hover:bg-white/10 hover:text-white"
                                                            }`}
                                                    >
                                                        <span className="mr-1.5">{cat.icon}</span>
                                                        {cat.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Source Type Toggle */}
                                        <div className="group">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block">
                                                소스 타입
                                            </label>
                                            <div className="flex gap-2">
                                                <button
                                                    type="button"
                                                    onClick={() => setSourceType("github")}
                                                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ${sourceType === "github"
                                                        ? "bg-violet-500/20 border-violet-500/50 text-violet-300 border"
                                                        : "bg-white/5 border border-white/10 text-zinc-400 hover:bg-white/10"
                                                        }`}
                                                >
                                                    <Github className="h-4 w-4" />
                                                    GitHub URL
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setSourceType("zip")}
                                                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all ${sourceType === "zip"
                                                        ? "bg-violet-500/20 border-violet-500/50 text-violet-300 border"
                                                        : "bg-white/5 border border-white/10 text-zinc-400 hover:bg-white/10"
                                                        }`}
                                                >
                                                    <Upload className="h-4 w-4" />
                                                    ZIP 파일 업로드
                                                </button>
                                            </div>
                                        </div>

                                        {/* GitHub URL or Code Input */}
                                        {sourceType === "github" ? (
                                            <div className="group">
                                                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block group-focus-within:text-violet-400 transition-colors">
                                                    GitHub Repository URL
                                                </label>
                                                <input
                                                    type="url"
                                                    value={githubUrl}
                                                    onChange={(e) => setGithubUrl(e.target.value)}
                                                    placeholder="https://github.com/username/repo"
                                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm font-light text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all"
                                                />
                                            </div>
                                        ) : (
                                            <div className="group">
                                                <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block">
                                                    ZIP 파일 업로드
                                                </label>
                                                <label
                                                    className={`flex flex-col items-center justify-center w-full h-32 rounded-xl border-2 border-dashed cursor-pointer transition-all ${zipFile
                                                        ? "border-violet-500/50 bg-violet-500/10"
                                                        : "border-white/20 bg-white/5 hover:border-violet-500/30 hover:bg-white/[0.07]"
                                                        }`}
                                                >
                                                    <input
                                                        type="file"
                                                        accept=".zip"
                                                        onChange={(e) => {
                                                            const file = e.target.files?.[0];
                                                            if (file) handleZipUpload(file);
                                                        }}
                                                        className="hidden"
                                                    />
                                                    {zipFile ? (
                                                        <div className="flex items-center gap-3 text-violet-300">
                                                            {isUploadingZip ? (
                                                                <Loader2 className="h-8 w-8 animate-spin" />
                                                            ) : (
                                                                <FileArchive className="h-8 w-8" />
                                                            )}
                                                            <div className="text-left">
                                                                <p className="text-sm font-medium">{zipFile.name}</p>
                                                                <p className="text-xs text-zinc-500">
                                                                    {isUploadingZip ? "업로드 중..." : `${(zipFile.size / 1024).toFixed(1)} KB ✓`}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="flex flex-col items-center gap-2 text-zinc-500">
                                                            <Upload className="h-8 w-8" />
                                                            <p className="text-sm">클릭하여 ZIP 파일 선택</p>
                                                            <p className="text-xs text-zinc-600">바이브코딩 결과물을 압축하여 업로드</p>
                                                        </div>
                                                    )}
                                                </label>
                                            </div>
                                        )}

                                        {/* Description */}
                                        <div className="group">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block group-focus-within:text-violet-400 transition-colors">
                                                설명
                                            </label>
                                            <textarea
                                                value={description}
                                                onChange={(e) => setDescription(e.target.value)}
                                                placeholder="이 앱이 무엇을 하는지 간단히 설명해주세요..."
                                                rows={3}
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm font-light text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all resize-none"
                                            />
                                        </div>

                                        {/* AI Tool (Optional) */}
                                        <div className="group">
                                            <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2 block">
                                                사용한 AI 도구 <span className="text-zinc-600">(선택)</span>
                                            </label>
                                            <select
                                                value={aiTool}
                                                onChange={(e) => setAiTool(e.target.value)}
                                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm font-light text-white focus:outline-none focus:border-violet-400/50 focus:bg-white/[0.07] focus:ring-4 focus:ring-violet-400/5 transition-all appearance-none cursor-pointer"
                                            >
                                                <option value="" className="bg-[#0F0F1A]">선택하세요</option>
                                                {AI_TOOLS.map((tool) => (
                                                    <option key={tool.id} value={tool.id} className="bg-[#0F0F1A]">
                                                        {tool.label}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        {/* Error Message */}
                                        {submitError && (
                                            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-2 text-red-400 text-sm">
                                                <AlertTriangle className="h-4 w-4 shrink-0" />
                                                <span>{submitError}</span>
                                            </div>
                                        )}

                                        {/* Submit Button */}
                                        <button
                                            type="submit"
                                            disabled={!isFormValid}
                                            className="w-full relative group overflow-hidden rounded-xl py-4 text-base font-bold tracking-wide text-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 bg-gradient-to-r from-violet-600 to-purple-600 shadow-[0_0_30px_rgba(139,92,246,0.3)] hover:shadow-[0_0_50px_rgba(139,92,246,0.5)]"
                                        >
                                            <span className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                                            <span className="relative z-10 flex items-center justify-center gap-2">
                                                {isPending ? (
                                                    <>
                                                        <Loader2 className="h-5 w-5 animate-spin" />
                                                        제출 중...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Sparkles className="h-5 w-5" />
                                                        등록 신청하기
                                                    </>
                                                )}
                                            </span>
                                        </button>
                                    </form>
                                ) : (
                                    /* Success State */
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="py-8 text-center space-y-6"
                                    >
                                        <div className="relative inline-block">
                                            <div className="absolute inset-0 bg-emerald-500/30 blur-[40px] rounded-full" />
                                            <div className="relative h-20 w-20 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto">
                                                <CheckCircle className="h-10 w-10 text-emerald-400" />
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <h3 className="text-2xl font-bold text-white">등록 신청 완료!</h3>
                                            <p className="text-sm text-zinc-400 max-w-xs mx-auto">
                                                내부 개발팀에서 검토 후 크레딧 시스템과 디자인에 맞게 마이그레이션하여 배포해드립니다.
                                            </p>
                                        </div>

                                        <div className="pt-4 space-y-3">
                                            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
                                                <span className="h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
                                                심사중
                                            </div>
                                            <p className="text-xs text-zinc-500">
                                                평균 검토 기간: 1-3일
                                            </p>
                                        </div>

                                        <button
                                            onClick={handleClose}
                                            className="mt-6 px-8 py-3 rounded-xl bg-white/5 border border-white/10 text-white font-medium hover:bg-white/10 transition-colors"
                                        >
                                            닫기
                                        </button>
                                    </motion.div>
                                )}
                            </div>

                            {/* Footer Note */}
                            {step === "form" && (
                                <div className="relative px-8 py-4 border-t border-white/5 bg-white/[0.02]">
                                    <p className="text-xs text-zinc-500 text-center">
                                        제출된 미니앱은 내부 검토를 거쳐 크레딧 차감 로직과 디자인 가이드라인에 맞게 수정됩니다.
                                    </p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                </Fragment>
            )}
        </AnimatePresence>
    );
}
