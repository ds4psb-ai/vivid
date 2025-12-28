"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
    FolderOpen,
    Plus,
    Star,
    MoreVertical,
    Edit2,
    Share2,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import LoginRequiredModal from "@/components/LoginRequiredModal";
import { useLanguage } from "@/contexts/LanguageContext";
import { useSession } from "@/hooks/useSession";
import { api, Template } from "@/lib/api";
import PageStatus from "@/components/PageStatus";
import { isNetworkError, normalizeApiError } from "@/lib/errors";

interface Collection {
    id: string;
    name: string;
    description: string;
    itemCount: number;
    isStarred: boolean;
    updatedAt: string;
}

export default function CollectionsPage() {
    const { language } = useLanguage();
    const [templates, setTemplates] = useState<Template[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [isOffline, setIsOffline] = useState(false);
    const [loginModalOpen, setLoginModalOpen] = useState(false);
    const { session } = useSession(false);

    const labels = {
        title: language === "ko" ? "컬렉션" : "Collections",
        subtitle: language === "ko" ? "패턴과 참조 자료를 정리하세요" : "Organize your patterns and references",
        newCollection: language === "ko" ? "새 컬렉션" : "New Collection",
        createCollection: language === "ko" ? "컬렉션 만들기" : "Create Collection",
        items: language === "ko" ? "개 항목" : "items",
        starred: language === "ko" ? "즐겨찾기" : "Starred",
        moreOptions: language === "ko" ? "더보기" : "More options",
        editCollection: language === "ko" ? "컬렉션 편집" : "Edit collection",
        shareCollection: language === "ko" ? "컬렉션 공유" : "Share collection",
        loadError: language === "ko" ? "컬렉션 데이터를 불러오지 못했습니다." : "Unable to load collections.",
        emptyState: language === "ko" ? "아직 컬렉션이 없습니다." : "No collections yet.",
        tagCollection: language === "ko" ? "템플릿 태그 기반 컬렉션" : "Collections derived from template tags",
        updated: language === "ko" ? "업데이트" : "Updated",
        loading: language === "ko" ? "컬렉션 불러오는 중..." : "Loading collections...",
    };

    useEffect(() => {
        let active = true;
        const loadCollections = async () => {
            setIsLoading(true);
            setLoadError(null);
            try {
                const result = await api.listTemplates(true);
                if (!active) return;
                setIsOffline(false);
                setTemplates(result);
            } catch (err) {
                if (!active) return;
                setLoadError(normalizeApiError(err, labels.loadError));
                setIsOffline(isNetworkError(err));
            } finally {
                if (active) setIsLoading(false);
            }
        };
        void loadCollections();
        return () => {
            active = false;
        };
    }, [labels.loadError]);

    const collections = useMemo<Collection[]>(() => {
        const tagMap = new Map<string, { count: number; latest: string }>();
        const today = new Date().toISOString().slice(0, 10);
        templates.forEach((template) => {
            (template.tags || []).forEach((tag) => {
                const key = tag.trim();
                if (!key) return;
                const current = tagMap.get(key) || { count: 0, latest: today };
                tagMap.set(key, { count: current.count + 1, latest: current.latest });
            });
        });
        return Array.from(tagMap.entries())
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 12)
            .map(([tag, meta], index) => ({
                id: `tag-${tag}`,
                name: `#${tag}`,
                description: labels.tagCollection,
                itemCount: meta.count,
                isStarred: index === 0,
                updatedAt: meta.latest,
            }));
    }, [labels.tagCollection, templates]);

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-4xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 flex flex-col gap-4 sm:mb-8 sm:flex-row sm:items-center sm:justify-between"
                    >
                        <div>
                            <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                            <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                        </div>
                        <button
                            onClick={() => {
                                if (!session?.authenticated) {
                                    setLoginModalOpen(true);
                                    return;
                                }
                                // Handle new collection (TODO)
                            }}
                            className="flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-sky-500 to-sky-600 px-4 py-2 font-semibold text-white shadow-lg shadow-sky-500/25 transition-all hover:from-sky-400 hover:to-sky-500"
                            aria-label={labels.newCollection}
                        >
                            <Plus className="h-4 w-4" aria-hidden="true" />
                            {labels.newCollection}
                        </button>
                    </motion.div>

                    {/* Collections Grid */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="grid gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3"
                        role="list"
                        aria-label={labels.title}
                    >
                        {isLoading && (
                            <PageStatus
                                variant="loading"
                                title={labels.loading ?? "Loading..."}
                                className="sm:col-span-2 lg:col-span-3"
                            />
                        )}
                        {!isLoading && loadError && (
                            <PageStatus
                                variant="error"
                                title={labels.loadError}
                                message={loadError}
                                isOffline={isOffline}
                                className="sm:col-span-2 lg:col-span-3"
                            />
                        )}
                        {!isLoading && !loadError && collections.length === 0 && (
                            <PageStatus
                                variant="empty"
                                title={labels.emptyState}
                                className="sm:col-span-2 lg:col-span-3"
                            />
                        )}
                        {!isLoading && !loadError && collections.map((collection, index) => (
                            <motion.article
                                key={collection.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.15 + index * 0.05 }}
                                className="group relative cursor-pointer rounded-lg border border-white/10 bg-slate-950/60 p-4 transition-all hover:border-white/20 sm:rounded-xl sm:p-5"
                                role="listitem"
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between">
                                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--accent)]/10 sm:h-10 sm:w-10">
                                        <FolderOpen className="h-4 w-4 text-[var(--accent)] sm:h-5 sm:w-5" aria-hidden="true" />
                                    </div>
                                    <div className="flex items-center gap-1">
                                        {collection.isStarred && (
                                            <Star
                                                className="h-4 w-4 fill-amber-400 text-amber-400"
                                                aria-label={labels.starred}
                                            />
                                        )}
                                        <button
                                            className="rounded-lg p-1 text-[var(--fg-muted)] opacity-0 transition-all group-hover:opacity-100 hover:bg-white/10"
                                            aria-label={labels.moreOptions}
                                        >
                                            <MoreVertical className="h-4 w-4" aria-hidden="true" />
                                        </button>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="mt-3 sm:mt-4">
                                    <h3 className="font-semibold text-[var(--fg-0)] group-hover:text-white transition-colors">
                                        {collection.name}
                                    </h3>
                                    <p className="mt-1 text-xs text-[var(--fg-muted)] line-clamp-2 sm:text-sm">
                                        {collection.description}
                                    </p>
                                </div>

                                {/* Footer */}
                                <div className="mt-3 flex items-center justify-between text-[10px] text-[var(--fg-muted)] sm:mt-4 sm:text-xs">
                                    <span>{collection.itemCount} {labels.items}</span>
                                    <span>{collection.updatedAt}</span>
                                </div>

                                {/* Hover Actions */}
                                <div className="absolute bottom-4 right-4 flex gap-1 opacity-0 transition-all group-hover:opacity-100 sm:bottom-5 sm:right-5">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (!session?.authenticated) setLoginModalOpen(true);
                                        }}
                                        className="rounded-lg bg-white/5 p-2 text-[var(--fg-muted)] hover:bg-white/10 hover:text-[var(--fg-0)]"
                                        aria-label={labels.editCollection}
                                    >
                                        <Edit2 className="h-3 w-3" aria-hidden="true" />
                                    </button>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (!session?.authenticated) setLoginModalOpen(true);
                                        }}
                                        className="rounded-lg bg-white/5 p-2 text-[var(--fg-muted)] hover:bg-white/10 hover:text-[var(--fg-0)]"
                                        aria-label={labels.shareCollection}
                                    >
                                        <Share2 className="h-3 w-3" aria-hidden="true" />
                                    </button>
                                </div>
                            </motion.article>
                        ))}

                        {/* Empty State / Add New */}
                        <motion.button
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                            onClick={() => {
                                if (!session?.authenticated) {
                                    setLoginModalOpen(true);
                                    return;
                                }
                                // Handle new collection (TODO)
                            }}
                            className="flex min-h-[140px] flex-col items-center justify-center rounded-lg border border-dashed border-white/20 bg-white/5 transition-all hover:border-white/30 hover:bg-white/10 sm:min-h-[160px] sm:rounded-xl"
                            aria-label={labels.createCollection}
                        >
                            <Plus className="h-6 w-6 text-[var(--fg-muted)] sm:h-8 sm:w-8" aria-hidden="true" />
                            <span className="mt-2 text-xs text-[var(--fg-muted)] sm:text-sm">
                                {labels.createCollection}
                            </span>
                        </motion.button>
                    </motion.div>
                </div>
            </div>
            {/* Login Required Modal */}
            <LoginRequiredModal
                isOpen={loginModalOpen}
                onClose={() => setLoginModalOpen(false)}
                returnTo="/collections"
            />
        </AppShell>
    );
}
