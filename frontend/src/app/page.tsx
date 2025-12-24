"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Film,
  Palette,
  Music,
  Zap,
  Coffee,
  ArrowRight,
  History as HistoryIcon,
  X,
  Check,
  RefreshCcw,
  Globe,
} from "lucide-react";
import { api, Template, TemplateVersion } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { translations } from "@/lib/translations";

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
};

const AUTEUR_COLORS: Record<string, { gradient: string; glow: string }> = {
  "tmpl-auteur-bong": { gradient: "from-sky-400 to-blue-600", glow: "shadow-sky-500/30" },
  "tmpl-auteur-park": { gradient: "from-rose-400 to-pink-600", glow: "shadow-rose-500/30" },
  "tmpl-auteur-shinkai": { gradient: "from-amber-300 to-orange-500", glow: "shadow-amber-500/30" },
  "tmpl-auteur-leejunho": { gradient: "from-violet-400 to-purple-600", glow: "shadow-violet-500/30" },
  "tmpl-auteur-na": { gradient: "from-emerald-400 to-teal-600", glow: "shadow-emerald-500/30" },
  "tmpl-auteur-hong": { gradient: "from-slate-400 to-zinc-600", glow: "shadow-slate-500/30" },
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
  const Icon = AUTEUR_ICONS[template.slug] || Sparkles;
  const colors = AUTEUR_COLORS[template.slug] || { gradient: "from-slate-400 to-slate-600", glow: "shadow-slate-500/20" };
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.div
      whileHover={{ scale: 1.03, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      className={`group relative w-full h-80 rounded-2xl border border-white/10 bg-slate-950/60 p-6 text-left backdrop-blur-xl transition-all hover:border-white/20 ${colors.glow} shadow-xl overflow-hidden`}
    >
      {/* Motion Poster Background on Hover */}
      <AnimatePresence>
        {isHovered && template.preview_video_url && (
          <div className="absolute inset-0 z-0 bg-black overflow-hidden">
            {/* Ken Burns Effect Image */}
            <motion.img
              src={template.preview_video_url}
              alt={template.title}
              initial={{ scale: 1, opacity: 0 }}
              animate={{ scale: 1.1, opacity: 0.8 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 3, ease: "linear" }}
              className="h-full w-full object-cover"
            />
            {/* Cinematic Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent" />
          </div>
        )}
      </AnimatePresence>

      {/* Gradient Accent (Static) */}
      {!isHovered && (
        <div className={`absolute inset-0 z-0 rounded-2xl bg-gradient-to-br ${colors.gradient} opacity-5 group-hover:opacity-10 transition-opacity`} />
      )}

      {/* Content Container */}
      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <div className="flex-1">
          <div className={`inline-flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${colors.gradient} shadow-lg mb-4`}>
            <Icon className="h-6 w-6 text-white" strokeWidth={2} />
          </div>

          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold text-slate-100 group-hover:text-white transition-colors">
              {template.title}
            </h3>
            {template.version !== undefined && (
              <span className="text-[10px] uppercase tracking-widest text-slate-400">
                v{template.version}
              </span>
            )}
          </div>
          <p className="mt-2 text-sm text-slate-400 line-clamp-3 group-hover:text-slate-200 transition-colors">
            {template.description}
          </p>
        </div>

        {/* Footer */}
        <div>
          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-4">
            {template.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-medium text-slate-400 backdrop-blur-md">
                {tag}
              </span>
            ))}
          </div>

          <div className="flex items-center justify-between">
            {/* CTA */}
            <div className="flex items-center gap-2 text-sm font-semibold text-sky-400 opacity-0 transform translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300">
              <TemplateCardText tKey="createCanvas" /> <ArrowRight className="h-4 w-4" />
            </div>
            <button
              onClick={(event) => {
                event.stopPropagation();
                onOpenVersions();
              }}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] uppercase tracking-widest text-slate-300 hover:bg-white/10"
            >
              <TemplateCardText tKey="versions" />
            </button>
          </div>
        </div>
      </div>
      {isCreating && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/70 text-sm font-semibold text-slate-100">
          <TemplateCardText tKey="creating" />
        </div>
      )}
    </motion.div>
  );
}

