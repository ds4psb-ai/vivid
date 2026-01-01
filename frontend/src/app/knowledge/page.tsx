"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
    BookOpen,
    Video,
    FileText,
    Sparkles,
    Layers,
    Search as SearchIcon,
    Filter,
    Grid,
    List,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import PageStatus from "@/components/PageStatus";
import LoginRequiredModal from "@/components/LoginRequiredModal";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, DerivedInsight, NotebookAssetItem, NotebookLibraryItem } from "@/lib/api";
import { useAdminAccess } from "@/hooks/useAdminAccess";
import { isNetworkError, normalizeApiError } from "@/lib/errors";
import { copyToClipboard } from "@/lib/clipboard";

type KnowledgeType = "notebook" | "analysis" | "guide" | "video" | "asset";

interface KnowledgeItem {
    id: string;
    title: string;
    type: KnowledgeType;
    description: string;
    tags: string[];
    updatedAt: string;
    meta?: {
        notebookId?: string;
        notebookRef?: string;
        guideScope?: string;
        clusterLabel?: string;
        sourceId?: string;
        guideType?: string;
        outputType?: string;
        assetId?: string;
        assetType?: string;
        assetRef?: string;
    };
}

const TYPE_ICONS: Record<KnowledgeType, React.ElementType> = {
    notebook: BookOpen,
    analysis: Sparkles,
    guide: FileText,
    video: Video,
    asset: Layers,
};

