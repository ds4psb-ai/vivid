"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Database,
  BookOpen,
  Layers,
  Package,
  Sparkles,
  Workflow,
  Clapperboard,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import {
  PatternVersionHistory,
  TemplateProvenance,
  QuarantineSample,
} from "@/components/admin";
import RunTraceDashboard from "@/components/RunTraceDashboard";
import AppShell from "@/components/AppShell";
import {
  api,
  CapsuleRefreshResponse,
  CapsuleSpec,
  NotebookLibraryItem,
  Template,
  PipelineStatus,
  OpsActionLog,
  PatternPromotionResponse,
  SheetsSyncResponse,
} from "@/lib/api";
import PageStatus from "@/components/PageStatus";
import { useAdminAccess } from "@/hooks/useAdminAccess";
import { useLanguage } from "@/contexts/LanguageContext";
import { isNetworkError, normalizeApiError } from "@/lib/errors";
import { localizeTemplate } from "@/lib/templateLocalization";

type StageCard = {
  key: string;
  title: string;
  icon: React.ElementType;
  total: number;
  latest?: string | null;
  meta?: string;
};

const formatLatest = (value?: string | null) => value || "-";

export default function PipelinePage() {
  const { language } = useLanguage();
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notebooks, setNotebooks] = useState<NotebookLibraryItem[]>([]);
  const [capsules, setCapsules] = useState<CapsuleSpec[]>([]);
  const [recentTemplates, setRecentTemplates] = useState<Template[]>([]);
  const [showMissingOnly, setShowMissingOnly] = useState(false);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  const [seedSubmitting, setSeedSubmitting] = useState(false);
  const [seedError, setSeedError] = useState<string | null>(null);
  const [seedSuccess, setSeedSuccess] = useState<string | null>(null);
  const [showPublishConfirm, setShowPublishConfirm] = useState(false);
  const [promoteSubmitting, setPromoteSubmitting] = useState(false);
  const [promoteError, setPromoteError] = useState<string | null>(null);
  const [promoteResult, setPromoteResult] = useState<PatternPromotionResponse | null>(null);
  const [refreshSubmitting, setRefreshSubmitting] = useState(false);
  const [refreshError, setRefreshError] = useState<string | null>(null);
  const [refreshResult, setRefreshResult] = useState<CapsuleRefreshResponse | null>(null);
  const [syncSubmitting, setSyncSubmitting] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<SheetsSyncResponse | null>(null);
  const [opsLogs, setOpsLogs] = useState<OpsActionLog[]>([]);
  const [opsLogError, setOpsLogError] = useState<string | null>(null);
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({});
  const [isOffline, setIsOffline] = useState(false);
  const [seedForm, setSeedForm] = useState({
    notebookId: "",
    slug: "",
    title: "",
    description: "",
    capsuleKey: "",
    capsuleVersion: "1.0.1",
    tags: "",
    isPublic: false,
  });
  const [promoteForm, setPromoteForm] = useState({
    note: "",
    minConfidence: 0.6,
    minSources: 2,
    minFitnessScore: 0.1,
    deriveFromEvidence: false,
    dryRun: false,
  });
  const [refreshForm, setRefreshForm] = useState({
    patternVersion: "",
    dryRun: false,
    onlyActive: true,
  });

  const loadErrorFallback =
    language === "ko" ? "파이프라인 상태를 불러오지 못했습니다." : "Unable to load pipeline status.";
  const templatesErrorFallback =
    language === "ko" ? "템플릿을 불러오지 못했습니다." : "Unable to load templates.";
  const opsErrorFallback =
    language === "ko" ? "운영 로그를 불러오지 못했습니다." : "Unable to load ops logs.";
  const { isAdmin, session, isLoading: isAuthLoading } = useAdminAccess();
  const localizedTemplates = useMemo(
    () => recentTemplates.map((template) => localizeTemplate(template, language)),
    [recentTemplates, language]
  );

  useEffect(() => {
    let active = true;
    if (isAuthLoading) {
      setIsLoading(true);
      return () => {
        active = false;
      };
    }
    if (!isAdmin) {
      setIsLoading(false);
      setStatus(null);
      setLoadError("admin-only");
      setIsOffline(false);
      return () => {
        active = false;
      };
    }
    const loadStatus = async () => {
      setIsLoading(true);
      setLoadError(null);
      setIsOffline(false);
      const [statusResult, notebooksResult, capsulesResult, templatesResult, logsResult] =
        await Promise.allSettled([
          api.getPipelineStatus(),
          api.listNotebookLibrary({ limit: 80 }),
          api.listCapsules(),
          api.listTemplates(true),
          api.listOpsActions(8),
        ]);

      if (!active) return;

      if (statusResult.status === "fulfilled") {
        setStatus(statusResult.value);
      } else {
        setLoadError(normalizeApiError(statusResult.reason, loadErrorFallback));
      }
      const offlineDetected = [
        statusResult,
        notebooksResult,
        capsulesResult,
        templatesResult,
        logsResult,
      ].some((result) => result.status === "rejected" && isNetworkError(result.reason));
      setIsOffline(offlineDetected);

      if (notebooksResult.status === "fulfilled") {
        setNotebooks(notebooksResult.value);
      } else {
        setNotebooks([]);
      }

      if (capsulesResult.status === "fulfilled") {
        setCapsules(capsulesResult.value);
      } else {
        setCapsules([]);
      }

      if (logsResult.status === "fulfilled") {
        setOpsLogs(logsResult.value);
        setOpsLogError(null);
      } else {
        setOpsLogs([]);
        setOpsLogError(normalizeApiError(logsResult.reason, opsErrorFallback));
      }

      if (templatesResult.status === "fulfilled") {
        setRecentTemplates(templatesResult.value.slice(0, 6));
        setTemplatesError(null);
      } else {
        setRecentTemplates([]);
        setTemplatesError(normalizeApiError(templatesResult.reason, templatesErrorFallback));
      }

      if (active) setIsLoading(false);
    };
    void loadStatus();
    return () => {
      active = false;
    };
  }, [isAdmin, isAuthLoading, language, loadErrorFallback, opsErrorFallback, templatesErrorFallback]);

  const labels = {
    title: language === "ko" ? "파이프라인 상태" : "Pipeline Status",
    subtitle:
      language === "ko"
        ? "거장 데이터화 → 템플릿 승격까지 진행 상태를 한 눈에 점검합니다."
        : "Audit the end-to-end pipeline from dataization to template promotion.",
    stageRawAssets: language === "ko" ? "원본 자산" : "Raw Assets",
    stageVideoSegments: language === "ko" ? "영상 세그먼트" : "Video Segments",
    stageNotebookLibrary: language === "ko" ? "노트북 라이브러리" : "Notebook Library",
    stageEvidenceRecords: language === "ko" ? "근거 레코드" : "Evidence Records",
    evidenceMissingSourcePack:
      language === "ko" ? "source_pack 누락" : "Missing source_pack_id",
    evidenceOpsOnly: language === "ko" ? "ops_only" : "ops_only",
    stagePatternCandidates: language === "ko" ? "패턴 후보" : "Pattern Candidates",
    stagePatternLibrary: language === "ko" ? "패턴 라이브러리" : "Pattern Library",
    stageCapsuleSpecs: language === "ko" ? "캡슐 스펙" : "Capsule Specs",
    stageTemplates: language === "ko" ? "템플릿" : "Templates",
    stageCapsuleRuns: language === "ko" ? "캡슐 실행" : "Capsule Runs",
    stageGenerationRuns: language === "ko" ? "생성 실행" : "Generation Runs",
    stageAssets: language === "ko" ? "자산" : "Assets",
    patternStatusTitle: language === "ko" ? "패턴 상태" : "Pattern Status",
    runStatusTitle: language === "ko" ? "실행 상태" : "Run Status",
    loadError: language === "ko" ? "파이프라인 상태를 불러오지 못했습니다." : "Unable to load pipeline status.",
    templatesLoadError: language === "ko" ? "템플릿을 불러오지 못했습니다." : "Unable to load templates.",
    opsRunsError: language === "ko" ? "운영 로그를 불러오지 못했습니다." : "Unable to load ops logs.",
    adminOnly:
      language === "ko"
        ? "관리자 전용 데이터입니다."
        : "Admin access required to view pipeline data.",
    adminOnlyAction: language === "ko" ? "관리자 로그인" : "Sign in as admin",
    adminOnlyHint:
      language === "ko"
        ? "관리자 권한이 있는 계정으로 로그인하세요."
        : "Sign in with an admin-enabled account.",
    loading: language === "ko" ? "파이프라인 상태 불러오는 중..." : "Loading pipeline status...",
    latest: language === "ko" ? "최근 업데이트" : "Latest",
    patternVersion: language === "ko" ? "패턴 버전" : "Pattern version",
    templatesPublic: language === "ko" ? "공개 템플릿" : "Public templates",
    templatesMissing: language === "ko" ? "근거 누락" : "Missing provenance",
    restricted: language === "ko" ? "권리 제한" : "Restricted",
    quarantine: language === "ko" ? "쿼런틴" : "Quarantine",
    quarantineEmpty:
      language === "ko"
        ? "쿼런틴에 저장된 항목이 없습니다."
        : "No quarantine rows found.",
    quarantineSample: language === "ko" ? "쿼런틴 샘플" : "Quarantine Sample",
    quarantineRow: language === "ko" ? "원본 행" : "Row payload",
    seedTitle: language === "ko" ? "템플릿 시드" : "Template Seeding",
    seedSubtitle:
      language === "ko"
        ? "NotebookLM 증거를 기반으로 템플릿을 생성합니다."
        : "Create templates seeded from notebook evidence.",
    seedNotebook: language === "ko" ? "노트북 선택" : "Notebook",
    seedCapsule: language === "ko" ? "캡슐 선택" : "Capsule",
    seedSlug: language === "ko" ? "템플릿 슬러그" : "Template slug",
    seedName: language === "ko" ? "템플릿 제목" : "Template title",
    seedDescription: language === "ko" ? "설명" : "Description",
    seedTags: language === "ko" ? "태그" : "Tags",
    seedCapsuleVersion: language === "ko" ? "캡슐 버전" : "Capsule version",
    seedPublic: language === "ko" ? "공개 템플릿" : "Public template",
    seedSubmit: language === "ko" ? "템플릿 생성" : "Create template",
    seedSubmitting: language === "ko" ? "생성 중..." : "Creating...",
    seedNoNotebook: language === "ko" ? "노트북이 없습니다." : "No notebooks available.",
    seedNoCapsule: language === "ko" ? "캡슐이 없습니다." : "No capsules available.",
    seedRequired:
      language === "ko"
        ? "필수 항목을 입력하세요."
        : "Please fill the required fields.",
    seedFailed: language === "ko" ? "템플릿 생성에 실패했습니다." : "Failed to create template.",
    seedSuccess: language === "ko" ? "템플릿이 생성되었습니다." : "Template created.",
    patternHistory: language === "ko" ? "패턴 버전 히스토리" : "Pattern Version History",
    noPatternHistory: language === "ko" ? "버전 히스토리가 없습니다." : "No version history.",
    syncTitle: language === "ko" ? "Sheets 동기화" : "Sheets Sync",
    syncSubtitle:
      language === "ko"
        ? "NotebookLM/Opal 결과를 Sheets Bus에서 DB로 승격합니다."
        : "Promote Sheets Bus outputs into DB SoR.",
    syncSubmit: language === "ko" ? "Sheets 동기화 실행" : "Run Sheets Sync",
    syncSubmitting: language === "ko" ? "동기화 중..." : "Syncing...",
    syncFailed: language === "ko" ? "Sheets 동기화에 실패했습니다." : "Sheets sync failed.",
    syncResult: language === "ko" ? "동기화 결과" : "Sync result",
    syncDuration: language === "ko" ? "소요 시간" : "Duration",
    syncQuarantine: language === "ko" ? "쿼런틴" : "Quarantine",
    opsRuns: language === "ko" ? "운영 로그" : "Ops Runs",
    opsRunsEmpty: language === "ko" ? "기록된 실행 로그가 없습니다." : "No ops runs logged.",
    opsRunsHint:
      language === "ko"
        ? "최근 실행 기록과 승격 이력을 확인합니다."
        : "Recent Sheets sync and promotion runs.",
    opsActionSheets: language === "ko" ? "Sheets 동기화" : "Sheets Sync",
    opsActionPromotion: language === "ko" ? "패턴 승격" : "Pattern Promotion",
    opsActionCapsuleRefresh: language === "ko" ? "캡슐 스펙 갱신" : "Capsule Refresh",
    opsStatusSuccess: language === "ko" ? "성공" : "Success",
    opsStatusFailed: language === "ko" ? "실패" : "Failed",
    opsActor: language === "ko" ? "실행자" : "Actor",
    opsDetails: language === "ko" ? "상세 보기" : "Details",
    opsHide: language === "ko" ? "접기" : "Hide",
    opsPayload: language === "ko" ? "요청 파라미터" : "Payload",
    opsStats: language === "ko" ? "결과 통계" : "Stats",
    templateProvenance: language === "ko" ? "템플릿 근거 추적" : "Template Provenance",
    templateProvenanceHint:
      language === "ko"
        ? "템플릿이 어떤 노트북/가이드/증거에서 생성됐는지 확인합니다."
        : "Verify which notebooks, guides, and evidence produced each template.",
    templateNoProvenance:
      language === "ko" ? "근거 정보가 없습니다." : "No provenance metadata found.",
    templateNotebook: language === "ko" ? "노트북" : "Notebook",
    templateGuideTypes: language === "ko" ? "가이드 타입" : "Guide types",
    templateEvidence: language === "ko" ? "증거 레퍼런스" : "Evidence refs",
    narrativeSeeds: language === "ko" ? "서사 씨드" : "Narrative seeds",
    beatSheetLabel: language === "ko" ? "비트" : "Beats",
    storyboardLabel: language === "ko" ? "스토리보드" : "Storyboard",
    templatePublic: language === "ko" ? "공개" : "Public",
    templatePrivate: language === "ko" ? "비공개" : "Private",
    templateMissingOnly: language === "ko" ? "근거 없는 템플릿만" : "Missing provenance only",
    templateMissingBadge: language === "ko" ? "근거 누락" : "Missing provenance",
    promotionTitle: language === "ko" ? "패턴 승격" : "Pattern Promotion",
    promotionSubtitle:
      language === "ko"
        ? "검증된 후보를 Pattern Library로 승격하고 버전을 갱신합니다."
        : "Promote validated candidates and bump patternVersion.",
    promotionNote: language === "ko" ? "버전 노트" : "Version note",
    promotionMinConfidence: language === "ko" ? "최소 신뢰도" : "Min confidence",
    promotionMinSources: language === "ko" ? "최소 소스 수" : "Min sources",
    promotionMinFitness: language === "ko" ? "최소 Lift" : "Min lift",
    promotionDerive: language === "ko" ? "Evidence에서 후보 자동 생성" : "Derive candidates from evidence",
    promotionDryRun: language === "ko" ? "Dry run (DB 변경 없음)" : "Dry run (no DB writes)",
    promotionSubmit: language === "ko" ? "패턴 승격 실행" : "Run promotion",
    promotionSubmitting: language === "ko" ? "승격 중..." : "Promoting...",
    promotionFailed: language === "ko" ? "패턴 승격에 실패했습니다." : "Pattern promotion failed.",
    promotionResult: language === "ko" ? "승격 결과" : "Promotion result",
    capsuleRefreshTitle: language === "ko" ? "캡슐 스펙 갱신" : "Capsule Spec Refresh",
    capsuleRefreshSubtitle:
      language === "ko"
        ? "최신 패턴 버전을 캡슐 스펙에 동기화합니다."
        : "Sync capsule specs to the latest pattern snapshot.",
    capsuleRefreshVersion: language === "ko" ? "패턴 버전 (선택)" : "Pattern version (optional)",
    capsuleRefreshDryRun: language === "ko" ? "Dry run (DB 변경 없음)" : "Dry run (no DB writes)",
    capsuleRefreshOnlyActive: language === "ko" ? "활성 캡슐만" : "Active only",
    capsuleRefreshSubmit: language === "ko" ? "캡슐 갱신 실행" : "Run capsule refresh",
    capsuleRefreshSubmitting: language === "ko" ? "갱신 중..." : "Refreshing...",
    capsuleRefreshFailed:
      language === "ko" ? "캡슐 갱신에 실패했습니다." : "Capsule refresh failed.",
    capsuleRefreshResult: language === "ko" ? "갱신 결과" : "Refresh result",
    capsuleRefreshUpdated: language === "ko" ? "갱신된 캡슐" : "Capsules updated",
    publishTitle: language === "ko" ? "공개 템플릿 확인" : "Confirm Public Template",
    publishDesc:
      language === "ko"
        ? "이 템플릿을 공개로 생성합니다. 진행할까요?"
        : "This template will be created as public. Continue?",
    publishConfirm: language === "ko" ? "공개 생성" : "Publish",
    publishCancel: language === "ko" ? "취소" : "Cancel",
  };

  const showAdminHint = (loadError || "").toLowerCase().includes("admin");
  const showLoginCta = showAdminHint && !session?.authenticated;

  const selectedNotebook = useMemo(
    () => notebooks.find((item) => item.notebook_id === seedForm.notebookId),
    [notebooks, seedForm.notebookId]
  );
  const selectedCapsule = useMemo(
    () => capsules.find((item) => item.capsule_key === seedForm.capsuleKey),
    [capsules, seedForm.capsuleKey]
  );

  const buildSlug = (value: string) => {
    const cleaned = value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    if (!cleaned) {
      return `tmpl-seed-${Date.now()}`;
    }
    return cleaned.startsWith("tmpl-") ? cleaned : `tmpl-${cleaned}`;
  };

  useEffect(() => {
    if (seedForm.notebookId || notebooks.length === 0) return;
    const notebook = notebooks[0];
    setSeedForm((prev) => ({
      ...prev,
      notebookId: notebook.notebook_id,
      slug: buildSlug(notebook.notebook_id),
      title: `${notebook.title} Template`,
      description: `Seeded from ${notebook.notebook_id}`,
      tags: (notebook.cluster_tags || []).join(", "),
    }));
  }, [notebooks, seedForm.notebookId]);

  useEffect(() => {
    if (seedForm.capsuleKey || capsules.length === 0) return;
    const capsule = capsules[0];
    setSeedForm((prev) => ({
      ...prev,
      capsuleKey: capsule.capsule_key,
      capsuleVersion: capsule.version,
    }));
  }, [capsules, seedForm.capsuleKey]);

  useEffect(() => {
    if (!seedForm.isPublic && showPublishConfirm) {
      setShowPublishConfirm(false);
    }
  }, [seedForm.isPublic, showPublishConfirm]);

  const handleNotebookChange = (value: string) => {
    const notebook = notebooks.find((item) => item.notebook_id === value);
    setSeedForm((prev) => ({
      ...prev,
      notebookId: value,
      slug: buildSlug(value),
      title: notebook ? `${notebook.title} Template` : prev.title,
      description: notebook ? `Seeded from ${notebook.notebook_id}` : prev.description,
      tags: notebook ? (notebook.cluster_tags || []).join(", ") : prev.tags,
    }));
  };

  const handleCapsuleChange = (value: string) => {
    const capsule = capsules.find((item) => item.capsule_key === value);
    setSeedForm((prev) => ({
      ...prev,
      capsuleKey: value,
      capsuleVersion: capsule?.version || prev.capsuleVersion,
    }));
  };

  const submitSeed = async () => {
    if (!seedForm.notebookId || !seedForm.slug || !seedForm.title || !seedForm.capsuleKey) {
      setSeedError(labels.seedRequired);
      return;
    }
    setSeedError(null);
    setSeedSuccess(null);
    setSeedSubmitting(true);
    try {
      await api.seedTemplateFromEvidence({
        notebook_id: seedForm.notebookId,
        slug: seedForm.slug.trim(),
        title: seedForm.title.trim(),
        description: seedForm.description.trim() || undefined,
        capsule_key: seedForm.capsuleKey.trim(),
        capsule_version: seedForm.capsuleVersion.trim() || "latest",
        tags: seedForm.tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        is_public: seedForm.isPublic,
      });
      setSeedSuccess(labels.seedSuccess);
    } catch (err) {
      setSeedError(normalizeApiError(err, labels.seedFailed));
    } finally {
      setSeedSubmitting(false);
    }
  };

  const handleSeedSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (seedForm.isPublic) {
      setShowPublishConfirm(true);
      return;
    }
    await submitSeed();
  };

  const handlePublishConfirm = async () => {
    setShowPublishConfirm(false);
    await submitSeed();
  };

  const handlePromoteSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPromoteError(null);
    setPromoteResult(null);
    setPromoteSubmitting(true);
    const minConfidence = Number.isFinite(promoteForm.minConfidence)
      ? promoteForm.minConfidence
      : 0.6;
    const minSources = Number.isFinite(promoteForm.minSources) && promoteForm.minSources > 0
      ? promoteForm.minSources
      : 2;
    try {
      const result = await api.promotePatterns({
        derive_from_evidence: promoteForm.deriveFromEvidence,
        min_confidence: minConfidence,
        min_sources: minSources,
        min_fitness_score: Number.isFinite(promoteForm.minFitnessScore)
          ? promoteForm.minFitnessScore
          : undefined,
        note: promoteForm.note.trim(),
        dry_run: promoteForm.dryRun,
      });
      setPromoteResult(result);
      const nextLogs = await api.listOpsActions(8);
      setOpsLogs(nextLogs);
      if (!promoteForm.dryRun) {
        const nextStatus = await api.getPipelineStatus();
        setStatus(nextStatus);
      }
    } catch (err) {
      setPromoteError(normalizeApiError(err, labels.promotionFailed));
    } finally {
      setPromoteSubmitting(false);
    }
  };

  const handleCapsuleRefresh = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setRefreshError(null);
    setRefreshResult(null);
    setRefreshSubmitting(true);
    try {
      const patternVersion = refreshForm.patternVersion.trim();
      const result = await api.refreshCapsuleSpecs({
        pattern_version: patternVersion || undefined,
        dry_run: refreshForm.dryRun,
        only_active: refreshForm.onlyActive,
      });
      setRefreshResult(result);
      const nextLogs = await api.listOpsActions(8);
      setOpsLogs(nextLogs);
      if (!refreshForm.dryRun) {
        const nextStatus = await api.getPipelineStatus();
        setStatus(nextStatus);
      }
    } catch (err) {
      setRefreshError(normalizeApiError(err, labels.capsuleRefreshFailed));
    } finally {
      setRefreshSubmitting(false);
    }
  };

  const handleSheetsSync = async () => {
    setSyncError(null);
    setSyncResult(null);
    setSyncSubmitting(true);
    try {
      const result = await api.syncSheets();
      setSyncResult(result);
      const nextLogs = await api.listOpsActions(8);
      setOpsLogs(nextLogs);
      const nextStatus = await api.getPipelineStatus();
      setStatus(nextStatus);
    } catch (err) {
      setSyncError(normalizeApiError(err, labels.syncFailed));
    } finally {
      setSyncSubmitting(false);
    }
  };

  const stageCards = useMemo<StageCard[]>(() => {
    if (!status) return [];
    return [
      {
        key: "raw",
        title: labels.stageRawAssets,
        icon: Database,
        total: status.raw_assets.total,
        latest: status.raw_assets.latest,
        meta: `${labels.restricted}: ${status.raw_restricted}`,
      },
      {
        key: "video",
        title: labels.stageVideoSegments,
        icon: Clapperboard,
        total: status.video_segments.total,
        latest: status.video_segments.latest,
      },
      {
        key: "notebook",
        title: labels.stageNotebookLibrary,
        icon: BookOpen,
        total: status.notebook_library.total,
        latest: status.notebook_library.latest,
        meta: `${labels.stageAssets}: ${status.notebook_assets.total}`,
      },
      {
        key: "evidence",
        title: labels.stageEvidenceRecords,
        icon: Sparkles,
        total: status.evidence_records.total,
        latest: status.evidence_records.latest,
        meta: `${labels.evidenceMissingSourcePack}: ${status.evidence_missing_source_pack ?? 0} · ${labels.evidenceOpsOnly}: ${status.evidence_ops_only ?? 0}`,
      },
      {
        key: "candidates",
        title: labels.stagePatternCandidates,
        icon: Layers,
        total: status.pattern_candidates.total,
        latest: status.pattern_candidates.latest,
      },
      {
        key: "patterns",
        title: labels.stagePatternLibrary,
        icon: Layers,
        total: status.patterns.total,
        latest: status.patterns.latest,
        meta: `${labels.patternVersion}: ${status.pattern_version || "-"}`,
      },
      {
        key: "capsules",
        title: labels.stageCapsuleSpecs,
        icon: Package,
        total: status.capsule_specs.total,
        latest: status.capsule_specs.latest,
        meta: `${labels.patternVersion}: ${status.pattern_version || "-"}`,
      },
      {
        key: "templates",
        title: labels.stageTemplates,
        icon: Workflow,
        total: status.templates.total,
        latest: status.templates.latest,
        meta: `${labels.templatesPublic}: ${status.templates_public} · ${labels.templatesMissing}: ${status.templates_missing_provenance ?? 0
          }`,
      },
      {
        key: "runs",
        title: labels.stageCapsuleRuns,
        icon: Activity,
        total: status.capsule_runs.total,
        latest: status.capsule_runs.latest,
      },
      {
        key: "generation",
        title: labels.stageGenerationRuns,
        icon: CheckCircle2,
        total: status.generation_runs.total,
        latest: status.generation_runs.latest,
      },
    ];
  }, [
    status,
    labels.patternVersion,
    labels.templatesPublic,
    labels.templatesMissing,
    labels.restricted,
    labels.stageRawAssets,
    labels.stageVideoSegments,
    labels.stageNotebookLibrary,
    labels.stageEvidenceRecords,
    labels.evidenceMissingSourcePack,
    labels.evidenceOpsOnly,
    labels.stagePatternCandidates,
    labels.stagePatternLibrary,
    labels.stageCapsuleSpecs,
    labels.stageTemplates,
    labels.stageCapsuleRuns,
    labels.stageGenerationRuns,
    labels.stageAssets,
  ]);

  const patternHistory = status?.pattern_versions || [];
  const promoteStats = promoteResult?.stats || {};
  const formatOpsAction = (value: string) => {
    if (value === "sheets_sync") return labels.opsActionSheets;
    if (value === "pattern_promotion") return labels.opsActionPromotion;
    if (value === "capsule_refresh") return labels.opsActionCapsuleRefresh;
    return value;
  };
  const statusTone = (value: string) => {
    if (value === "success") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
    if (value === "failed") return "border-rose-500/30 bg-rose-500/10 text-rose-200";
    return "border-white/10 bg-white/5 text-slate-200";
  };
  const toggleLog = (id: string) => {
    setExpandedLogs((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getTemplateMeta = (template: Template) => {
    const graphMeta = (template.graph_data?.meta || {}) as Record<string, unknown>;
    const guideSources = Array.isArray(graphMeta.guide_sources) ? graphMeta.guide_sources : [];
    const firstSource = guideSources[0] as { notebook_id?: string; guide_types?: string[] } | undefined;
    const notebookId = firstSource?.notebook_id || "-";
    const guideTypes = Array.isArray(firstSource?.guide_types) ? firstSource?.guide_types : [];
    const evidenceRefs = Array.isArray(graphMeta.evidence_refs) ? graphMeta.evidence_refs : [];
    const narrativeSeeds = (graphMeta.narrative_seeds || {}) as Record<string, unknown>;
    const storyBeats = Array.isArray(narrativeSeeds.story_beats) ? narrativeSeeds.story_beats : [];
    const storyboardCards = Array.isArray(narrativeSeeds.storyboard_cards)
      ? narrativeSeeds.storyboard_cards
      : [];
    return {
      notebookId,
      guideTypes,
      evidenceRefs,
      storyBeats,
      storyboardCards,
      hasMeta: guideSources.length > 0 || evidenceRefs.length > 0,
    };
  };

  const missingProvenanceCount = useMemo(() => {
    if (typeof status?.templates_missing_provenance === "number") {
      return status.templates_missing_provenance;
    }
    return localizedTemplates.filter((template) => !getTemplateMeta(template).hasMeta).length;
  }, [localizedTemplates, status]);

  const templatesToShow = useMemo(() => {
    if (!showMissingOnly) return localizedTemplates;
    return localizedTemplates.filter((template) => !getTemplateMeta(template).hasMeta);
  }, [localizedTemplates, showMissingOnly]);

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-6xl">
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-sky-500/20">
                <Activity className="h-5 w-5 text-emerald-200" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">{labels.title}</h1>
                <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">{labels.subtitle}</p>
              </div>
            </div>
          </motion.div>

          {isLoading && (
            <PageStatus
              variant="loading"
              title={labels.loading}
              className="mb-4"
            />
          )}
          {!isLoading && loadError && !showAdminHint && (
            <PageStatus
              variant="error"
              title={labels.loadError}
              message={loadError}
              isOffline={isOffline}
              className="mb-4"
            />
          )}
          {!isLoading && showAdminHint && (
            <PageStatus
              variant="admin"
              title={labels.adminOnly}
              message={labels.adminOnlyHint}
              action={showLoginCta ? { label: labels.adminOnlyAction, href: "/login" } : undefined}
              className="mb-4"
            />
          )}

          {!isLoading && status && (
            <>
              <RunTraceDashboard className="mb-6" />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {stageCards.map((card, index) => (
                  <motion.div
                    key={card.key}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="rounded-xl border border-white/10 bg-slate-950/60 p-5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <card.icon className="h-4 w-4 text-[var(--accent)]" />
                        <h3 className="text-sm font-semibold text-[var(--fg-0)]">{card.title}</h3>
                      </div>
                      <span className="rounded-full bg-white/5 px-2 py-1 text-[10px] text-[var(--fg-muted)]">
                        {labels.latest}: {formatLatest(card.latest)}
                      </span>
                    </div>
                    <div className="mt-4 text-2xl font-semibold text-[var(--fg-0)]">
                      {card.total.toLocaleString()}
                    </div>
                    {card.meta && (
                      <div className="mt-2 text-xs text-[var(--fg-muted)]">{card.meta}</div>
                    )}
                  </motion.div>
                ))}
              </div>

              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-[var(--fg-muted)]">{labels.patternStatusTitle}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(status.pattern_status).map(([key, value]) => (
                      <span key={key} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                </div>
                <PatternVersionHistory limit={5} className="bg-white/5 border-white/10" />
                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="text-xs font-semibold text-[var(--fg-muted)]">{labels.runStatusTitle}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(status.capsule_run_status).map(([key, value]) => (
                      <span key={key} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
                        Capsule {key}: {value}
                      </span>
                    ))}
                    {Object.entries(status.generation_run_status).map(([key, value]) => (
                      <span key={key} className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200">
                        Generation {key}: {value}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-4 lg:col-span-2">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[var(--fg-muted)]">
                    <AlertTriangle className="h-4 w-4 text-amber-300" />
                    {labels.quarantine}
                    <span className="rounded-full border border-amber-400/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-200">
                      {status.quarantine_total || 0}
                    </span>
                  </div>
                  {status.quarantine_total ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(status.quarantine_items || []).slice(0, 8).map((item) => (
                        <span
                          key={`${item.sheet}-${item.reason}`}
                          className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-200"
                        >
                          {item.sheet}/{item.reason}: {item.count}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div className="mt-3 text-xs text-[var(--fg-muted)]">{labels.quarantineEmpty}</div>
                  )}
                </div>
              </div>

              <TemplateProvenance className="mt-6 bg-slate-950/60 border-white/10" />

              <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/10">
                    <Database className="h-5 w-5 text-sky-200" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--fg-0)]">{labels.syncTitle}</h2>
                    <p className="text-sm text-[var(--fg-muted)]">{labels.syncSubtitle}</p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-[var(--fg-muted)]">
                  <div>
                    {labels.quarantine}:{" "}
                    <span className="font-semibold text-amber-200">{status.quarantine_total || 0}</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleSheetsSync}
                    disabled={syncSubmitting}
                    className="rounded-lg bg-sky-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {syncSubmitting ? labels.syncSubmitting : labels.syncSubmit}
                  </button>
                </div>

                {syncError && (
                  <div className="mt-3 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                    {syncError}
                  </div>
                )}
                {syncResult && (
                  <div className="mt-3 rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-xs text-slate-200">
                    <div className="font-semibold text-[var(--fg-0)]">{labels.syncResult}</div>
                    <div className="mt-2 flex flex-wrap gap-3">
                      <span>
                        {labels.syncDuration}: {syncResult.duration_ms}ms
                      </span>
                      <span>
                        {labels.syncQuarantine}: {syncResult.quarantine_total}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/10">
                    <Layers className="h-5 w-5 text-sky-200" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--fg-0)]">{labels.promotionTitle}</h2>
                    <p className="text-sm text-[var(--fg-muted)]">{labels.promotionSubtitle}</p>
                  </div>
                </div>

                <form onSubmit={handlePromoteSubmit} className="mt-5 space-y-4 text-sm">
                  <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                    {labels.promotionNote}
                    <input
                      value={promoteForm.note}
                      onChange={(event) =>
                        setPromoteForm((prev) => ({ ...prev, note: event.target.value }))
                      }
                      className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                      placeholder="manual promotion note"
                    />
                  </label>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                      {labels.promotionMinConfidence}
                      <input
                        type="number"
                        step="0.05"
                        min={0}
                        max={1}
                        value={promoteForm.minConfidence}
                        onChange={(event) =>
                          setPromoteForm((prev) => ({
                            ...prev,
                            minConfidence: Number(event.target.value),
                          }))
                        }
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                      />
                    </label>
                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                      {labels.promotionMinSources}
                      <input
                        type="number"
                        min={2}
                        value={promoteForm.minSources}
                        onChange={(event) =>
                          setPromoteForm((prev) => ({
                            ...prev,
                            minSources: Number(event.target.value),
                          }))
                        }
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                      />
                    </label>
                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                      {labels.promotionMinFitness}
                      <input
                        type="number"
                        step="0.05"
                        min={0}
                        max={1}
                        value={promoteForm.minFitnessScore}
                        onChange={(event) =>
                          setPromoteForm((prev) => ({
                            ...prev,
                            minFitnessScore: Number(event.target.value),
                          }))
                        }
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                      />
                    </label>
                  </div>

                  <div className="flex flex-wrap gap-4 text-xs text-[var(--fg-muted)]">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={promoteForm.deriveFromEvidence}
                        onChange={(event) =>
                          setPromoteForm((prev) => ({
                            ...prev,
                            deriveFromEvidence: event.target.checked,
                          }))
                        }
                        className="h-4 w-4 rounded border-white/20 bg-slate-950/60 text-[var(--accent)]"
                      />
                      {labels.promotionDerive}
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={promoteForm.dryRun}
                        onChange={(event) =>
                          setPromoteForm((prev) => ({
                            ...prev,
                            dryRun: event.target.checked,
                          }))
                        }
                        className="h-4 w-4 rounded border-white/20 bg-slate-950/60 text-[var(--accent)]"
                      />
                      {labels.promotionDryRun}
                    </label>
                  </div>

                  {promoteError && (
                    <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                      {promoteError}
                    </div>
                  )}

                  {promoteResult && (
                    <div className="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-xs text-slate-200">
                      <div className="font-semibold text-[var(--fg-0)]">{labels.promotionResult}</div>
                      <div className="mt-2 grid gap-2 sm:grid-cols-2">
                        <div>changed: {promoteResult.changed ? "yes" : "no"}</div>
                        <div>patternVersion: {promoteResult.pattern_version || "-"}</div>
                        <div>candidates: {promoteStats.candidates ?? 0}</div>
                        <div>promoted: {promoteStats.promoted_patterns ?? 0}</div>
                        <div>trace upserted: {promoteStats.traces_upserted ?? 0}</div>
                        <div>skipped rights: {promoteStats.skipped_rights ?? 0}</div>
                        <div>skipped sources: {promoteStats.skipped_sources ?? 0}</div>
                        <div>skipped confidence: {promoteStats.skipped_confidence ?? 0}</div>
                        <div>skipped fitness: {promoteStats.skipped_fitness ?? 0}</div>
                        <div>skipped evidence: {promoteStats.skipped_evidence ?? 0}</div>
                        <div>skipped taxonomy: {promoteStats.skipped_taxonomy ?? 0}</div>
                        <div>skipped trace min: {promoteStats.skipped_trace_min ?? 0}</div>
                        <div>skipped coverage: {promoteStats.skipped_coverage ?? 0}</div>
                        <div>derived: {promoteResult.derived_candidates ?? 0}</div>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={promoteSubmitting}
                      className="rounded-lg bg-sky-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {promoteSubmitting ? labels.promotionSubmitting : labels.promotionSubmit}
                    </button>
                  </div>
                </form>
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10">
                    <Package className="h-5 w-5 text-emerald-200" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--fg-0)]">
                      {labels.capsuleRefreshTitle}
                    </h2>
                    <p className="text-sm text-[var(--fg-muted)]">
                      {labels.capsuleRefreshSubtitle}
                    </p>
                  </div>
                </div>

                <form onSubmit={handleCapsuleRefresh} className="mt-5 space-y-4 text-sm">
                  <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                    {labels.capsuleRefreshVersion}
                    <input
                      value={refreshForm.patternVersion}
                      onChange={(event) =>
                        setRefreshForm((prev) => ({
                          ...prev,
                          patternVersion: event.target.value,
                        }))
                      }
                      className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                      placeholder={status?.pattern_version || "latest"}
                    />
                  </label>
                  <label className="flex items-center gap-2 text-xs text-[var(--fg-muted)]">
                    <input
                      type="checkbox"
                      checked={refreshForm.dryRun}
                      onChange={(event) =>
                        setRefreshForm((prev) => ({
                          ...prev,
                          dryRun: event.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-white/20 bg-slate-950/60 text-[var(--accent)]"
                    />
                    {labels.capsuleRefreshDryRun}
                  </label>
                  <label className="flex items-center gap-2 text-xs text-[var(--fg-muted)]">
                    <input
                      type="checkbox"
                      checked={refreshForm.onlyActive}
                      onChange={(event) =>
                        setRefreshForm((prev) => ({
                          ...prev,
                          onlyActive: event.target.checked,
                        }))
                      }
                      className="h-4 w-4 rounded border-white/20 bg-slate-950/60 text-[var(--accent)]"
                    />
                    {labels.capsuleRefreshOnlyActive}
                  </label>

                  {refreshError && (
                    <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                      {refreshError}
                    </div>
                  )}

                  {refreshResult && (
                    <div className="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-xs text-slate-200">
                      <div className="font-semibold text-[var(--fg-0)]">
                        {labels.capsuleRefreshResult}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-3">
                        <span>
                          {labels.patternVersion}: {refreshResult.pattern_version}
                        </span>
                        <span>
                          {labels.capsuleRefreshUpdated}: {refreshResult.updated}
                        </span>
                        <span>dry run: {refreshResult.dry_run ? "yes" : "no"}</span>
                        <span>
                          {labels.capsuleRefreshOnlyActive}: {refreshResult.only_active ? "yes" : "no"}
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={refreshSubmitting}
                      className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {refreshSubmitting
                        ? labels.capsuleRefreshSubmitting
                        : labels.capsuleRefreshSubmit}
                    </button>
                  </div>
                </form>
              </div>

              <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-500/10">
                    <Activity className="h-5 w-5 text-slate-200" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--fg-0)]">{labels.opsRuns}</h2>
                    <p className="text-sm text-[var(--fg-muted)]">
                      {opsLogError ? opsLogError : labels.opsRunsHint}
                    </p>
                  </div>
                </div>

                <div className="mt-4 space-y-3 text-xs text-slate-200">
                  {opsLogs.length === 0 ? (
                    <div className="rounded-lg border border-white/10 bg-slate-950/40 px-3 py-3 text-[var(--fg-muted)]">
                      {labels.opsRunsEmpty}
                    </div>
                  ) : (
                    opsLogs.map((log) => (
                      <div
                        key={log.id}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2"
                      >
                        <div className="flex flex-col gap-1">
                          <div className="text-[var(--fg-0)]">{formatOpsAction(log.action_type)}</div>
                          {log.note && (
                            <div className="text-[10px] text-[var(--fg-muted)]">{log.note}</div>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-[10px]">
                          <span
                            className={`rounded-full border px-2 py-0.5 ${statusTone(log.status)}`}
                          >
                            {log.status === "success"
                              ? labels.opsStatusSuccess
                              : log.status === "failed"
                                ? labels.opsStatusFailed
                                : log.status}
                          </span>
                          {log.actor_id && (
                            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-slate-200">
                              {labels.opsActor}: {log.actor_id}
                            </span>
                          )}
                          <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-slate-200">
                            {log.duration_ms ? `${log.duration_ms}ms` : "-"}
                          </span>
                          <span className="text-[var(--fg-muted)]">{log.created_at}</span>
                          <button
                            type="button"
                            onClick={() => toggleLog(log.id)}
                            className="rounded-full border border-white/10 px-2 py-0.5 text-slate-200 transition-colors hover:bg-white/5"
                          >
                            {expandedLogs[log.id] ? labels.opsHide : labels.opsDetails}
                          </button>
                        </div>
                        {expandedLogs[log.id] && (
                          <div className="w-full rounded-lg border border-white/10 bg-slate-950/60 p-3 text-[10px] text-slate-300">
                            <div className="grid gap-3 sm:grid-cols-2">
                              <div>
                                <div className="text-[9px] uppercase text-[var(--fg-muted)]">
                                  {labels.opsPayload}
                                </div>
                                <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-words">
                                  {JSON.stringify(log.payload || {}, null, 2)}
                                </pre>
                              </div>
                              <div>
                                <div className="text-[9px] uppercase text-[var(--fg-muted)]">
                                  {labels.opsStats}
                                </div>
                                <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap break-words">
                                  {JSON.stringify(log.stats || {}, null, 2)}
                                </pre>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {status.quarantine_sample && status.quarantine_sample.length > 0 && (
                <QuarantineSample limit={6} className="mt-6 bg-slate-950/60 border-white/10" />
              )}

              <div className="mt-8 rounded-2xl border border-white/10 bg-slate-950/60 p-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10">
                    <Sparkles className="h-5 w-5 text-emerald-200" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--fg-0)]">{labels.seedTitle}</h2>
                    <p className="text-sm text-[var(--fg-muted)]">{labels.seedSubtitle}</p>
                  </div>
                </div>

                <form onSubmit={handleSeedSubmit} className="mt-5 space-y-4 text-sm">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                      {labels.seedNotebook}
                      <select
                        value={seedForm.notebookId}
                        onChange={(event) => handleNotebookChange(event.target.value)}
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                        disabled={notebooks.length === 0}
                      >
                        {notebooks.length === 0 && (
                          <option value="">{labels.seedNoNotebook}</option>
                        )}
                        {notebooks.map((item) => (
                          <option key={item.notebook_id} value={item.notebook_id}>
                            {item.title || item.notebook_id}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                      {labels.seedCapsule}
                      <select
                        value={seedForm.capsuleKey}
                        onChange={(event) => handleCapsuleChange(event.target.value)}
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                        disabled={capsules.length === 0}
                      >
                        {capsules.length === 0 && (
                          <option value="">{labels.seedNoCapsule}</option>
                        )}
                        {capsules.map((item) => (
                          <option key={item.capsule_key} value={item.capsule_key}>
                            {item.display_name}
                          </option>
                        ))}
                      </select>
                      {selectedCapsule && (
                        <span className="text-[10px] text-[var(--fg-muted)]">
                          {selectedCapsule.description}
                        </span>
                      )}
                    </label>
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
                      {labels.seedName}
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
                      {labels.seedTags}
                      <input
                        value={seedForm.tags}
                        onChange={(event) =>
                          setSeedForm((prev) => ({ ...prev, tags: event.target.value }))
                        }
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                        placeholder={selectedNotebook?.cluster_tags?.join(", ") || "thriller, suspense"}
                      />
                    </label>
                    <label className="flex flex-col gap-2 text-xs text-[var(--fg-muted)]">
                      {labels.seedCapsuleVersion}
                      <input
                        value={seedForm.capsuleVersion}
                        onChange={(event) =>
                          setSeedForm((prev) => ({ ...prev, capsuleVersion: event.target.value }))
                        }
                        className="rounded-lg border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-[var(--fg-0)] focus:border-[var(--accent)]"
                      />
                    </label>
                  </div>

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

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={seedSubmitting || !seedForm.notebookId || !seedForm.capsuleKey}
                      className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {seedSubmitting ? labels.seedSubmitting : labels.seedSubmit}
                    </button>
                  </div>
                </form>
              </div>
            </>
          )}
        </div>
      </div>
      {showPublishConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="publish-confirm-title"
          aria-describedby="publish-confirm-desc"
          onClick={() => setShowPublishConfirm(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950/90 p-5 text-sm text-[var(--fg-0)] shadow-xl"
            onClick={(event) => event.stopPropagation()}
          >
            <h3 id="publish-confirm-title" className="text-base font-semibold">
              {labels.publishTitle}
            </h3>
            <p id="publish-confirm-desc" className="mt-2 text-xs text-[var(--fg-muted)]">
              {labels.publishDesc}
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-lg border border-white/10 px-3 py-2 text-xs text-[var(--fg-0)] transition-colors hover:bg-white/5 disabled:opacity-60"
                onClick={() => setShowPublishConfirm(false)}
                disabled={seedSubmitting}
              >
                {labels.publishCancel}
              </button>
              <button
                type="button"
                className="rounded-lg bg-emerald-500 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handlePublishConfirm}
                disabled={seedSubmitting}
              >
                {seedSubmitting ? labels.seedSubmitting : labels.publishConfirm}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
