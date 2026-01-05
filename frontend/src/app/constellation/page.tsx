"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles, Plus, Star, Loader2, AlertCircle, RefreshCw, X, Play
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, Constellation } from "@/lib/api";
import { PRESET_CONFIG, getPresetConfig, ConstellationPreset } from "@/components/constellation/constants";
import { useToast } from "@/components/Toast";

// =============================================================================
// CONSTELLATION VISUAL - 별자리 비주얼
// =============================================================================

function ConstellationVisual() {
    return (
        <div className="relative w-full h-[400px] flex items-center justify-center overflow-hidden">
            {/* Star Field Background */}
            <div className="absolute inset-0">
                {[...Array(50)].map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0.2 }}
                        animate={{ opacity: [0.2, 0.8, 0.2] }}
                        transition={{
                            duration: 2 + Math.random() * 3,
                            repeat: Infinity,
                            delay: Math.random() * 2,
                        }}
                        className="absolute w-1 h-1 bg-white rounded-full"
                        style={{
                            left: `${Math.random() * 100}%`,
                            top: `${Math.random() * 100}%`,
                        }}
                    />
                ))}
            </div>

            {/* Constellation Lines */}
            <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.3 }}>
                <motion.path
                    d="M 200 150 L 400 100 L 600 180 L 500 280 L 300 250 Z"
                    stroke="url(#constellation-gradient)"
                    strokeWidth="1"
                    fill="none"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: 3, ease: "easeInOut" }}
                />
                <defs>
                    <linearGradient id="constellation-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#8b5cf6" />
                        <stop offset="50%" stopColor="#06b6d4" />
                        <stop offset="100%" stopColor="#f59e0b" />
                    </linearGradient>
                </defs>
            </svg>

            {/* Constellation Points */}
            {[
                { x: 200, y: 150 },
                { x: 400, y: 100 },
                { x: 600, y: 180 },
                { x: 500, y: 280 },
                { x: 300, y: 250 },
            ].map((pos, i) => (
                <motion.div
                    key={i}
                    className="absolute w-3 h-3 bg-white rounded-full shadow-[0_0_15px_rgba(255,255,255,0.8)]"
                    style={{ left: pos.x, top: pos.y }}
                    initial={{ scale: 0 }}
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: i * 0.3,
                    }}
                />
            ))}

            {/* Content Overlay */}
            <div className="relative z-10 text-center px-8">
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-4xl md:text-6xl font-black tracking-tight text-white mb-4"
                >
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-violet-400 to-amber-400">
                        별자리
                    </span>
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-slate-400 text-lg max-w-xl mx-auto"
                >
                    여러 특이점을 연결하여 멀티씬 프로젝트를 만드세요
                </motion.p>
            </div>
        </div>
    );
}

// =============================================================================
// PRESET FILTER
// =============================================================================

function PresetFilter({
    selectedPreset,
    onPresetChange,
}: {
    selectedPreset: ConstellationPreset | "";
    onPresetChange: (preset: ConstellationPreset | "") => void;
}) {
    return (
        <div className="flex flex-wrap items-center justify-center gap-2 mb-12">
            <button
                onClick={() => onPresetChange("")}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    !selectedPreset
                        ? "bg-white text-black shadow-lg"
                        : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                }`}
            >
                전체
            </button>
            {(Object.keys(PRESET_CONFIG) as ConstellationPreset[]).map((preset) => {
                const config = PRESET_CONFIG[preset];
                const Icon = config.Icon;
                return (
                    <button
                        key={preset}
                        onClick={() => onPresetChange(preset === selectedPreset ? "" : preset)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                            preset === selectedPreset
                                ? `bg-gradient-to-r ${config.color} text-white shadow-lg`
                                : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white"
                        }`}
                    >
                        <Icon className="w-4 h-4" />
                        {config.label}
                    </button>
                );
            })}
        </div>
    );
}

// =============================================================================
// CONSTELLATION CARD
// =============================================================================