const isExternalLink = (value?: string) => Boolean(value && /^https?:\/\//i.test(value));
const copyText = (value?: string) => {
    if (!value) return;
    void copyToClipboard(value);
};

export default function KnowledgePage() {
    const { language, t } = useLanguage();
    const [search, setSearch] = useState("");
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
    const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
    const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [isOffline, setIsOffline] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [guideScopeFilter, setGuideScopeFilter] = useState("");
    const [outputTypeFilter, setOutputTypeFilter] = useState("");
    const [assetTypeFilter, setAssetTypeFilter] = useState("");
    const [seedDialogOpen, setSeedDialogOpen] = useState(false);
    const [seedContext, setSeedContext] = useState<KnowledgeItem | null>(null);
    const [seedError, setSeedError] = useState<string | null>(null);
    const [seedSuccess, setSeedSuccess] = useState<string | null>(null);
    const [seedSubmitting, setSeedSubmitting] = useState(false);
    const [seedForm, setSeedForm] = useState({
        slug: "",
        title: "",
        description: "",
        capsuleKey: "",
        capsuleVersion: "1.0.1",
        tags: "",
        isPublic: false,
    });
    const { isAdmin, session, isLoading: isAuthLoading } = useAdminAccess(false);
    const [loginModalOpen, setLoginModalOpen] = useState(false);

    const labels = useMemo(() => ({
        title: language === "ko" ? "지식 센터" : "Knowledge Center",
        subtitle: language === "ko" ? "노트북 라이브러리의 패턴, 가이드, 분석 탐색" : "Explore patterns, guides, and analysis from the Notebook Library",
        searchPlaceholder: language === "ko" ? "지식 베이스 검색..." : "Search knowledge base...",
        filter: language === "ko" ? "필터" : "Filter",
        filters: language === "ko" ? "필터" : "Filters",
        guideScope: language === "ko" ? "가이드 범위" : "Guide scope",
        outputType: language === "ko" ? "출력 유형" : "Output type",
        assetType: language === "ko" ? "자산 유형" : "Asset type",
        allScopes: language === "ko" ? "전체 범위" : "All scopes",
        allOutputs: language === "ko" ? "전체 출력" : "All outputs",
        allAssets: language === "ko" ? "전체 자산" : "All assets",
        resetFilters: language === "ko" ? "필터 초기화" : "Reset filters",
        noResults: language === "ko" ? "검색 결과 없음" : "No results found for",
        loading: language === "ko" ? "노트북 라이브러리 불러오는 중..." : "Loading notebook library...",
        loadErrorTitle: language === "ko" ? "데이터 로드 실패" : "Unable to load data",
        loadErrorDetail: language === "ko" ? "지식 데이터를 불러오지 못했습니다." : "Unable to load knowledge data.",
        adminHint: language === "ko" ? "관리자 전용 데이터입니다." : "Admin access required to view library data.",
        adminHintDetail:
            language === "ko"
                ? "관리자 권한이 있는 계정으로 로그인하세요."
                : "Sign in with an admin-enabled account.",
        adminAction: language === "ko" ? "관리자 로그인" : "Sign in as admin",
        gridView: language === "ko" ? "그리드 보기" : "Grid view",
        listView: language === "ko" ? "목록 보기" : "List view",
        viewMode: language === "ko" ? "보기 방식" : "View mode",
        detailTitle: language === "ko" ? "상세 정보" : "Details",
        detailType: language === "ko" ? "유형" : "Type",
        detailNotebookId: language === "ko" ? "노트북 ID" : "Notebook ID",
        detailNotebookRef: language === "ko" ? "노트북 링크" : "Notebook Ref",
        detailGuideScope: language === "ko" ? "가이드 범위" : "Guide scope",
        detailCluster: language === "ko" ? "클러스터" : "Cluster",
        detailSourceId: language === "ko" ? "소스 ID" : "Source ID",
        detailGuideType: language === "ko" ? "가이드 타입" : "Guide type",
        detailOutputType: language === "ko" ? "출력 타입" : "Output type",
        detailAssetId: language === "ko" ? "자산 ID" : "Asset ID",
        detailAssetType: language === "ko" ? "자산 유형" : "Asset type",
        detailAssetRef: language === "ko" ? "자산 링크" : "Asset ref",
        detailUpdated: language === "ko" ? "업데이트" : "Updated",
        close: language === "ko" ? "닫기" : "Close",
        copy: language === "ko" ? "복사" : "Copy",
        cancel: language === "ko" ? "취소" : "Cancel",
        error: language === "ko" ? "오류가 발생했습니다." : "Something went wrong.",
        seedTemplate: language === "ko" ? "템플릿 시드" : "Seed Template",
        seedTemplateTitle: language === "ko" ? "템플릿 시드" : "Seed Template",
        seedTemplateSubtitle:
            language === "ko"
                ? "노트북 기반 템플릿을 생성합니다"
                : "Create a template seeded from the notebook",
        seedNotebookId: language === "ko" ? "노트북 ID" : "Notebook ID",
        seedSlug: language === "ko" ? "템플릿 슬러그" : "Template slug",
        seedTitle: language === "ko" ? "템플릿 제목" : "Template title",
        seedDescription: language === "ko" ? "설명" : "Description",
        seedCapsuleKey: language === "ko" ? "캡슐 키" : "Capsule key",
        seedCapsuleVersion: language === "ko" ? "캡슐 버전" : "Capsule version",
        seedTags: language === "ko" ? "태그" : "Tags",
        seedPublic: language === "ko" ? "공개 템플릿" : "Public template",
        seedSubmit: language === "ko" ? "생성" : "Create",
        seedSubmitting: language === "ko" ? "생성 중..." : "Creating...",
        seedSuccess: language === "ko" ? "템플릿이 생성되었습니다." : "Template created.",
        seedError: language === "ko" ? "필수 항목을 확인하세요." : "Please fill the required fields.",
        defaultNotebookDesc: language === "ko" ? "노트북 라이브러리 항목" : "Notebook library entry",
        defaultAssetDesc: language === "ko" ? "노트북 라이브러리 자산" : "Notebook library asset",
        seedTitleSuffix: language === "ko" ? "템플릿" : "Template",
        seedDescriptionDefault: language === "ko" ? "노트북 기반 템플릿" : "Seeded template",
        typeNotebook: language === "ko" ? "노트북" : "Notebook",
        typeAnalysis: language === "ko" ? "분석" : "Analysis",
        typeGuide: language === "ko" ? "가이드" : "Guide",
        typeVideo: language === "ko" ? "영상" : "Video",
        typeAsset: language === "ko" ? "자산" : "Asset",
    }), [language]);

    const knowledgeTypeLabels: Record<KnowledgeType, string> = {
        notebook: labels.typeNotebook,
        analysis: labels.typeAnalysis,
        guide: labels.typeGuide,
        video: labels.typeVideo,
        asset: labels.typeAsset,
    };

    const guideScopeOptions = [
        { value: "auteur", label: language === "ko" ? "거장" : "auteur" },
        { value: "genre", label: language === "ko" ? "장르" : "genre" },
        { value: "format", label: language === "ko" ? "포맷" : "format" },
        { value: "creator", label: language === "ko" ? "크리에이터" : "creator" },
        { value: "mixed", label: language === "ko" ? "혼합" : "mixed" },
    ];

    const outputTypeOptions = [
        { value: "video_overview", label: language === "ko" ? "영상 요약" : "video_overview" },
        { value: "audio_overview", label: language === "ko" ? "오디오 요약" : "audio_overview" },
        { value: "mind_map", label: language === "ko" ? "마인드맵" : "mind_map" },
        { value: "report", label: language === "ko" ? "리포트" : "report" },
        { value: "data_table", label: language === "ko" ? "데이터 테이블" : "data_table" },
    ];

    const assetTypeOptions = [
        { value: "video", label: language === "ko" ? "영상" : "video" },
        { value: "image", label: language === "ko" ? "이미지" : "image" },
        { value: "doc", label: language === "ko" ? "문서" : "doc" },
        { value: "script", label: language === "ko" ? "스크립트" : "script" },
        { value: "still", label: language === "ko" ? "스틸" : "still" },
        { value: "scene", label: language === "ko" ? "씬" : "scene" },
        { value: "segment", label: language === "ko" ? "세그먼트" : "segment" },
        { value: "link", label: language === "ko" ? "링크" : "link" },
    ];

    const resolveOptionLabel = (value: string | undefined, options: Array<{ value: string; label: string }>) => {
        if (!value) return value;
        return options.find((option) => option.value === value)?.label || value;
    };

    const guideTypeLabel = (value?: string) => {
        if (!value) return value;
        switch (value) {
            case "summary":
                return t("guideSummary");
            case "homage":
                return t("guideHomage");
            case "variation":
                return t("guideVariation");
            case "template_fit":
                return t("guideTemplateFit");
            case "persona":
                return t("guidePersona");
            case "synapse":
                return t("guideSynapse");
            case "story":
                return t("guideStory");
            case "beat_sheet":
                return t("guideBeatSheet");
            case "storyboard":
                return t("guideStoryboard");
            case "study_guide":
                return t("guideStudyGuide");
            case "briefing_doc":
                return t("guideBriefingDoc");
            case "table":
                return t("guideTable");
            default:
                return value;
        }
    };

    const buildSeedTitle = (base: string) => `${base} ${labels.seedTitleSuffix}`.trim();

    const buildSeedDescription = (notebookId?: string) => {
        if (language === "ko") {
            return notebookId ? `노트북 ${notebookId} 기반 템플릿` : labels.seedDescriptionDefault;
        }
        return notebookId ? `Seeded from ${notebookId}` : labels.seedDescriptionDefault;
    };

    useEffect(() => {
        let active = true;
        if (isAuthLoading) {
            setIsLoading(true);
            return () => {
                active = false;
            };
        }
        if (!isAdmin) {
            setKnowledgeItems([]);
            setIsLoading(false);
            setLoadError("admin-only");
            setIsOffline(false);
            return () => {
                active = false;
            };
        }

        const loadKnowledge = async () => {
            setIsLoading(true);
            setLoadError(null);
            setIsOffline(false);

            const results = await Promise.allSettled([
                api.listNotebookLibrary({
                    limit: 80,
                    guide_scope: guideScopeFilter || undefined,
                }),
                api.listDerivedInsights({
                    limit: 80,
                    output_type: outputTypeFilter || undefined,
                }),
                api.listNotebookAssets({
                    limit: 80,
                    asset_type: assetTypeFilter || undefined,
                }),
            ]);

            if (!active) return;

            const items: KnowledgeItem[] = [];
            const errors: string[] = [];

            const formatDate = (value?: string | null) =>
                value ? value.split("T")[0] : "";

            const addNotebookItems = (entries: NotebookLibraryItem[]) => {
                entries.forEach((entry) => {
                    const tags = [
                        entry.guide_scope || "",
                        ...(entry.cluster_tags || []),
                    ].filter(Boolean);
                    items.push({
                        id: `notebook-${entry.notebook_id}`,
                        title: entry.title || entry.notebook_id,
                        type: "notebook",
                        description:
                            entry.cluster_label ||
                            entry.curator_notes ||
                            labels.defaultNotebookDesc,
                        tags,
                        updatedAt: formatDate(entry.updated_at || entry.created_at),
                        meta: {
                            notebookId: entry.notebook_id,
                            notebookRef: entry.notebook_ref,
                            guideScope: entry.guide_scope || undefined,
                            clusterLabel: entry.cluster_label || undefined,
                        },
                    });
                });
            };

            const addDerivedItems = (entries: DerivedInsight[]) => {
                entries.forEach((entry) => {
                    const guideType = entry.guide_type || "";
                    const outputType = entry.output_type || "";
                    const type: KnowledgeType =
                        outputType === "video_overview" || outputType === "audio_overview"
                            ? "video"
                            : guideType && guideType !== "summary"
                                ? "guide"
                                : "analysis";
                    const tags = [
                        outputType,
                        ...(entry.labels || []),
                        ...(entry.signature_motifs || []),
                    ].filter(Boolean);
                    items.push({
                        id: `derived-${entry.id}`,
                        title: entry.notebook_id || entry.source_id,
                        type,
                        description: entry.summary,
                        tags,
                        updatedAt: formatDate(entry.generated_at || entry.created_at),
                        meta: {
                            sourceId: entry.source_id,
                            notebookId: entry.notebook_id || undefined,
                            guideType: entry.guide_type || undefined,
                            outputType: entry.output_type,
                        },
                    });
                });
            };

            const addAssetItems = (entries: NotebookAssetItem[]) => {
                entries.forEach((entry) => {
                    const tags = [
                        entry.asset_type,
                        entry.notebook_id,
                        ...(entry.tags || []),
                    ].filter(Boolean);
                    items.push({
                        id: `asset-${entry.id}`,
                        title: entry.title || entry.asset_id,
                        type: "asset",
                        description:
                            entry.notes ||
                            entry.asset_ref ||
                            labels.defaultAssetDesc,
                        tags,
                        updatedAt: formatDate(entry.updated_at || entry.created_at),
                        meta: {
                            notebookId: entry.notebook_id,
                            assetId: entry.asset_id,
                            assetType: entry.asset_type,
                            assetRef: entry.asset_ref || undefined,
                        },
                    });
                });
            };

            results.forEach((result, index) => {
                if (result.status === "fulfilled") {
                    if (index === 0) addNotebookItems(result.value as NotebookLibraryItem[]);
                    if (index === 1) addDerivedItems(result.value as DerivedInsight[]);
                    if (index === 2) addAssetItems(result.value as NotebookAssetItem[]);
                } else {
                    errors.push(normalizeApiError(result.reason, labels.loadErrorDetail));
                }
            });

            setKnowledgeItems(items);
            if (errors.length) {
                setLoadError(errors[0]);
            }
            const offlineDetected = results.some(
                (result) => result.status === "rejected" && isNetworkError(result.reason)
            );
            setIsOffline(offlineDetected);
            setIsLoading(false);
        };

        void loadKnowledge();
        return () => {
            active = false;
        };
    }, [isAdmin, isAuthLoading, guideScopeFilter, outputTypeFilter, assetTypeFilter, labels]);

    const filteredKnowledge = useMemo(() => {
        if (!search.trim()) return knowledgeItems;
        const searchLower = search.toLowerCase();
        return knowledgeItems.filter(
            (k) =>
                k.title.toLowerCase().includes(searchLower) ||
                k.description.toLowerCase().includes(searchLower) ||
                k.tags.some((t) => t.toLowerCase().includes(searchLower))
        );
    }, [knowledgeItems, search]);

    const showAdminHint = (loadError || "").toLowerCase().includes("admin");
    const showLoginCta = showAdminHint && !session?.authenticated;

    const buildDefaultSlug = (value: string) => {
        const cleaned = value
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");
        if (!cleaned) {
            return `tmpl-seed-${Date.now()}`;
        }
        return cleaned.startsWith("tmpl-") ? cleaned : `tmpl-${cleaned}`;
    };

    const openSeedDialog = (item: KnowledgeItem) => {
        if (!session?.authenticated) {
            setLoginModalOpen(true);
            return;
        }
        const notebookId = item.meta?.notebookId || "";
        const base = notebookId || item.title || "template";
        setSeedForm({
            slug: buildDefaultSlug(base),
            title: buildSeedTitle(base),
            description: buildSeedDescription(notebookId),
            capsuleKey: "",
            capsuleVersion: "1.0.1",
            tags: item.tags.join(", "),
            isPublic: false,
        });
        setSeedContext(item);
        setSeedError(null);
        setSeedSuccess(null);
        setSeedDialogOpen(true);
        setSelectedItem(null);
    };

    const closeSeedDialog = () => {
        setSeedDialogOpen(false);
        setSeedContext(null);
        setSeedSubmitting(false);
    };

    const handleSeedSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!seedContext?.meta?.notebookId) {
            setSeedError(labels.seedError);
            return;
        }
        if (
            !seedForm.slug.trim() ||
            !seedForm.title.trim() ||
            !seedForm.capsuleKey.trim() ||
            !seedForm.capsuleVersion.trim()
        ) {
            setSeedError(labels.seedError);
            return;
        }
        setSeedError(null);
        setSeedSuccess(null);
        setSeedSubmitting(true);
        try {
            await api.seedTemplateFromEvidence({
                notebook_id: seedContext.meta.notebookId,
                slug: seedForm.slug.trim(),
                title: seedForm.title.trim(),
                description: seedForm.description.trim() || undefined,
                capsule_key: seedForm.capsuleKey.trim(),
                capsule_version: seedForm.capsuleVersion.trim(),
                tags: seedForm.tags
                    .split(",")
                    .map((tag) => tag.trim())
                    .filter(Boolean),
                is_public: seedForm.isPublic,
            });
            setSeedSuccess(labels.seedSuccess);
        } catch (err) {
            setSeedError(normalizeApiError(err, labels.error));
        } finally {
            setSeedSubmitting(false);
        }
    };

    return (
        <AppShell showTopBar={false}>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-5xl">
                    {/* Header */}
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 sm:mb-8"
                    >
                        <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                        <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
                    </motion.div>

                    {/* Search & Filter Bar */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-4 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-center sm:gap-4"
                    >
                        <div className="relative flex-1">
                            <SearchIcon
                                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--fg-muted)] sm:left-4"
                                aria-hidden="true"
                            />
                            <input
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder={labels.searchPlaceholder}
                                className="w-full rounded-lg border border-white/10 bg-slate-950/60 py-2 pl-9 pr-3 text-sm text-[var(--fg-0)] placeholder-[var(--fg-muted)] outline-none focus:border-[var(--accent)] sm:py-3 sm:pl-11 sm:pr-4"
                                aria-label={labels.searchPlaceholder}
                            />
                        </div>
                        <div className="flex gap-2 sm:gap-3">
                            <button
                                onClick={() => setShowFilters((prev) => !prev)}
                                className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10 sm:px-4 sm:py-3 sm:text-sm"
                                aria-label={labels.filter}
                                aria-expanded={showFilters}
                            >
                                <Filter className="h-3 w-3 sm:h-4 sm:w-4" aria-hidden="true" />
                                {labels.filter}
                            </button>
                            <div className="flex rounded-lg border border-white/10 bg-white/5" role="group" aria-label={labels.viewMode}>
                                <button
                                    onClick={() => setViewMode("grid")}
                                    className={`p-2 transition-colors sm:p-3 ${viewMode === "grid"
                                        ? "bg-white/10 text-[var(--fg-0)]"
                                        : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
                                        }`}
                                    aria-label={labels.gridView}
                                    aria-pressed={viewMode === "grid"}
                                >
                                    <Grid className="h-4 w-4" aria-hidden="true" />
                                </button>
                                <button
                                    onClick={() => setViewMode("list")}
                                    className={`p-2 transition-colors sm:p-3 ${viewMode === "list"
                                        ? "bg-white/10 text-[var(--fg-0)]"
                                        : "text-[var(--fg-muted)] hover:text-[var(--fg-0)]"
                                        }`}
                                    aria-label={labels.listView}
                                    aria-pressed={viewMode === "list"}
                                >
                                    <List className="h-4 w-4" aria-hidden="true" />
                                </button>
                            </div>
                        </div>
                    </motion.div>

                    {/* Filters Panel */}
                    <AnimatePresence>
                        {showFilters && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="mb-5 rounded-xl border border-white/10 bg-white/5 p-4 sm:p-5"
                                aria-label={labels.filters}
                            >
                                <div className="grid gap-4 sm:grid-cols-3">
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.guideScope}
                                        <select
                                            value={guideScopeFilter}
                                            onChange={(event) => setGuideScopeFilter(event.target.value)}
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                        >
                                            <option value="">{labels.allScopes}</option>
                                            {guideScopeOptions.map((option) => (
                                                <option key={option.value} value={option.value}>
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.outputType}
                                        <select
                                            value={outputTypeFilter}
                                            onChange={(event) => setOutputTypeFilter(event.target.value)}
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                        >
                                            <option value="">{labels.allOutputs}</option>
                                            {outputTypeOptions.map((option) => (
                                                <option key={option.value} value={option.value}>
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.assetType}
                                        <select
                                            value={assetTypeFilter}
                                            onChange={(event) => setAssetTypeFilter(event.target.value)}
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                        >
                                            <option value="">{labels.allAssets}</option>
                                            {assetTypeOptions.map((option) => (
                                                <option key={option.value} value={option.value}>
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                </div>
                                <div className="mt-4 flex justify-end">
                                    <button
                                        onClick={() => {
                                            setGuideScopeFilter("");
                                            setOutputTypeFilter("");
                                            setAssetTypeFilter("");
                                        }}
                                        className="rounded-lg border border-white/10 px-3 py-2 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10"
                                    >
                                        {labels.resetFilters}
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Knowledge Grid/List */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.15 }}
                        className={
                            viewMode === "grid"
                                ? "grid gap-3 sm:grid-cols-2 sm:gap-4 lg:grid-cols-3"
                                : "space-y-2 sm:space-y-3"
                        }
                        role="list"
                        aria-label={labels.title}
                    >
                        {isLoading && (
                            <PageStatus
                                variant="loading"
                                title={labels.loading}
                                className={viewMode === "grid" ? "col-span-full" : ""}
                            />
                        )}
                        {!isLoading && loadError && !showAdminHint && (
                            <PageStatus
                                variant="error"
                                title={labels.loadErrorTitle}
                                message={loadError}
                                isOffline={isOffline}
                                className={viewMode === "grid" ? "col-span-full" : ""}
                            />
                        )}
                        {showAdminHint && (
                            <PageStatus
                                variant="admin"
                                title={labels.adminHint}
                                message={labels.adminHintDetail}
                                action={showLoginCta ? { label: labels.adminAction, href: "/login" } : undefined}
                                className={viewMode === "grid" ? "col-span-full" : ""}
                            />
                        )}
                        {filteredKnowledge.map((item, index) => {
                            const Icon = TYPE_ICONS[item.type];
                            return (
                                <motion.article
                                    key={item.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.2 + index * 0.05 }}
                                    className={`group cursor-pointer rounded-lg border border-white/10 bg-slate-950/60 transition-all hover:border-white/20 sm:rounded-xl ${viewMode === "list" ? "flex items-center gap-3 p-3 sm:gap-4 sm:p-4" : "p-4 sm:p-5"
                                        }`}
                                    tabIndex={0}
                                    onClick={() => setSelectedItem(item)}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter" || event.key === " ") {
                                            event.preventDefault();
                                            setSelectedItem(item);
                                        }
                                    }}
                                    role="listitem"
                                    aria-label={`${labels.detailTitle}: ${item.title}`}
                                >
                                    <div
                                        className={`flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--accent)]/10 sm:h-10 sm:w-10 ${viewMode === "list" ? "flex-shrink-0" : "mb-3"
                                            }`}
                                    >
                                        <Icon className="h-4 w-4 text-[var(--accent)] sm:h-5 sm:w-5" aria-hidden="true" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-semibold text-[var(--fg-0)] group-hover:text-white transition-colors truncate">
                                            {item.title}
                                        </h3>
                                        <p className="mt-1 text-xs text-[var(--fg-muted)] line-clamp-2 sm:text-sm">
                                            {item.description}
                                        </p>
                                        <div className="mt-2 flex flex-wrap gap-1 sm:mt-3 sm:gap-2">
                                            {item.tags.map((tag) => (
                                                <span
                                                    key={tag}
                                                    className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-medium text-[var(--fg-muted)]"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    {viewMode === "list" && (
                                        <div className="text-xs text-[var(--fg-muted)] flex-shrink-0">
                                            {item.updatedAt}
                                        </div>
                                    )}
                                </motion.article>
                            );
                        })}
                    </motion.div>

                    {/* Empty State */}
                    {!isLoading && !loadError && filteredKnowledge.length === 0 && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-8">
                            <PageStatus
                                variant="empty"
                                title={labels.noResults}
                                message={search ? `"${search}"` : undefined}
                            />
                        </motion.div>
                    )}
                </div>
            </div>

            <AnimatePresence>
                {selectedItem && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 bg-black/60"
                            onClick={() => setSelectedItem(null)}
                            aria-hidden="true"
                        />
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className="fixed left-1/2 top-1/2 z-50 w-[min(560px,90vw)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-white/10 bg-[var(--bg-1)] p-6 shadow-2xl"
                            role="dialog"
                            aria-modal="true"
                            aria-label={labels.detailTitle}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div>
                                    <div className="text-xs text-[var(--fg-muted)]">{labels.detailTitle}</div>
                                    <h2 className="mt-1 text-lg font-semibold text-[var(--fg-0)]">
                                        {selectedItem.title}
                                    </h2>
                                </div>
                                <button
                                    onClick={() => setSelectedItem(null)}
                                    className="rounded-lg border border-white/10 px-3 py-1 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10"
                                >
                                    {labels.close}
                                </button>
                            </div>
                            <p className="mt-3 text-sm text-[var(--fg-muted)]">
                                {selectedItem.description}
                            </p>
                            <div className="mt-4 grid gap-3 text-xs text-[var(--fg-muted)] sm:grid-cols-2">
                                <div>
                                    <span className="text-[var(--fg-0)]">{labels.detailType}</span>
                                    <div>{knowledgeTypeLabels[selectedItem.type]}</div>
                                </div>
                                {selectedItem.meta?.notebookId && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailNotebookId}</span>
                                        <div>{selectedItem.meta.notebookId}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.notebookRef && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailNotebookRef}</span>
                                        <div className="mt-1 flex items-center gap-2">
                                            <div className="min-w-0 flex-1 truncate">
                                                {isExternalLink(selectedItem.meta.notebookRef) ? (
                                                    <a
                                                        href={selectedItem.meta.notebookRef}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="text-sky-400 hover:text-sky-300 hover:underline"
                                                    >
                                                        {selectedItem.meta.notebookRef}
                                                    </a>
                                                ) : (
                                                    <span>{selectedItem.meta.notebookRef}</span>
                                                )}
                                            </div>
                                            <button
                                                onClick={() => copyText(selectedItem.meta?.notebookRef)}
                                                className="rounded-md border border-white/10 px-2 py-1 text-[10px] text-[var(--fg-muted)] transition-colors hover:bg-white/10"
                                                aria-label={`${labels.copy}: ${labels.detailNotebookRef}`}
                                            >
                                                {labels.copy}
                                            </button>
                                        </div>
                                    </div>
                                )}
                                {selectedItem.meta?.guideScope && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailGuideScope}</span>
                                        <div>{resolveOptionLabel(selectedItem.meta.guideScope, guideScopeOptions)}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.clusterLabel && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailCluster}</span>
                                        <div>{selectedItem.meta.clusterLabel}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.sourceId && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailSourceId}</span>
                                        <div>{selectedItem.meta.sourceId}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.guideType && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailGuideType}</span>
                                        <div>{guideTypeLabel(selectedItem.meta.guideType)}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.outputType && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailOutputType}</span>
                                        <div>{resolveOptionLabel(selectedItem.meta.outputType, outputTypeOptions)}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.assetId && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailAssetId}</span>
                                        <div>{selectedItem.meta.assetId}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.assetType && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailAssetType}</span>
                                        <div>{resolveOptionLabel(selectedItem.meta.assetType, assetTypeOptions)}</div>
                                    </div>
                                )}
                                {selectedItem.meta?.assetRef && (
                                    <div>
                                        <span className="text-[var(--fg-0)]">{labels.detailAssetRef}</span>
                                        <div className="mt-1 flex items-center gap-2">
                                            <div className="min-w-0 flex-1 truncate">
                                                {isExternalLink(selectedItem.meta.assetRef) ? (
                                                    <a
                                                        href={selectedItem.meta.assetRef}
                                                        target="_blank"
                                                        rel="noreferrer"
                                                        className="text-sky-400 hover:text-sky-300 hover:underline"
                                                    >
                                                        {selectedItem.meta.assetRef}
                                                    </a>
                                                ) : (
                                                    <span>{selectedItem.meta.assetRef}</span>
                                                )}
                                            </div>
                                            <button
                                                onClick={() => copyText(selectedItem.meta?.assetRef)}
                                                className="rounded-md border border-white/10 px-2 py-1 text-[10px] text-[var(--fg-muted)] transition-colors hover:bg-white/10"
                                                aria-label={`${labels.copy}: ${labels.detailAssetRef}`}
                                            >
                                                {labels.copy}
                                            </button>
                                        </div>
                                    </div>
                                )}
                                <div>
                                    <span className="text-[var(--fg-0)]">{labels.detailUpdated}</span>
                                    <div>{selectedItem.updatedAt}</div>
                                </div>
                            </div>
                            <div className="mt-4 flex flex-wrap gap-1">
                                {selectedItem.tags.map((tag) => (
                                    <span
                                        key={tag}
                                        className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-medium text-[var(--fg-muted)]"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                            {selectedItem.type === "notebook" && (
                                <div className="mt-5 flex justify-end">
                                    <button
                                        onClick={() => openSeedDialog(selectedItem)}
                                        className="inline-flex items-center gap-2 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-xs font-semibold text-emerald-200 transition-colors hover:bg-emerald-500/20"
                                    >
                                        <Sparkles className="h-3 w-3" />
                                        {labels.seedTemplate}
                                    </button>
                                </div>
                            )}
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {seedDialogOpen && seedContext && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 bg-black/60"
                            onClick={closeSeedDialog}
                            aria-hidden="true"
                        />
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 20 }}
                            className="fixed left-1/2 top-1/2 z-50 w-[min(520px,92vw)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-white/10 bg-[var(--bg-1)] p-6 shadow-2xl"
                            role="dialog"
                            aria-modal="true"
                            aria-label={labels.seedTemplateTitle}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div>
                                    <div className="text-xs text-[var(--fg-muted)]">{labels.seedTemplateTitle}</div>
                                    <h2 className="mt-1 text-lg font-semibold text-[var(--fg-0)]">
                                        {labels.seedTemplateSubtitle}
                                    </h2>
                                </div>
                                <button
                                    onClick={closeSeedDialog}
                                    className="rounded-lg border border-white/10 px-3 py-1 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10"
                                >
                                    {labels.close}
                                </button>
                            </div>
                            <form onSubmit={handleSeedSubmit} className="mt-5 space-y-4 text-sm">
                                <div>
                                    <label className="text-xs text-[var(--fg-muted)]">{labels.seedNotebookId}</label>
                                    <div className="mt-1 rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-[var(--fg-0)]">
                                        {seedContext.meta?.notebookId || "-"}
                                    </div>
                                </div>
                                <div className="grid gap-3 sm:grid-cols-2">
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.seedSlug}
                                        <input
                                            value={seedForm.slug}
                                            onChange={(event) =>
                                                setSeedForm((prev) => ({ ...prev, slug: event.target.value }))
                                            }
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                            required
                                        />
                                    </label>
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.seedTitle}
                                        <input
                                            value={seedForm.title}
                                            onChange={(event) =>
                                                setSeedForm((prev) => ({ ...prev, title: event.target.value }))
                                            }
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                            required
                                        />
                                    </label>
                                </div>
                                <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                    {labels.seedDescription}
                                    <textarea
                                        value={seedForm.description}
                                        onChange={(event) =>
                                            setSeedForm((prev) => ({ ...prev, description: event.target.value }))
                                        }
                                        className="min-h-[72px] rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                    />
                                </label>
                                <div className="grid gap-3 sm:grid-cols-2">
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.seedCapsuleKey}
                                        <input
                                            value={seedForm.capsuleKey}
                                            onChange={(event) =>
                                                setSeedForm((prev) => ({ ...prev, capsuleKey: event.target.value }))
                                            }
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                            placeholder="auteur.bong-joon-ho"
                                            required
                                        />
                                    </label>
                                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                        {labels.seedCapsuleVersion}
                                        <input
                                            value={seedForm.capsuleVersion}
                                            onChange={(event) =>
                                                setSeedForm((prev) => ({
                                                    ...prev,
                                                    capsuleVersion: event.target.value,
                                                }))
                                            }
                                            className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                            required
                                        />
                                    </label>
                                </div>
                                <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                                    {labels.seedTags}
                                    <input
                                        value={seedForm.tags}
                                        onChange={(event) =>
                                            setSeedForm((prev) => ({ ...prev, tags: event.target.value }))
                                        }
                                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                                        placeholder="thriller, suspense"
                                    />
                                </label>
                                <label className="flex items-center gap-2 text-xs text-[var(--fg-muted)]">
                                    <input
                                        type="checkbox"
                                        checked={seedForm.isPublic}
                                        onChange={(event) =>
                                            setSeedForm((prev) => ({ ...prev, isPublic: event.target.checked }))
                                        }
                                        className="h-4 w-4 rounded border-white/20 bg-slate-950/60 text-[var(--accent)]"
                                    />
                                    {labels.seedPublic}
                                </label>
                                {seedError && (
                                    <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                                        {seedError}
                                    </div>
                                )}
                                {seedSuccess && (
                                    <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-200">
                                        {seedSuccess}
                                    </div>
                                )}
                                <div className="flex justify-end gap-2">
                                    <button
                                        type="button"
                                        onClick={closeSeedDialog}
                                        className="rounded-lg border border-white/10 px-3 py-2 text-xs text-[var(--fg-muted)] transition-colors hover:bg-white/10"
                                    >
                                        {labels.cancel}
                                    </button>
                                    <button
                                        type="submit"
                                        className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
                                        disabled={seedSubmitting}
                                    >
                                        {seedSubmitting ? labels.seedSubmitting : labels.seedSubmit}
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
            {/* Login Required Modal */}
            <LoginRequiredModal
                isOpen={loginModalOpen}
                onClose={() => setLoginModalOpen(false)}
                returnTo="/knowledge"
            />
        </AppShell>
    );
}
