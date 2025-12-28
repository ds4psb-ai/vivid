"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Film,
  Palette,
  Music,
  Zap,
  Coffee,
  Clapperboard,
  ArrowRight,
  History as HistoryIcon,
  X,
  Check,
  RefreshCcw,
  Globe,
} from "lucide-react";
import { api, Template, TemplateVersion } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import PageStatus from "@/components/PageStatus";
import { isNetworkError, normalizeApiError } from "@/lib/errors";
import { localizeTemplate } from "@/lib/templateLocalization";
import { translations } from "@/lib/translations";
import { withViewTransition } from "@/lib/viewTransitions";
import { getBeatLabel, getStoryboardLabel } from "@/lib/narrative";
import AppShell from "@/components/AppShell";

// Helper component for TemplateCard to use translations
const TemplateCardText = ({ tKey }: { tKey: keyof typeof translations.ko }) => {
  const { t } = useLanguage();
  return <>{t(tKey)}</>;
};

// Icon mapping for each auteur
const AUTEUR_ICONS: Record<string, React.ElementType> = {
  "tmpl-auteur-bong": Film,
  "tmpl-auteur-park": Palette,
  "tmpl-auteur-shinkai": Sparkles,
  "tmpl-auteur-leejunho": Music,
  "tmpl-auteur-na": Zap,
  "tmpl-auteur-hong": Coffee,
  "tmpl-production-stage": Clapperboard,
};

const AUTEUR_COLORS: Record<string, { gradient: string; glow: string }> = {
  "tmpl-auteur-bong": { gradient: "from-sky-400 to-blue-600", glow: "shadow-sky-500/30" },
  "tmpl-auteur-park": { gradient: "from-amber-400 to-orange-600", glow: "shadow-amber-500/30" },
  "tmpl-auteur-shinkai": { gradient: "from-cyan-400 to-teal-600", glow: "shadow-cyan-500/30" },
  "tmpl-auteur-leejunho": { gradient: "from-emerald-400 to-teal-600", glow: "shadow-emerald-500/30" },
  "tmpl-auteur-na": { gradient: "from-rose-400 to-red-600", glow: "shadow-rose-500/30" },
  "tmpl-auteur-hong": { gradient: "from-slate-400 to-zinc-600", glow: "shadow-slate-500/30" },
  "tmpl-production-stage": { gradient: "from-lime-400 to-emerald-600", glow: "shadow-emerald-500/30" },
};

const isVideoPreview = (url?: string | null) => {
  if (!url) return false;
  const clean = url.split("?")[0].toLowerCase();
  return [".mp4", ".webm", ".mov"].some((ext) => clean.endsWith(ext));
};

const getNarrativeSeeds = (graphData?: Record<string, unknown>) => {
  const meta = graphData?.meta;
  const narrativeSeeds =
    meta && typeof meta === "object"
      ? ((meta as Record<string, unknown>).narrative_seeds as Record<string, unknown>) || {}
      : {};
  const storyBeats = Array.isArray(narrativeSeeds.story_beats)
    ? narrativeSeeds.story_beats
    : [];
  const storyboardCards = Array.isArray(narrativeSeeds.storyboard_cards)
    ? narrativeSeeds.storyboard_cards
    : [];
  const beatSnippet = getBeatLabel(storyBeats[0]);
  const storyboardSnippet = getStoryboardLabel(storyboardCards[0]);
  return {
    storyBeats,
    storyboardCards,
    beatSnippet,
    storyboardSnippet,
    hasSeeds: storyBeats.length > 0 || storyboardCards.length > 0,
  };
};

const isProductionTemplateGraph = (graphData?: Record<string, unknown>) => {
  const meta = graphData?.meta as Record<string, unknown> | undefined;
  if (!meta || typeof meta !== "object") return false;
  const production = meta.production_contract as Record<string, unknown> | undefined;
  if (!production || typeof production !== "object") return false;
  const shotContracts = Array.isArray(production.shot_contracts) ? production.shot_contracts : [];
  const storyboardRefs = Array.isArray(production.storyboard_refs) ? production.storyboard_refs : [];
  return shotContracts.length > 0 || storyboardRefs.length > 0;
};

