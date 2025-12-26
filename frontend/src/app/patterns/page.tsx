"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Layers,
  Search as SearchIcon,
  Filter,
  Hash,
  Link as LinkIcon,
} from "lucide-react";
import AppShell from "@/components/AppShell";
import { useLanguage } from "@/contexts/LanguageContext";
import { api, PatternItem, PatternTraceItem, PatternVersion } from "@/lib/api";
import { isAdminModeEnabled } from "@/lib/admin";
import { normalizeApiError } from "@/lib/errors";

type ActiveTab = "library" | "trace";

const PATTERN_TYPES = ["hook", "scene", "subtitle", "audio", "pacing"];
const STATUS_OPTIONS = ["validated", "proposed", "promoted"];

export default function PatternsPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<ActiveTab>("library");
  const [search, setSearch] = useState("");
  const [patternType, setPatternType] = useState("");
  const [status, setStatus] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [patterns, setPatterns] = useState<PatternItem[]>([]);
  const [trace, setTrace] = useState<PatternTraceItem[]>([]);
  const [patternVersions, setPatternVersions] = useState<PatternVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const adminModeEnabled = useMemo(() => isAdminModeEnabled(), []);

  const patternTypeLabel = (value: string) => {
    switch (value) {
      case "hook":
        return t("patternTypeHook");
      case "scene":
        return t("patternTypeScene");
      case "subtitle":
        return t("patternTypeSubtitle");
      case "audio":
        return t("patternTypeAudio");
      case "pacing":
        return t("patternTypePacing");
      default:
        return value;
    }
  };

  const statusLabel = (value: string) => {
    switch (value) {
      case "validated":
        return t("patternStatusValidated");
      case "proposed":
        return t("patternStatusProposed");
      case "promoted":
        return t("patternStatusPromoted");
      default:
        return value;
    }
  };

  useEffect(() => {
    let active = true;
    if (!adminModeEnabled) {
      setPatterns([]);
      setTrace([]);
      setPatternVersions([]);
      setIsLoading(false);
      setLoadError("admin-only");
      return () => {
        active = false;
      };
    }
    const loadData = async () => {
      setIsLoading(true);
      setLoadError(null);
      try {
        const versionsPromise = api.listPatternVersions(5);
        if (activeTab === "library") {
          const data = await api.listPatterns({
            search: search || undefined,
            pattern_type: patternType || undefined,
            status: status || undefined,
            limit: 80,
          });
          const versions = await versionsPromise;
          if (!active) return;
          setPatterns(data);
          setPatternVersions(versions);
        } else {
          const data = await api.listPatternTrace({
            search: search || undefined,
            pattern_type: patternType || undefined,
            source_id: sourceId || undefined,
            limit: 80,
          });
          const versions = await versionsPromise;
          if (!active) return;
          setTrace(data);
          setPatternVersions(versions);
        }
      } catch (err) {
        if (!active) return;
        setLoadError(normalizeApiError(err, t("patternLoadError")));
      } finally {
        if (active) setIsLoading(false);
      }
    };

    void loadData();
    return () => {
      active = false;
    };
  }, [adminModeEnabled, activeTab, search, patternType, status, sourceId, t]);

  const tabLabel = useMemo(
    () => (activeTab === "library" ? t("patternLibraryTab") : t("patternTraceTab")),
    [activeTab, t]
  );
  const latestVersion = patternVersions[0]?.version;
  const showAdminHint = (loadError || "").toLowerCase().includes("admin");

  return (
    <AppShell showTopBar={false}>
      <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 sm:mb-8"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500/20 to-amber-500/20">
                <Layers className="h-5 w-5 text-sky-300" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl">
                  {t("patternLibraryTitle")}
                </h1>
                <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">
                  {t("patternLibrarySubtitle")}
                </p>
              </div>
            </div>
            {latestVersion && (
              <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-[11px] font-semibold text-sky-200">
                {t("patternVersion")}: {latestVersion}
              </div>
            )}
          </motion.div>

          {loadError && !showAdminHint && (
            <div className="mb-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
              {loadError}
            </div>
          )}
          {showAdminHint && (
            <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
              {t("adminOnly")}
            </div>
          )}

          <div className="mb-4 flex flex-wrap items-center gap-2">
            <button
              onClick={() => setActiveTab("library")}
              className={`rounded-full px-4 py-2 text-xs font-semibold transition-colors ${activeTab === "library"
                  ? "bg-sky-500/20 text-sky-200"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
                }`}
            >
              {t("patternLibraryTab")}
            </button>
            <button
              onClick={() => setActiveTab("trace")}
              className={`rounded-full px-4 py-2 text-xs font-semibold transition-colors ${activeTab === "trace"
                  ? "bg-emerald-500/20 text-emerald-200"
                  : "bg-white/5 text-slate-300 hover:bg-white/10"
                }`}
            >
              {t("patternTraceTab")}
            </button>
            <span className="text-xs text-slate-500">{tabLabel}</span>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 flex flex-col gap-3 rounded-xl border border-white/10 bg-slate-950/50 p-4 sm:flex-row sm:items-center"
          >
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={activeTab === "library" ? t("searchPatterns") : t("searchTrace")}
                className="w-full rounded-lg border border-white/10 bg-slate-950/60 py-2 pl-9 pr-3 text-sm text-[var(--fg-0)] placeholder-slate-500 outline-none focus:border-[var(--accent)]"
                aria-label={activeTab === "library" ? t("searchPatterns") : t("searchTrace")}
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300">
                <Filter className="h-3 w-3" />
                <select
                  value={patternType}
                  onChange={(e) => setPatternType(e.target.value)}
                  className="bg-transparent text-xs text-slate-200 outline-none"
                >
                  <option value="">{t("allTypes")}</option>
                  {PATTERN_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {patternTypeLabel(type)}
                    </option>
                  ))}
                </select>
              </div>
              {activeTab === "library" && (
                <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300">
                  <Filter className="h-3 w-3" />
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="bg-transparent text-xs text-slate-200 outline-none"
                  >
                    <option value="">{t("allStatus")}</option>
                    {STATUS_OPTIONS.map((value) => (
                      <option key={value} value={value}>
                        {statusLabel(value)}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              {activeTab === "trace" && (
                <div className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300">
                  <Hash className="h-3 w-3" />
                  <input
                    value={sourceId}
                    onChange={(e) => setSourceId(e.target.value)}
                    placeholder={t("sourceIdFilter")}
                    className="w-36 bg-transparent text-xs text-slate-200 outline-none placeholder-slate-500"
                  />
                </div>
              )}
            </div>
          </motion.div>

          {activeTab === "library" ? (
            <div className="grid gap-4 md:grid-cols-2">
              {isLoading ? (
                <div className="col-span-full rounded-xl border border-white/10 bg-slate-950/50 px-4 py-6 text-sm text-slate-500">
                  {t("loading")}
                </div>
              ) : patterns.length === 0 ? (
                <div className="col-span-full rounded-xl border border-white/10 bg-slate-950/50 px-4 py-6 text-sm text-slate-500">
                  {t("noPatterns")}
                </div>
              ) : (
                patterns.map((pattern) => (
                  <div
                    key={pattern.id}
                    className="rounded-xl border border-white/10 bg-slate-950/60 p-4 transition-colors hover:border-white/20"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-100">{pattern.name}</div>
                        <div className="mt-1 text-xs text-slate-400">{pattern.description || "—"}</div>
                      </div>
                      <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2 py-0.5 text-[10px] font-semibold text-sky-200">
                        {patternTypeLabel(pattern.pattern_type)}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500">
                      <span>{t("patternStatus")}: {statusLabel(pattern.status)}</span>
                      <span>{pattern.updated_at.split("T")[0]}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {isLoading ? (
                <div className="rounded-xl border border-white/10 bg-slate-950/50 px-4 py-6 text-sm text-slate-500">
                  {t("loading")}
                </div>
              ) : trace.length === 0 ? (
                <div className="rounded-xl border border-white/10 bg-slate-950/50 px-4 py-6 text-sm text-slate-500">
                  {t("noPatternTrace")}
                </div>
              ) : (
                trace.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-xl border border-white/10 bg-slate-950/60 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-100">
                          {item.pattern_name || item.pattern_id}
                        </div>
                        <div className="mt-1 text-xs text-slate-400 font-mono">
                          {item.source_id}
                        </div>
                      </div>
                      {item.pattern_type && (
                        <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-200">
                          {patternTypeLabel(item.pattern_type)}
                        </span>
                      )}
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-3 text-[10px] text-slate-500">
                      {typeof item.weight === "number" && (
                        <span>{t("patternWeight")}: {item.weight.toFixed(2)}</span>
                      )}
                      {item.evidence_ref && (
                        <span className="inline-flex items-center gap-1">
                          <LinkIcon className="h-3 w-3" />
                          {item.evidence_ref}
                        </span>
                      )}
                      <span>{item.updated_at.split("T")[0]}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
