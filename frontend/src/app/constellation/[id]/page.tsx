"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
    Sparkles, Plus, Star, Loader2, AlertCircle, X, ArrowLeft,
    Play, Trash2, Check, ChevronRight,
    Edit2, Save
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { api, Constellation, StarPoint, SingularityTemplate } from "@/lib/api";
import { getPresetConfig, getStatusConfig } from "@/components/constellation/constants";
import { useToast } from "@/components/Toast";

// =============================================================================
// STAR CARD
// =============================================================================

function StarCard({
    star,
    onExecute,
    onDelete,
    isExecuting,
}: {
    star: StarPoint;
    onExecute: () => void;
    onDelete: () => void;
    isExecuting: boolean;
}) {
    const status = getStatusConfig(star.status);

    return (
        <motion.div
            layout
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="group relative bg-gradient-to-b from-white/[0.04] to-transparent border border-white/10 rounded-2xl overflow-hidden
                       hover:border-cyan-500/30 transition-all"
        >
            {/* Scene Number Badge */}
            <div className="absolute top-3 left-3 z-10 w-8 h-8 rounded-full bg-black/60 backdrop-blur flex items-center justify-center text-sm font-bold text-white">
                {star.scene_number}
            </div>

            {/* Status Badge */}
            <div className={`absolute top-3 right-3 z-10 px-2 py-0.5 rounded-full ${status.bgColor} ${status.color} text-[10px] font-medium`}>
                {status.label}
            </div>

            {/* Thumbnail */}
            <div className="relative h-32 bg-gradient-to-br from-slate-900 to-slate-950">
                {star.thumbnail_url ? (
                    <img
                        src={star.thumbnail_url}
                        alt={star.singularity_name}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <Star className="w-8 h-8 text-slate-700" />
                    </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />

                {/* Execute Button (on hover) */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all">
                    <button
                        onClick={onExecute}
                        disabled={isExecuting}
                        className="w-10 h-10 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-xl hover:scale-110 transition-transform disabled:opacity-50"
                    >
                        {isExecuting ? (
                            <Loader2 className="w-5 h-5 text-black animate-spin" />
                        ) : (
                            <Play className="w-5 h-5 text-black ml-0.5" />
                        )}
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="p-4">
                <h4 className="text-sm font-semibold text-white mb-1 line-clamp-1">
                    {star.singularity_name}
                </h4>
                <p className="text-xs text-slate-500 line-clamp-1">
                    {Object.keys(star.overrides || {}).length > 0
                        ? `${Object.keys(star.overrides).length}개 커스텀 설정`
                        : "기본 설정"}
                </p>
            </div>

            {/* Delete Button */}
            <button
                onClick={onDelete}
                className="absolute bottom-3 right-3 p-1.5 rounded-lg bg-red-500/10 text-red-400 opacity-0 group-hover:opacity-100 hover:bg-red-500/20 transition-all"
            >
                <Trash2 className="w-3.5 h-3.5" />
            </button>
        </motion.div>
    );
}

// =============================================================================
// ADD STAR MODAL
// =============================================================================

function AddStarModal({
    isOpen,
    onClose,
    onAdd,
    isAdding,
}: {
    isOpen: boolean;
    onClose: () => void;
    onAdd: (singularityId: string) => void;
    isAdding: boolean;
}) {
    const [singularities, setSingularities] = useState<SingularityTemplate[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedId, setSelectedId] = useState<string | null>(null);

    useEffect(() => {
        if (!isOpen) return;

        const load = async () => {
            setLoading(true);
            try {
                const response = await api.listSingularityTemplates({ pageSize: 50 });
                setSingularities(response.items);
            } catch (err) {
                console.error("Failed to load singularities:", err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [isOpen]);

    if (!isOpen) return null;

    const filtered = singularities.filter(s =>
        s.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.tags.some(t => t.toLowerCase().includes(searchTerm.toLowerCase()))
    );

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
                className="w-full max-w-2xl bg-slate-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl max-h-[var(--layout-max-height-md)] flex flex-col"
            >
                {/* Header */}
                <div className="p-6 border-b border-white/10 flex-shrink-0">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-white">씬 추가하기</h2>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            <X className="w-5 h-5 text-slate-400" />
                        </button>
                    </div>

                    {/* Search */}
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="특이점 검색..."
                        className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
                    />
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12">
                            <Sparkles className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                            <p className="text-slate-500">특이점을 찾을 수 없습니다</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 gap-3">
                            {filtered.map((singularity) => (
                                <button
                                    key={singularity.id}
                                    onClick={() => setSelectedId(singularity.id)}
                                    className={`text-left p-4 rounded-xl border transition-all ${
                                        selectedId === singularity.id
                                            ? "bg-cyan-500/20 border-cyan-500/50"
                                            : "bg-white/5 border-white/10 hover:bg-white/10"
                                    }`}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className="w-12 h-12 rounded-lg bg-slate-800 flex-shrink-0 overflow-hidden">
                                            {singularity.thumbnail_url ? (
                                                <img
                                                    src={singularity.thumbnail_url}
                                                    alt={singularity.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center">
                                                    <Sparkles className="w-5 h-5 text-slate-600" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-semibold text-white line-clamp-1">
                                                {singularity.title}
                                            </h4>
                                            <div className="flex flex-wrap gap-1 mt-1">
                                                {singularity.tags.slice(0, 2).map(tag => (
                                                    <span key={tag} className="px-1.5 py-0.5 rounded bg-white/5 text-[10px] text-slate-500">
                                                        #{tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                        {selectedId === singularity.id && (
                                            <Check className="w-5 h-5 text-cyan-400 flex-shrink-0" />
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/10 flex-shrink-0">
                    <button
                        onClick={() => selectedId && onAdd(selectedId)}
                        disabled={!selectedId || isAdding}
                        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all"
                    >
                        {isAdding ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Plus className="w-5 h-5" />
                        )}
                        {isAdding ? "추가 중..." : "씬 추가"}
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function ConstellationDetailPage() {
    const router = useRouter();
    const params = useParams();
    const id = params?.id as string;
    const toast = useToast();

    const [constellation, setConstellation] = useState<Constellation | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showAddModal, setShowAddModal] = useState(false);
    const [isAdding, setIsAdding] = useState(false);
    const [executingScene, setExecutingScene] = useState<number | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editName, setEditName] = useState("");
    const [editDescription, setEditDescription] = useState("");

    const loadConstellation = useCallback(async () => {
        if (!id) return;
        setLoading(true);
        setError(null);
        try {
            const data = await api.getConstellation(id);
            setConstellation(data);
            setEditName(data.name);
            setEditDescription(data.description);
        } catch (err) {
            setError(err instanceof Error ? err.message : "별자리를 불러오는데 실패했습니다");
        } finally {
            setLoading(false);
        }
    }, [id]);

    useEffect(() => {
        loadConstellation();
    }, [loadConstellation]);

    const handleAddStar = async (singularityId: string) => {
        if (!constellation) return;
        setIsAdding(true);
        try {
            await api.addStar(constellation.id, { singularity_id: singularityId });
            setShowAddModal(false);
            await loadConstellation();
        } catch (err) {
            console.error("Failed to add star:", err);
            toast.error("씬 추가에 실패했습니다");
        } finally {
            setIsAdding(false);
        }
    };

    const handleDeleteStar = async (sceneNumber: number) => {
        if (!constellation) return;
        if (!confirm(`씬 ${sceneNumber}을(를) 삭제하시겠습니까?`)) return;

        try {
            await api.deleteStar(constellation.id, sceneNumber);
            await loadConstellation();
        } catch (err) {
            console.error("Failed to delete star:", err);
            toast.error("씬 삭제에 실패했습니다");
        }
    };

    const handleExecuteStar = async (sceneNumber: number) => {
        if (!constellation) return;
        setExecutingScene(sceneNumber);
        try {
            const result = await api.generateStar(constellation.id, sceneNumber);
            // Navigate to flow page with context
            router.push(result.redirect_url);
        } catch (err) {
            console.error("Failed to execute star:", err);
            toast.error("씬 실행에 실패했습니다");
            setExecutingScene(null);
        }
    };

    const handleSaveEdit = async () => {
        if (!constellation) return;
        try {
            await api.updateConstellation(constellation.id, {
                name: editName,
                description: editDescription,
            });
            setIsEditing(false);
            await loadConstellation();
        } catch (err) {
            console.error("Failed to update:", err);
            toast.error("수정에 실패했습니다");
        }
    };

    if (loading) {
        return (
            <AppShell>
                <div className="min-h-screen bg-black flex items-center justify-center">
                    <div className="text-center">
                        <Loader2 className="w-10 h-10 text-cyan-400 animate-spin mx-auto mb-4" />
                        <p className="text-slate-500">별자리를 불러오는 중...</p>
                    </div>
                </div>
            </AppShell>
        );
    }

    if (error || !constellation) {
        return (
            <AppShell>
                <div className="min-h-screen bg-black flex items-center justify-center">
                    <div className="text-center">
                        <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" />
                        <p className="text-red-400 mb-4">{error || "별자리를 찾을 수 없습니다"}</p>
                        <button
                            onClick={() => router.push("/constellation")}
                            className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg text-white hover:bg-white/20 mx-auto"
                        >
                            <ArrowLeft className="w-4 h-4" />
                            목록으로 돌아가기
                        </button>
                    </div>
                </div>
            </AppShell>
        );
    }

    const presetConfig = getPresetConfig(constellation.preset);
    const PresetIcon = presetConfig.Icon;
    const stars = constellation.star_points || [];

    return (
        <AppShell>
            <div className="min-h-screen bg-black">
                {/* Header */}
                <div className="sticky top-0 z-40 bg-black/80 backdrop-blur-xl border-b border-white/10">
                    <div className="max-w-6xl mx-auto px-6 py-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <button
                                    onClick={() => router.push("/constellation")}
                                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                                >
                                    <ArrowLeft className="w-5 h-5 text-white" />
                                </button>

                                {isEditing ? (
                                    <input
                                        value={editName}
                                        onChange={(e) => setEditName(e.target.value)}
                                        className="text-2xl font-bold bg-transparent text-white border-b border-cyan-500 focus:outline-none"
                                    />
                                ) : (
                                    <h1 className="text-2xl font-bold text-white">{constellation.name}</h1>
                                )}

                                <div className={`px-3 py-1 rounded-full bg-gradient-to-r ${presetConfig.color} text-xs font-medium text-white flex items-center gap-1`}>
                                    <PresetIcon className="w-3 h-3" />
                                    {presetConfig.label}
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                {isEditing ? (
                                    <>
                                        <button
                                            onClick={() => setIsEditing(false)}
                                            className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                                        >
                                            취소
                                        </button>
                                        <button
                                            onClick={handleSaveEdit}
                                            className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-white font-medium rounded-lg transition-colors"
                                        >
                                            <Save className="w-4 h-4" />
                                            저장
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        onClick={() => setIsEditing(true)}
                                        className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                        편집
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Description */}
                        {isEditing ? (
                            <textarea
                                value={editDescription}
                                onChange={(e) => setEditDescription(e.target.value)}
                                className="mt-3 w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-slate-400 text-sm focus:outline-none focus:border-cyan-500/50 resize-none"
                                rows={2}
                            />
                        ) : (
                            <p className="mt-2 text-slate-500 text-sm max-w-2xl">
                                {constellation.description || "설명이 없습니다"}
                            </p>
                        )}

                        {/* Progress */}
                        <div className="mt-4 flex items-center gap-4">
                            <div className="flex-1 max-w-xs">
                                <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                                    <span>진행률</span>
                                    <span>{constellation.progress_percent}%</span>
                                </div>
                                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${constellation.progress_percent}%` }}
                                        className={`h-full bg-gradient-to-r ${presetConfig.color} rounded-full`}
                                    />
                                </div>
                            </div>
                            <div className="text-sm text-slate-400">
                                <span className="text-white font-semibold">{constellation.completed_count}</span>
                                {" / "}
                                {constellation.target_scene_count} 씬 완료
                            </div>
                        </div>
                    </div>
                </div>

                {/* Content */}
                <div className="max-w-6xl mx-auto px-6 py-8">
                    {/* Timeline Header */}
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-semibold text-white">씬 타임라인</h2>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 text-white font-medium rounded-lg transition-all text-sm"
                        >
                            <Plus className="w-4 h-4" />
                            씬 추가
                        </button>
                    </div>

                    {/* Stars Grid */}
                    {stars.length === 0 ? (
                        <div className="text-center py-16 border border-dashed border-white/10 rounded-2xl">
                            <Sparkles className="w-12 h-12 text-slate-700 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-white mb-2">아직 씬이 없습니다</h3>
                            <p className="text-slate-500 mb-6">
                                특이점을 선택하여 첫 번째 씬을 추가하세요
                            </p>
                            <button
                                onClick={() => setShowAddModal(true)}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-white font-semibold rounded-xl transition-colors"
                            >
                                <Plus className="w-5 h-5" />
                                첫 씬 추가하기
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                            <AnimatePresence mode="popLayout">
                                {stars.map((star) => (
                                    <StarCard
                                        key={star.scene_number}
                                        star={star}
                                        onExecute={() => handleExecuteStar(star.scene_number)}
                                        onDelete={() => handleDeleteStar(star.scene_number)}
                                        isExecuting={executingScene === star.scene_number}
                                    />
                                ))}
                            </AnimatePresence>

                            {/* Add Card */}
                            <motion.button
                                onClick={() => setShowAddModal(true)}
                                className="h-full min-h-[var(--layout-min-height-lg)] border-2 border-dashed border-white/10 rounded-2xl flex flex-col items-center justify-center gap-2 text-slate-500 hover:border-cyan-500/30 hover:text-cyan-400 transition-all"
                            >
                                <Plus className="w-8 h-8" />
                                <span className="text-sm font-medium">씬 추가</span>
                            </motion.button>
                        </div>
                    )}

                    {/* Execute All Button */}
                    {stars.length > 0 && (
                        <div className="mt-8 flex justify-center">
                            <button
                                onClick={() => {
                                    const pendingStar = stars.find(s => s.status === "pending");
                                    if (pendingStar) {
                                        handleExecuteStar(pendingStar.scene_number);
                                    }
                                }}
                                className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white font-bold rounded-2xl transition-all shadow-lg shadow-violet-500/25"
                            >
                                <Play className="w-5 h-5" />
                                다음 씬 생성하기
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    )}
                </div>

                {/* Add Star Modal */}
                <AnimatePresence>
                    {showAddModal && (
                        <AddStarModal
                            isOpen={showAddModal}
                            onClose={() => setShowAddModal(false)}
                            onAdd={handleAddStar}
                            isAdding={isAdding}
                        />
                    )}
                </AnimatePresence>
            </div>
        </AppShell>
    );
}