function TemplateCard({
  template,
  onSelect,
  onOpenVersions,
  isCreating,
}: {
  template: Template;
  onSelect: () => void;
  onOpenVersions: () => void;
  isCreating: boolean;
}) {
  const { t } = useLanguage();
  const Icon = AUTEUR_ICONS[template.slug] || Sparkles;
  const colors = AUTEUR_COLORS[template.slug] || { gradient: "from-slate-400 to-slate-600", glow: "shadow-slate-500/20" };
  const [isHovered, setIsHovered] = useState(false);
  const graphMeta = (template.graph_data?.meta || {}) as Record<string, unknown>;
  const evidenceRefs = Array.isArray(graphMeta.evidence_refs) ? graphMeta.evidence_refs : [];
  const evidenceCount = evidenceRefs.length;
  const isProductionTemplate = isProductionTemplateGraph(template.graph_data as unknown as Record<string, unknown>);
  const seeds = getNarrativeSeeds(template.graph_data as unknown as Record<string, unknown>);
  const guideSources = Array.isArray(graphMeta.guide_sources) ? graphMeta.guide_sources : [];
  const guideTypeSet = new Set<string>();
  guideSources.forEach((source) => {
    if (!source || typeof source !== "object") return;
    const guideTypes = (source as { guide_types?: unknown }).guide_types;
    if (!Array.isArray(guideTypes)) return;
    guideTypes.forEach((type) => {
      if (typeof type === "string" && type.trim()) {
        guideTypeSet.add(type.trim());
      }
    });
  });
  const guideLabelMap: Record<string, string> = {
    summary: t("guideSummary"),
    homage: t("guideHomage"),
    variation: t("guideVariation"),
    template_fit: t("guideTemplateFit"),
    persona: t("guidePersona"),
    synapse: t("guideSynapse"),
    story: t("guideStory"),
    beat_sheet: t("guideBeatSheet"),
    storyboard: t("guideStoryboard"),
  };
  const guideLabels = Array.from(guideTypeSet).map((type) => guideLabelMap[type] || type.toUpperCase());
  const visibleGuideLabels = guideLabels.slice(0, 3);
  const extraGuideCount = guideLabels.length - visibleGuideLabels.length;

  // Spring animation config for premium feel
  const springConfig = { type: "spring" as const, stiffness: 400, damping: 28 };

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -12 }}
      whileTap={{ scale: 0.98 }}
      transition={springConfig}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      aria-label={`${template.title} - ${template.description}`}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      className="group relative cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-0)] rounded-[var(--card-radius)]"
    >
      {/* Glass Card Container */}
      <div
        className="relative flex flex-col overflow-hidden rounded-[var(--card-radius)] border backdrop-blur-xl transition-all duration-300 ease-out"
        style={{
          background: isHovered ? 'var(--card-bg-hover)' : 'var(--card-bg)',
          borderColor: isHovered ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.1)',
          boxShadow: isHovered ? 'var(--card-shadow-hover)' : 'var(--card-shadow)',
        }}
      >
        {/* ─── Thumbnail Section ─── */}
        <div className="relative m-[var(--card-padding)] aspect-[16/10] overflow-hidden rounded-[var(--card-inner-radius)] bg-gradient-to-br from-slate-900/90 to-slate-800/60">

          {/* Media Content */}
          <AnimatePresence mode="wait">
            {template.preview_video_url ? (
              isVideoPreview(template.preview_video_url) ? (
                <motion.video
                  key="video"
                  src={template.preview_video_url}
                  muted
                  autoPlay={isHovered}
                  loop
                  playsInline
                  preload="metadata"
                  initial={{ scale: 1, opacity: 0.85 }}
                  animate={{
                    scale: isHovered ? 1.06 : 1,
                    opacity: isHovered ? 1 : 0.85,
                    filter: isHovered ? 'brightness(1.05)' : 'brightness(0.95)'
                  }}
                  transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
                  className="absolute inset-0 h-full w-full object-cover"
                />
              ) : (
                <motion.img
                  key="image"
                  src={template.preview_video_url}
                  alt={template.title}
                  loading="lazy"
                  initial={{ scale: 1, opacity: 0.85 }}
                  animate={{
                    scale: isHovered ? 1.06 : 1,
                    opacity: isHovered ? 1 : 0.85,
                    filter: isHovered ? 'brightness(1.05)' : 'brightness(0.95)'
                  }}
                  transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
                  className="absolute inset-0 h-full w-full object-cover"
                />
              )
            ) : (
              // Fallback: Gradient + Icon
              <motion.div
                className={`absolute inset-0 bg-gradient-to-br ${colors.gradient}`}
                initial={{ opacity: 0.25 }}
                animate={{ opacity: isHovered ? 0.35 : 0.25 }}
              >
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div
                    animate={{ scale: isHovered ? 1.15 : 1, rotate: isHovered ? 5 : 0 }}
                    transition={springConfig}
                    className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${colors.gradient} flex items-center justify-center shadow-2xl ring-1 ring-white/10`}
                  >
                    <Icon className="h-8 w-8 text-white drop-shadow-lg" strokeWidth={1.5} />
                  </motion.div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Gradient Overlay */}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent opacity-60 group-hover:opacity-80 transition-opacity duration-300" />

          {/* ─── Badges (Stagger Animation) ─── */}
          <div className="absolute top-2.5 left-2.5 flex flex-wrap gap-1.5">
            {evidenceCount > 0 && (
              <motion.span
                initial={{ opacity: 0, x: -8, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                transition={{ delay: 0.1, ...springConfig }}
                className="inline-flex items-center gap-1 rounded-full bg-emerald-500/95 px-2.5 py-1 text-[10px] font-bold text-white shadow-lg shadow-emerald-500/30 backdrop-blur-sm"
              >
                <Check className="h-3 w-3" />
                {t("templateVerified")}
              </motion.span>
            )}
            {isProductionTemplate && (
              <motion.span
                initial={{ opacity: 0, x: -8, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                transition={{ delay: 0.2, ...springConfig }}
                className="inline-flex items-center gap-1 rounded-full bg-sky-500/95 px-2.5 py-1 text-[10px] font-bold text-white shadow-lg shadow-sky-500/30 backdrop-blur-sm"
              >
                <Clapperboard className="h-3 w-3" />
                {t("productionTemplate")}
              </motion.span>
            )}
          </div>

          {/* Version Badge */}
          {template.version !== undefined && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.15 }}
              className="absolute top-2.5 right-2.5 rounded-full bg-black/60 px-2.5 py-1 text-[10px] font-semibold text-white/90 backdrop-blur-md shadow-lg"
            >
              v{template.version}
            </motion.span>
          )}

          {/* ─── Hover CTA Button ─── */}
          <motion.div
            initial={{ opacity: 0, y: 12, scale: 0.92 }}
            animate={{
              opacity: isHovered ? 1 : 0,
              y: isHovered ? 0 : 12,
              scale: isHovered ? 1 : 0.92
            }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <div className="flex items-center gap-2.5 rounded-full bg-white px-6 py-3 text-sm font-bold text-slate-900 shadow-2xl shadow-black/30 ring-1 ring-white/20">
              <Sparkles className="h-4 w-4 text-[var(--accent)]" />
              {t("createCanvas")}
              <ArrowRight className="h-4 w-4 opacity-60" />
            </div>
          </motion.div>
        </div>

        {/* ─── Content Section ─── */}
        <div className="flex flex-1 flex-col px-5 pb-5">

          {/* Title */}
          <h3 className="text-[15px] font-semibold leading-tight text-white/95 group-hover:text-white transition-colors duration-200 line-clamp-1">
            {template.title}
          </h3>

          {/* Description */}
          <p className="mt-2 text-[13px] leading-relaxed text-white/50 group-hover:text-white/70 transition-colors duration-200 line-clamp-2">
            {template.description}
          </p>

          {/* Narrative Seeds */}
          {seeds.hasSeeds && (
            <div className="mt-3 flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-white/[0.04] px-2 py-1 text-[10px] font-medium text-white/50 ring-1 ring-white/[0.06]">
                <span className="opacity-70">📝</span>
                {seeds.storyBeats.length} {t("beats") || "beats"}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-md bg-white/[0.04] px-2 py-1 text-[10px] font-medium text-white/50 ring-1 ring-white/[0.06]">
                <span className="opacity-70">🎬</span>
                {seeds.storyboardCards.length} {t("shots") || "shots"}
              </span>
            </div>
          )}

          {/* Guide Labels */}
          {visibleGuideLabels.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {visibleGuideLabels.map((label, i) => (
                <motion.span
                  key={label}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 + i * 0.05 }}
                  className="rounded-full bg-white/[0.05] px-2.5 py-1 text-[10px] font-medium text-white/55 ring-1 ring-white/[0.06]"
                >
                  {label}
                </motion.span>
              ))}
              {extraGuideCount > 0 && (
                <span className="rounded-full bg-white/[0.03] px-2.5 py-1 text-[10px] font-medium text-white/35">
                  +{extraGuideCount}
                </span>
              )}
            </div>
          )}

          {/* ─── Footer ─── */}
          <div className="mt-auto pt-4">
            <div className="flex items-center justify-between border-t border-white/[0.06] pt-3">
              {/* Tags */}
              <div className="flex items-center gap-1.5 overflow-hidden">
                {template.tags.slice(0, 2).map((tag) => (
                  <span
                    key={tag}
                    className="truncate rounded bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium text-white/40 ring-1 ring-white/[0.05]"
                  >
                    {tag}
                  </span>
                ))}
                {template.tags.length > 2 && (
                  <span className="text-[9px] text-white/25">+{template.tags.length - 2}</span>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpenVersions();
                  }}
                  className="rounded-full border border-white/10 bg-white/[0.04] p-2 text-white/50 hover:bg-white/10 hover:text-white/90 hover:border-white/20 transition-all duration-200"
                  title={t("versions")}
                  aria-label={t("versions")}
                >
                  <HistoryIcon className="h-3.5 w-3.5" />
                </motion.button>

                {/* Animated Arrow on Hover */}
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={{
                    width: isHovered ? 28 : 0,
                    opacity: isHovered ? 1 : 0
                  }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--accent)]/20">
                    <ArrowRight className="h-4 w-4 text-[var(--accent)]" />
                  </div>
                </motion.div>
              </div>
            </div>
          </div>
        </div>

        {/* ─── Auteur Glow Effect (Subtle) ─── */}
        <div
          className="pointer-events-none absolute -inset-px rounded-[var(--card-radius)] opacity-0 group-hover:opacity-100 transition-opacity duration-500"
          style={{
            boxShadow: colors.glow.includes('sky') ? 'var(--glow-sky)' :
              colors.glow.includes('amber') ? 'var(--glow-amber)' :
                colors.glow.includes('rose') ? 'var(--glow-rose)' :
                  colors.glow.includes('emerald') ? 'var(--glow-emerald)' :
                    'var(--glow-violet)'
          }}
        />
      </div>

      {/* ─── Creating Overlay ─── */}
      <AnimatePresence>
        {isCreating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-20 flex items-center justify-center rounded-[var(--card-radius)] bg-black/85 backdrop-blur-md"
          >
            <div className="flex flex-col items-center gap-3">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
                className="h-8 w-8 rounded-full border-2 border-[var(--accent)] border-t-transparent"
              />
              <span className="text-sm font-medium text-white/90">{t("creating")}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
}

function HomePageContent() {
  const router = useRouter();
  const { t, language, setLanguage } = useLanguage();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templateFilter, setTemplateFilter] = useState<"all" | "production">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [creating, setCreating] = useState<string | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [templateVersions, setTemplateVersions] = useState<TemplateVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [versionAction, setVersionAction] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const [trackedReferral, setTrackedReferral] = useState(false);

  const localizedTemplates = useMemo(
    () => templates.map((template) => localizeTemplate(template, language)),
    [templates, language]
  );

  const templateVersionIndex = useMemo(() => {
    if (!selectedTemplate?.version) return null;
    return selectedTemplate.version;
  }, [selectedTemplate]);

  const filteredTemplates = useMemo(() => {
    if (templateFilter === "production") {
      return localizedTemplates.filter((template) =>
        isProductionTemplateGraph(template.graph_data as unknown as Record<string, unknown>)
      );
    }
    return localizedTemplates;
  }, [localizedTemplates, templateFilter]);

  useEffect(() => {
    api.listTemplates()
      .then((result) => {
        setTemplates(result);
        setIsOffline(false);
      })
      .catch((err) => {
        setError(normalizeApiError(err, t("loadTemplatesError")));
        setIsOffline(isNetworkError(err));
      })
      .finally(() => setLoading(false));
  }, [t]);

  useEffect(() => {
    if (trackedReferral) return;
    const code = searchParams?.get("ref") || "";
    if (!code) return;
    setTrackedReferral(true);
    void api.trackAffiliateClick({ affiliate_code: code }).catch(() => undefined);
  }, [searchParams, trackedReferral]);

  const handleSelectTemplate = async (template: Template) => {
    setCreating(template.id);
    try {
      const canvas = await api.createCanvasFromTemplate(template.id, `${template.title} - ${t("newProject")}`);
      withViewTransition(() => router.push(`/canvas?id=${canvas.id}`));
    } catch (err) {
      setError(normalizeApiError(err, t("createCanvasError")));
      setCreating(null);
    }
  };

  const handleOpenVersions = async (template: Template) => {
    setSelectedTemplate(template);
    setShowVersions(true);
    setVersionsLoading(true);
    setVersionsError(null);
    try {
      const versions = await api.listTemplateVersions(template.id);
      setTemplateVersions(versions);
    } catch (err) {
      setVersionsError(normalizeApiError(err, t("loadVersionsError")));
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleUseVersion = async (version: TemplateVersion) => {
    if (!selectedTemplate) return;
    setVersionAction(version.id);
    try {
      const canvas = await api.createCanvas({
        title: `${selectedTemplate.title} v${version.version}`,
        graph_data: version.graph_data,
        is_public: false,
      });
      withViewTransition(() => router.push(`/canvas?id=${canvas.id}`));
    } catch (err) {
      setVersionsError(normalizeApiError(err, t("createCanvasError")));
    } finally {
      setVersionAction(null);
    }
  };

  const handleRevertVersion = async (version: TemplateVersion) => {
    if (!selectedTemplate) return;
    setVersionAction(`revert-${version.id}`);
    try {
      const updated = await api.updateTemplate(selectedTemplate.id, {
        graph_data: version.graph_data,
        notes: `revert to v${version.version}`,
      });
      setTemplates((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setSelectedTemplate(updated);
      const versions = await api.listTemplateVersions(updated.id);
      setTemplateVersions(versions);
    } catch (err) {
      setVersionsError(normalizeApiError(err, t("revertTemplateError")));
    } finally {
      setVersionAction(null);
    }
  };

  return (
    <AppShell showTopBar={false}>
      {/* Aurora Background Effects */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-purple-900/20 blur-[128px] animate-pulse" />
        <div className="absolute top-[-20%] right-[-10%] w-[40%] h-[50%] rounded-full bg-blue-900/20 blur-[128px] animate-pulse delay-700" />
        <div className="absolute bottom-[-20%] left-[20%] w-[60%] h-[50%] rounded-full bg-indigo-900/20 blur-[128px] animate-pulse delay-1000" />
      </div>

      <div className="relative z-10 min-h-screen px-6 py-20">
        <div className="mx-auto max-w-7xl">
          {/* Header */}
          <div className="text-center relative">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="inline-flex items-center gap-2 rounded-full border border-[#4200FF]/20 bg-[#4200FF]/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#4200FF] backdrop-blur-md shadow-lg shadow-[#4200FF]/10 mb-8"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>{t("homeBadge")}</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30, filter: "blur(10px)" }}
              animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ delay: 0.1, duration: 0.8, ease: "easeOut" }}
              className="font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white via-slate-200 to-slate-400 text-5xl md:text-7xl drop-shadow-2xl"
            >
              {t("homeTitle")}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="mx-auto mt-6 max-w-2xl text-lg sm:text-xl text-slate-400 leading-relaxed font-light"
            >
              {t("homeSubtitle")}
            </motion.p>

            {/* Language Switcher */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="absolute top-0 right-0 hidden lg:block"
            >
              <button
                onClick={() => setLanguage(language === "ko" ? "en" : "ko")}
                className="group flex items-center gap-2 rounded-full border border-white/5 bg-slate-900/50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400 hover:bg-white/10 hover:text-white hover:border-white/10 transition-all backdrop-blur-md"
              >
                <Globe className="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity" />
                {language === "ko" ? "English" : "한국어"}
              </button>
            </motion.div>
          </div>

          {/* Error */}
          {error && (
            <div className="mx-auto mt-8 max-w-md">
              <PageStatus
                variant="error"
                title={t("loadTemplatesError")}
                message={error}
                isOffline={isOffline}
              />
            </div>
          )}

          {/* Template Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mt-12"
          >
            <div className="flex flex-wrap items-center justify-center gap-2">
              {[
                { key: "all", label: t("filterAll") },
                { key: "production", label: t("filterProduction") },
              ].map((filter) => (
                <button
                  key={filter.key}
                  onClick={() => setTemplateFilter(filter.key as "all" | "production")}
                  className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${templateFilter === filter.key
                    ? "bg-sky-500/20 text-sky-200 border border-sky-500/40"
                    : "border border-white/10 bg-white/5 text-slate-400 hover:text-slate-200"
                    }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            <div className="mt-8 grid gap-6 grid-cols-[repeat(auto-fill,minmax(320px,1fr))]">
              {loading ? (
                // Premium Skeleton Loader - matches new card design
                Array.from({ length: 8 }).map((_, i) => (
                  <div
                    key={i}
                    className="flex flex-col overflow-hidden rounded-[var(--card-radius)] border border-[var(--card-border)] bg-[var(--card-bg)]"
                    style={{ animationDelay: `${i * 75}ms` }}
                  >
                    {/* Thumbnail skeleton */}
                    <div className="m-[var(--card-padding)] aspect-[16/10] rounded-[var(--card-inner-radius)] bg-white/[0.04] animate-pulse" />

                    {/* Content skeleton */}
                    <div className="flex flex-col px-4 pb-4 space-y-3">
                      {/* Title */}
                      <div className="h-[18px] w-4/5 rounded-md bg-white/[0.06] animate-pulse" />
                      {/* Description lines */}
                      <div className="space-y-2">
                        <div className="h-3 w-full rounded bg-white/[0.04] animate-pulse" />
                        <div className="h-3 w-3/4 rounded bg-white/[0.03] animate-pulse" />
                      </div>
                      {/* Tags */}
                      <div className="flex gap-2 pt-3 border-t border-white/[0.04]">
                        <div className="h-5 w-14 rounded-full bg-white/[0.03] animate-pulse" />
                        <div className="h-5 w-18 rounded-full bg-white/[0.03] animate-pulse" />
                      </div>
                    </div>
                  </div>
                ))
              ) : filteredTemplates.length > 0 ? (
                filteredTemplates.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    onSelect={() => handleSelectTemplate(template)}
                    onOpenVersions={() => handleOpenVersions(template)}
                    isCreating={creating === template.id}
                  />
                ))
              ) : (
                <PageStatus
                  variant="empty"
                  title={t("noTemplates")}
                  className="col-span-full"
                />
              )}
            </div>
          </motion.div>

          {/* Blank Canvas Option */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-12 text-center"
          >
            <span className="text-sm text-slate-500">{t("or")}</span>
            <Link
              href="/canvas"
              className="ml-2 text-sm font-semibold text-sky-400 hover:text-sky-300"
            >
              {t("startBlankCanvas")} →
            </Link>
          </motion.div>

          {/* Creating Overlay */}
          {creating && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
              <div className="flex items-center gap-3 rounded-xl bg-slate-950 px-6 py-4 shadow-2xl">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
                <span className="text-sm text-slate-200">{t("creatingCanvas")}</span>
              </div>
            </div>
          )}

          <AnimatePresence>
            {showVersions && selectedTemplate && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
                onClick={() => setShowVersions(false)}
              >
                <motion.div
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.95, opacity: 0 }}
                  className="w-full max-w-2xl rounded-2xl border border-white/10 bg-slate-950 shadow-2xl overflow-hidden"
                  onClick={(event) => event.stopPropagation()}
                >
                  <div className="flex items-center justify-between p-6 border-b border-white/5">
                    <div>
                      <div className="text-xs uppercase tracking-widest text-slate-400">{t("templateVersions")}</div>
                      <div className="text-lg font-semibold text-white">{selectedTemplate.title}</div>
                    </div>
                    <button onClick={() => setShowVersions(false)} className="text-slate-400 hover:text-white">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
                    {versionsLoading && (
                      <div className="text-sm text-slate-400">{t("loadingVersions")}</div>
                    )}
                    {versionsError && (
                      <div className="text-sm text-rose-300">{versionsError}</div>
                    )}
                    {!versionsLoading && templateVersions.length === 0 && (
                      <div className="text-sm text-slate-500">{t("noVersions")}</div>
                    )}
                    {templateVersions.map((version) => {
                      const isCurrent = templateVersionIndex === version.version;
                      const seeds = getNarrativeSeeds(version.graph_data as unknown as Record<string, unknown>);
                      return (
                        <div
                          key={version.id}
                          className="rounded-xl border border-white/10 bg-slate-900/50 p-4"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-sm font-semibold text-slate-100">
                                v{version.version} {isCurrent ? `(${t("currentVersion")})` : ""}
                              </div>
                              <div className="text-xs text-slate-500 mt-1">
                                {new Date(version.created_at).toLocaleString()}
                              </div>
                              {version.notes && (
                                <div className="text-xs text-slate-400 mt-1">{version.notes}</div>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleUseVersion(version)}
                                disabled={versionAction === version.id}
                                className="inline-flex items-center gap-1 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[10px] uppercase tracking-widest text-sky-300 hover:bg-sky-500/20 disabled:opacity-50"
                              >
                                <Check className="h-3 w-3" />
                                {t("useVersion")}
                              </button>
                              <button
                                onClick={() => handleRevertVersion(version)}
                                disabled={versionAction === `revert-${version.id}` || isCurrent}
                                className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[10px] uppercase tracking-widest text-amber-300 hover:bg-amber-500/20 disabled:opacity-50"
                              >
                                <RefreshCcw className="h-3 w-3" />
                                {t("revertVersion")}
                              </button>
                            </div>
                          </div>
                          {seeds.hasSeeds && (
                            <div className="mt-3 rounded-lg border border-white/10 bg-slate-950/50 px-3 py-2 text-[11px] text-slate-300">
                              <div className="flex items-center justify-between text-[10px] uppercase tracking-widest text-slate-400">
                                <span>{t("narrativeSeeds")}</span>
                                <span>
                                  {t("beatSheet")}: {seeds.storyBeats.length} · {t("storyboard")}:{" "}
                                  {seeds.storyboardCards.length}
                                </span>
                              </div>
                              {seeds.beatSnippet && (
                                <div className="mt-2 line-clamp-1 text-[11px] text-slate-200">
                                  {t("beat")} 1: {seeds.beatSnippet}
                                </div>
                              )}
                              {seeds.storyboardSnippet && (
                                <div className="mt-1 line-clamp-1 text-[11px] text-slate-400">
                                  {t("shot")} 1: {seeds.storyboardSnippet}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  <div className="p-4 border-t border-white/10 text-[10px] text-slate-500 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <HistoryIcon className="h-3 w-3" />
                      <TemplateCardText tKey="latestHistory" />
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </AppShell>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
      </div>
    }>
      <HomePageContent />
    </Suspense>
  );
}