export default function HomePage() {
  const router = useRouter();
  const { t, language, setLanguage } = useLanguage();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [templateVersions, setTemplateVersions] = useState<TemplateVersion[]>([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [versionAction, setVersionAction] = useState<string | null>(null);

  const templateVersionIndex = useMemo(() => {
    if (!selectedTemplate?.version) return null;
    return selectedTemplate.version;
  }, [selectedTemplate]);

  useEffect(() => {
    api.listTemplates()
      .then(setTemplates)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectTemplate = async (template: Template) => {
    setCreating(template.id);
    try {
      const canvas = await api.createCanvasFromTemplate(template.id, `${template.title} - My Project`);
      router.push(`/canvas?id=${canvas.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create canvas");
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
      setVersionsError(err instanceof Error ? err.message : "Failed to load versions");
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
      router.push(`/canvas?id=${canvas.id}`);
    } catch (err) {
      setVersionsError(err instanceof Error ? err.message : "Failed to create canvas");
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
      setVersionsError(err instanceof Error ? err.message : "Failed to revert template");
    } finally {
      setVersionAction(null);
    }
  };

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 rounded-full bg-sky-500/10 px-4 py-1.5 text-sm font-medium text-sky-400"
          >
            <Sparkles className="h-4 w-4" />
            Node Canvas Studio
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-6 font-bold tracking-tight text-slate-100 sm:text-5xl"
          >
            {language === "ko" ? "거장의 스타일로 시작하세요" : "Start with a Master's Style"}
          </motion.div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="mx-auto mt-4 max-w-xl text-lg text-slate-400"
          >
            {language === "ko"
              ? "6명의 거장 템플릿 중 하나를 선택하면, 해당 스타일의 캡슐 노드가 적용된 캔버스로 바로 시작합니다."
              : "Choose from 6 auteur templates to instantly start with a canvas styled by their unique capsule nodes."}
          </motion.p>

          {/* Language Switcher */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="absolute top-6 right-6"
          >
            <button
              onClick={() => setLanguage(language === "ko" ? "en" : "ko")}
              className="flex items-center gap-2 rounded-full border border-white/10 bg-slate-900/50 px-3 py-1.5 text-xs font-medium text-slate-400 hover:bg-white/5 hover:text-white transition-colors"
            >
              <Globe className="h-3 w-3" />
              {language === "ko" ? "English" : "한국어"}
            </button>
          </motion.div>
        </div>

        {/* Error */}
        {error && (
          <div className="mx-auto mt-8 max-w-md rounded-lg bg-rose-500/10 px-4 py-3 text-center text-sm text-rose-200">
            {t("error")}: {error}
          </div>
        )}

        {/* Template Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
        >
          {loading ? (
            // Skeleton
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-64 animate-pulse rounded-2xl bg-slate-800/50" />
            ))
          ) : templates.length > 0 ? (
            templates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onSelect={() => handleSelectTemplate(template)}
                onOpenVersions={() => handleOpenVersions(template)}
                isCreating={creating === template.id}
              />
            ))
          ) : (
            <div className="col-span-full text-center text-slate-500">
              {language === "ko"
                ? "템플릿이 없습니다. 백엔드에서 시드 데이터를 실행해주세요."
                : "No templates found. Please run backend seed data."}
            </div>
          )}
        </motion.div>

        {/* Blank Canvas Option */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-12 text-center"
        >
          <span className="text-sm text-slate-500">{language === "ko" ? "또는" : "or"}</span>
          <Link
            href="/canvas"
            className="ml-2 text-sm font-semibold text-sky-400 hover:text-sky-300"
          >
            {language === "ko" ? "빈 캔버스로 시작하기 →" : "Start with Blank Canvas →"}
          </Link>
        </motion.div>

        {/* Creating Overlay */}
        {creating && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="flex items-center gap-3 rounded-xl bg-slate-950 px-6 py-4 shadow-2xl">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
              <span className="text-sm text-slate-200">캔버스를 생성하고 있습니다...</span>
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
                    <div className="text-xs uppercase tracking-widest text-slate-400">Template Versions</div>
                    <div className="text-lg font-semibold text-white">{selectedTemplate.title}</div>
                  </div>
                  <button onClick={() => setShowVersions(false)} className="text-slate-400 hover:text-white">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
                  {versionsLoading && (
                    <div className="text-sm text-slate-400">Loading versions...</div>
                  )}
                  {versionsError && (
                    <div className="text-sm text-rose-300">{versionsError}</div>
                  )}
                  {!versionsLoading && templateVersions.length === 0 && (
                    <div className="text-sm text-slate-500">No versions yet.</div>
                  )}
                  {templateVersions.map((version) => {
                    const isCurrent = templateVersionIndex === version.version;
                    return (
                      <div
                        key={version.id}
                        className="rounded-xl border border-white/10 bg-slate-900/50 p-4"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="text-sm font-semibold text-slate-100">
                              v{version.version} {isCurrent ? "(current)" : ""}
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
                              Use
                            </button>
                            <button
                              onClick={() => handleRevertVersion(version)}
                              disabled={versionAction === `revert-${version.id}` || isCurrent}
                              className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-[10px] uppercase tracking-widest text-amber-300 hover:bg-amber-500/20 disabled:opacity-50"
                            >
                              <RefreshCcw className="h-3 w-3" />
                              Revert
                            </button>
                          </div>
                        </div>
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
  );
}