function ConstellationCard({
    constellation,
    onClick,
    index,
}: {
    constellation: Constellation;
    onClick: () => void;
    index: number;
}) {
    const presetConfig = getPresetConfig(constellation.preset);
    const PresetIcon = presetConfig.Icon;
    const progressPercent = constellation.progress_percent || 0;

    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            whileHover={{ y: -8, scale: 1.02 }}
            onClick={onClick}
            className="group relative bg-gradient-to-b from-white/[0.04] to-transparent border border-white/10 rounded-3xl overflow-hidden cursor-pointer
                       hover:border-cyan-500/40 hover:shadow-[0_0_60px_rgba(6,182,212,0.15)] transition-all duration-500"
        >
            {/* Thumbnail / Star Pattern */}
            <div className="relative h-48 bg-gradient-to-br from-slate-900 to-slate-950 overflow-hidden">
                {/* Star pattern background */}
                <div className="absolute inset-0 opacity-30">
                    {[...Array(15)].map((_, i) => (
                        <div
                            key={i}
                            className="absolute w-1.5 h-1.5 bg-white rounded-full"
                            style={{
                                left: `${10 + (i * 23) % 80}%`,
                                top: `${15 + (i * 17) % 70}%`,
                            }}
                        />
                    ))}
                </div>

                {constellation.thumbnail_url ? (
                    <img
                        src={constellation.thumbnail_url}
                        alt={constellation.name}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                    />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Sparkles className="w-12 h-12 text-slate-700" />
                    </div>
                )}

                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent" />

                {/* Play Button */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <motion.div
                        whileHover={{ scale: 1.1 }}
                        className="w-14 h-14 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-2xl"
                    >
                        <Play className="w-6 h-6 text-black ml-1" />
                    </motion.div>
                </div>

                {/* Preset Badge */}
                <div className={`absolute top-4 right-4 px-3 py-1 rounded-full bg-gradient-to-r ${presetConfig.color} text-[10px] font-bold text-white tracking-wide flex items-center gap-1`}>
                    <PresetIcon className="w-3 h-3" />
                    {presetConfig.label}
                </div>

                {/* Scene Count */}
                <div className="absolute bottom-4 left-4 flex items-center gap-2">
                    <div className="px-2 py-1 rounded-lg bg-black/60 backdrop-blur text-white text-xs font-medium">
                        {constellation.scene_count || 0} / {constellation.target_scene_count} 씬
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="p-6">
                <h3 className="text-lg font-bold text-white mb-2 group-hover:text-cyan-300 transition-colors line-clamp-1">
                    {constellation.name}
                </h3>
                <p className="text-sm text-slate-500 mb-4 line-clamp-2 leading-relaxed">
                    {constellation.description || "별자리 설명이 없습니다"}
                </p>

                {/* Progress Bar */}
                <div className="mb-4">
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                        <span>진행률</span>
                        <span>{progressPercent}%</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercent}%` }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            className={`h-full bg-gradient-to-r ${presetConfig.color} rounded-full`}
                        />
                    </div>
                </div>

                {/* Stats */}
                <div className="flex items-center justify-between text-xs text-slate-600">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <Star className="w-3.5 h-3.5 text-cyan-500" />
                            {constellation.completed_count || 0} 완료
                        </span>
                    </div>
                    <span className="text-slate-500">{constellation.creator_name}</span>
                </div>
            </div>
        </motion.div>
    );
}

// =============================================================================
// CREATE MODAL
// =============================================================================

function CreateModal({
    isOpen,
    onClose,
    onCreate,
    isCreating,
    initialSingularityId,
}: {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (data: { name: string; description: string; preset: ConstellationPreset; target_scene_count: number }) => void;
    isCreating: boolean;
    initialSingularityId?: string | null;
}) {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [preset, setPreset] = useState<ConstellationPreset>("short_drama");
    const [targetCount, setTargetCount] = useState(5);

    if (!isOpen) return null;

    const handleSubmit = () => {
        if (!name.trim()) return;
        onCreate({
            name: name.trim(),
            description: description.trim(),
            preset,
            target_scene_count: targetCount,
        });
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-xl"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                className="w-full max-w-lg bg-slate-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl"
            >
                {/* Header */}
                <div className="p-6 border-b border-white/10">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">새 별자리 만들기</h2>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5 text-slate-400" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-5">
                    {/* Name */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">프로젝트 이름</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="예: 왕가위 스타일 숏폼"
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">설명</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="프로젝트에 대한 간단한 설명..."
                            rows={3}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 resize-none"
                        />
                    </div>

                    {/* Preset */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">프로젝트 타입</label>
                        <div className="grid grid-cols-3 gap-2">
                            {(Object.keys(PRESET_CONFIG) as ConstellationPreset[]).map((key) => {
                                const config = PRESET_CONFIG[key];
                                const Icon = config.Icon;
                                return (
                                    <button
                                        key={key}
                                        onClick={() => {
                                            setPreset(key);
                                            setTargetCount(config.defaultSceneCount);
                                        }}
                                        className={`flex flex-col items-center gap-1 p-3 rounded-xl border transition-all ${
                                            preset === key
                                                ? `bg-gradient-to-br ${config.color} border-transparent`
                                                : "bg-white/5 border-white/10 hover:bg-white/10"
                                        }`}
                                    >
                                        <Icon className="w-4 h-4 text-white" />
                                        <span className="text-xs text-white">{config.label}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Target Scene Count */}
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">
                            목표 씬 수: <span className="text-white font-bold">{targetCount}</span>
                        </label>
                        <input
                            type="range"
                            min={1}
                            max={50}
                            value={targetCount}
                            onChange={(e) => setTargetCount(parseInt(e.target.value))}
                            className="w-full accent-cyan-500"
                        />
                        <div className="flex justify-between text-xs text-slate-500 mt-1">
                            <span>1</span>
                            <span>50</span>
                        </div>
                    </div>

                    {/* Pre-selected Singularity Indicator */}
                    {initialSingularityId && (
                        <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                            <div className="flex items-center gap-2 text-cyan-400 text-sm">
                                <Sparkles className="w-4 h-4" />
                                <span className="font-medium">특이점이 첫 번째 씬으로 추가됩니다</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/10">
                    <button
                        onClick={handleSubmit}
                        disabled={!name.trim() || isCreating}
                        className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-2xl transition-all shadow-lg shadow-cyan-500/25"
                    >
                        {isCreating ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Plus className="w-5 h-5" />
                        )}
                        {isCreating ? "생성 중..." : "별자리 생성"}
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
}

// =============================================================================
// SEARCH PARAMS HANDLER (must be inside Suspense)
// =============================================================================

function SearchParamsHandler({
    onNewWithSingularity,
}: {
    onNewWithSingularity: (singularityId: string) => void;
}) {
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        const isNew = searchParams.get("new");
        const singularityId = searchParams.get("singularity");
        if (isNew === "true" && singularityId) {
            onNewWithSingularity(singularityId);
            router.replace("/constellation");
        }
    }, [searchParams, router, onNewWithSingularity]);

    return null;
}

// =============================================================================
// MAIN PAGE
// =============================================================================

function ConstellationPageContent() {
    const router = useRouter();
    const toast = useToast();
    const [constellations, setConstellations] = useState<Constellation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedPreset, setSelectedPreset] = useState<ConstellationPreset | "">("");
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const [initialSingularityId, setInitialSingularityId] = useState<string | null>(null);

    const handleNewWithSingularity = useCallback((singularityId: string) => {
        setInitialSingularityId(singularityId);
        setShowCreateModal(true);
    }, []);

    const loadConstellations = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.listConstellations({
                preset: selectedPreset || undefined,
                public_only: false, // Show user's own too
            });
            setConstellations(response.items);
        } catch (err) {
            setError(err instanceof Error ? err.message : "별자리를 불러오는데 실패했습니다");
        } finally {
            setLoading(false);
        }
    }, [selectedPreset]);

    useEffect(() => {
        loadConstellations();
    }, [loadConstellations]);

    const handleCreate = async (data: { name: string; description: string; preset: ConstellationPreset; target_scene_count: number }) => {
        setIsCreating(true);
        try {
            const created = await api.createConstellation({
                ...data,
                first_singularity_id: initialSingularityId || undefined,
            });
            setShowCreateModal(false);
            setInitialSingularityId(null); // Reset
            router.push(`/constellation/${created.id}`);
        } catch (err) {
            console.error("Failed to create constellation:", err);
            toast.error("별자리 생성에 실패했습니다");
        } finally {
            setIsCreating(false);
        }
    };

    return (
        <AppShell>
            <Suspense fallback={null}>
                <SearchParamsHandler onNewWithSingularity={handleNewWithSingularity} />
            </Suspense>
            <div className="min-h-screen bg-black">
                {/* Visual Header */}
                <ConstellationVisual />

                {/* Content */}
                <div className="max-w-7xl mx-auto px-6 pb-24">
                    {/* Actions */}
                    <div className="flex justify-center mb-8">
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-cyan-500/25"
                        >
                            <Plus className="w-5 h-5" />
                            새 별자리 만들기
                        </button>
                    </div>

                    {/* Preset Filter */}
                    <PresetFilter
                        selectedPreset={selectedPreset}
                        onPresetChange={setSelectedPreset}
                    />

                    {/* Loading */}
                    {loading && (
                        <div className="flex flex-col items-center justify-center py-20">
                            <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mb-4" />
                            <p className="text-slate-500">별자리를 불러오는 중...</p>
                        </div>
                    )}

                    {/* Error */}
                    {error && !loading && (
                        <div className="flex flex-col items-center justify-center py-20">
                            <AlertCircle className="w-10 h-10 text-red-400 mb-4" />
                            <p className="text-red-400 mb-4">{error}</p>
                            <button
                                onClick={loadConstellations}
                                className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-white hover:bg-white/20"
                            >
                                <RefreshCw className="w-4 h-4" />
                                다시 시도
                            </button>
                        </div>
                    )}

                    {/* Empty */}
                    {!loading && !error && constellations.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-20">
                            <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6">
                                <Sparkles className="w-8 h-8 text-slate-600" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">아직 별자리가 없습니다</h3>
                            <p className="text-slate-500 mb-4">
                                첫 번째 멀티씬 프로젝트를 시작해보세요
                            </p>
                            <button
                                onClick={() => setShowCreateModal(true)}
                                className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-white font-semibold rounded-xl transition-colors"
                            >
                                별자리 만들기
                            </button>
                        </div>
                    )}

                    {/* Grid */}
                    {!loading && !error && constellations.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {constellations.map((constellation, i) => (
                                <ConstellationCard
                                    key={constellation.id}
                                    constellation={constellation}
                                    onClick={() => router.push(`/constellation/${constellation.id}`)}
                                    index={i}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Create Modal */}
                <AnimatePresence>
                    {showCreateModal && (
                        <CreateModal
                            isOpen={showCreateModal}
                            onClose={() => {
                                setShowCreateModal(false);
                                setInitialSingularityId(null);
                            }}
                            onCreate={handleCreate}
                            isCreating={isCreating}
                            initialSingularityId={initialSingularityId}
                        />
                    )}
                </AnimatePresence>
            </div>
        </AppShell>
    );
}

export default function ConstellationPage() {
    return <ConstellationPageContent />;
}
