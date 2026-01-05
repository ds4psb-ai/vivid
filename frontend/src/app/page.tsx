"use client";

/**
 * Home Page - Refactored
 * 
 * Components extracted to _components/ folder
 * Main page: ~330 lines (down from 875)
 */

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Globe } from "lucide-react";
import { api, Template, TemplateVersion } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";
import { useSessionContext } from "@/contexts/SessionContext";
import PageStatus from "@/components/PageStatus";
import { isNetworkError, normalizeApiError } from "@/lib/errors";
import { localizeTemplate } from "@/lib/templateLocalization";
import { withViewTransition } from "@/lib/viewTransitions";
import AppShell from "@/components/AppShell";

// Local components
import { TemplateCard, isProductionTemplateGraph, VersionsModal } from "./_components";

function HomePageContent() {
  const router = useRouter();
  const { t, language, setLanguage } = useLanguage();
  const { isAuthenticated, isLoading: isSessionLoading } = useSessionContext();
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

  useEffect(() => {
    if (isSessionLoading) return;
    if (isAuthenticated) {
      router.replace("/studio");
    }
  }, [isAuthenticated, isSessionLoading, router]);

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
        isProductionTemplateGraph(template.graph_data)
      );
    }
    return localizedTemplates;
  }, [localizedTemplates, templateFilter]);

  useEffect(() => {
    api.listTemplates()
      .then((result) => { setTemplates(result); setIsOffline(false); })
      .catch((err) => { setError(normalizeApiError(err, t("loadTemplatesError"))); setIsOffline(isNetworkError(err)); })
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
      const updated = await api.updateTemplate(selectedTemplate.id, { graph_data: version.graph_data, notes: `revert to v${version.version}` });
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
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, ease: "easeOut" }}
              className="inline-flex items-center gap-2 rounded-full border border-[#4200FF]/20 bg-[#4200FF]/10 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-[#4200FF] backdrop-blur-md shadow-lg shadow-[#4200FF]/10 mb-8">
              <Sparkles className="h-3.5 w-3.5" /><span>{t("homeBadge")}</span>
            </motion.div>

            <motion.h1 initial={{ opacity: 0, y: 30, filter: "blur(10px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} transition={{ delay: 0.1, duration: 0.8, ease: "easeOut" }}
              className="font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white via-slate-200 to-slate-400 text-5xl md:text-7xl drop-shadow-2xl">
              {t("homeTitle")}
            </motion.h1>

            <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.8 }}
              className="mx-auto mt-6 max-w-2xl text-lg sm:text-xl text-slate-400 leading-relaxed font-light">
              {t("homeSubtitle")}
            </motion.p>

            {/* Language Switcher */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }} className="absolute top-0 right-0 hidden lg:block">
              <button onClick={() => setLanguage(language === "ko" ? "en" : "ko")}
                className="group flex items-center gap-2 rounded-full border border-white/5 bg-slate-900/50 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-slate-400 hover:bg-white/10 hover:text-white hover:border-white/10 transition-all backdrop-blur-md">
                <Globe className="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity" />
                {language === "ko" ? "English" : "한국어"}
              </button>
            </motion.div>
          </div>

          {/* Error */}
          {error && (
            <div className="mx-auto mt-8 max-w-md">
              <PageStatus variant="error" title={t("loadTemplatesError")} message={error} isOffline={isOffline} />
            </div>
          )}

          {/* Template Grid */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="mt-12">
            <div className="flex flex-wrap items-center justify-center gap-2">
              {[
                { key: "all", label: t("filterAll") },
                { key: "production", label: t("filterProduction") },
              ].map((filter) => (
                <button key={filter.key} onClick={() => setTemplateFilter(filter.key as "all" | "production")}
                  className={`rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${templateFilter === filter.key
                    ? "bg-sky-500/20 text-sky-200 border border-sky-500/40"
                    : "border border-white/10 bg-white/5 text-slate-400 hover:text-slate-200"}`}>
                  {filter.label}
                </button>
              ))}
            </div>

            <div className="mt-8 grid gap-6 grid-cols-[repeat(auto-fill,minmax(320px,1fr))]">
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="flex flex-col overflow-hidden rounded-[var(--card-radius)] border border-[var(--card-border)] bg-[var(--card-bg)]" style={{ animationDelay: `${i * 75}ms` }}>
                    <div className="m-[var(--card-padding)] aspect-[16/10] rounded-[var(--card-inner-radius)] bg-white/[0.04] animate-pulse" />
                    <div className="flex flex-col px-4 pb-4 space-y-3">
                      <div className="h-[18px] w-4/5 rounded-md bg-white/[0.06] animate-pulse" />
                      <div className="space-y-2">
                        <div className="h-3 w-full rounded bg-white/[0.04] animate-pulse" />
                        <div className="h-3 w-3/4 rounded bg-white/[0.03] animate-pulse" />
                      </div>
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
                <PageStatus variant="empty" title={t("noTemplates")} className="col-span-full" />
              )}
            </div>
          </motion.div>

          {/* Blank Canvas Option */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="mt-12 text-center">
            <span className="text-sm text-slate-500">{t("or")}</span>
            <Link href="/canvas" className="ml-2 text-sm font-semibold text-sky-400 hover:text-sky-300">
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

          {/* Versions Modal */}
          <AnimatePresence>
            {showVersions && selectedTemplate && (
              <VersionsModal
                template={selectedTemplate}
                versions={templateVersions}
                currentVersion={templateVersionIndex}
                isLoading={versionsLoading}
                error={versionsError}
                actionId={versionAction}
                onClose={() => setShowVersions(false)}
                onUseVersion={handleUseVersion}
                onRevertVersion={handleRevertVersion}
              />
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
