"use client";

/**
 * IntentSearchBar - Intent-Aware Search with Step Recommendations
 *
 * Phase 11: Workflow UX Innovation
 *
 * Provides intelligent search with:
 * - Keyword-based intent classification
 * - Workflow step recommendations
 * - Preset suggestions (거장, 장르, 플랫폼)
 * - Confidence-based ranking
 * - Quick action pills
 *
 * 2026 Pattern: "Intent-First Navigation"
 */

import {
  useState,
  useCallback,
  useMemo,
  useRef,
  useEffect,
  type KeyboardEvent,
  type ChangeEvent,
} from "react";
import {
  Search,
  Sparkles,
  Layers,
  Video,
  Music2,
  Palette,
  Brain,
  CheckCircle,
  Wand2,
  FileCode,
  ChevronRight,
  X,
  Clock,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { MegaAppId } from "./types";

// =============================================================================
// Types
// =============================================================================

export interface IntentSearchBarProps {
  /** Callback when a suggestion is selected */
  onSelect: (suggestion: IntentSuggestion) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Show recent searches */
  showRecent?: boolean;
  /** Show preset pills */
  showPresets?: boolean;
  /** Current app context (affects suggestions) */
  currentApp?: MegaAppId;
  /** Compact mode */
  compact?: boolean;
  /** Custom className */
  className?: string;
}

/** Intent classification result */
export interface IntentSuggestion {
  /** Unique ID */
  id: string;
  /** Matched intent type */
  intent: IntentType;
  /** Display label */
  label: string;
  /** Description */
  description: string;
  /** Confidence score (0-100) */
  confidence: number;
  /** Target app */
  targetApp: MegaAppId;
  /** Target step within app */
  targetStep?: string;
  /** Icon */
  icon: LucideIcon;
  /** Color class */
  colorClass: string;
  /** Matched keywords */
  matchedKeywords: string[];
  /** Is this a preset? */
  isPreset?: boolean;
  /** Preset category */
  presetCategory?: "auteur" | "genre" | "platform" | "general";
}

/** Intent types (aligned with backend) */
export type IntentType =
  | "generate_prompt"
  | "create_storyboard"
  | "generate_image"
  | "analyze_reference"
  | "quality_check"
  | "aesthetic_direct"
  | "persona_analyze"
  | "veo_generate"
  | "kling_generate"
  | "suno_generate"
  | "workflow_request"
  | "general";

// =============================================================================
// Intent Classification Data
// =============================================================================

/** Keyword patterns for intent classification */
interface IntentPattern {
  intent: IntentType;
  keywords: string[];
  targetApp: MegaAppId;
  targetStep?: string;
  label: string;
  description: string;
  icon: LucideIcon;
  colorClass: string;
  priority: number;
}

const INTENT_PATTERNS: IntentPattern[] = [
  // DNA Lab intents
  {
    intent: "analyze_reference",
    keywords: ["영상 분석", "레퍼런스", "분석", "vpe", "logic vector", "참조"],
    targetApp: "dna-lab",
    targetStep: "vpe",
    label: "영상 분석",
    description: "레퍼런스 영상에서 Logic Vector 추출",
    icon: Video,
    colorClass: "text-cyan-400",
    priority: 10,
  },
  {
    intent: "aesthetic_direct",
    keywords: ["미학", "스타일", "거장", "봉준호", "왕가위", "웡카위", "쿠브릭", "aesthetic", "ad"],
    targetApp: "dna-lab",
    targetStep: "ad",
    label: "미학 적용",
    description: "거장 스타일 및 미학 적용",
    icon: Palette,
    colorClass: "text-amber-400",
    priority: 10,
  },
  {
    intent: "persona_analyze",
    keywords: ["페르소나", "창작 dna", "mirror", "캐릭터", "아이덴티티"],
    targetApp: "dna-lab",
    targetStep: "mirror",
    label: "창작 DNA",
    description: "페르소나 DNA 분석",
    icon: Brain,
    colorClass: "text-violet-400",
    priority: 10,
  },
  {
    intent: "quality_check",
    keywords: ["품질", "검증", "qc", "퀄리티", "검수"],
    targetApp: "dna-lab",
    targetStep: "qc",
    label: "품질 검증",
    description: "최종 품질 검수",
    icon: CheckCircle,
    colorClass: "text-emerald-400",
    priority: 10,
  },

  // Story Engine intents
  {
    intent: "create_storyboard",
    keywords: ["스토리", "스토리보드", "내러티브", "구조", "설계", "story"],
    targetApp: "story-engine",
    targetStep: "story",
    label: "스토리 설계",
    description: "내러티브 구조 설계",
    icon: Layers,
    colorClass: "text-purple-400",
    priority: 10,
  },
  {
    intent: "generate_prompt",
    keywords: ["프롬프트", "연금술", "prompt", "alchemy"],
    targetApp: "story-engine",
    targetStep: "prompt",
    label: "프롬프트 연금술",
    description: "AI 프롬프트 생성",
    icon: Wand2,
    colorClass: "text-pink-400",
    priority: 10,
  },
  {
    intent: "workflow_request",
    keywords: ["시스템 프롬프트", "system prompt", "최종"],
    targetApp: "story-engine",
    targetStep: "system-prompt",
    label: "시스템 프롬프트",
    description: "최종 시스템 프롬프트 생성",
    icon: FileCode,
    colorClass: "text-cyan-400",
    priority: 10,
  },

  // Production intents
  {
    intent: "veo_generate",
    keywords: ["veo", "비디오", "영상 생성", "video", "구글"],
    targetApp: "production",
    targetStep: "veo",
    label: "VEO 3.1",
    description: "Google VEO 비디오 생성",
    icon: Video,
    colorClass: "text-emerald-400",
    priority: 10,
  },
  {
    intent: "kling_generate",
    keywords: ["kling", "클링", "립싱크", "시네마틱"],
    targetApp: "production",
    targetStep: "kling",
    label: "Kling 2.6",
    description: "시네마틱 비디오 & 립싱크",
    icon: Video,
    colorClass: "text-orange-400",
    priority: 10,
  },
  {
    intent: "suno_generate",
    keywords: ["suno", "음악", "music", "노래", "bgm"],
    targetApp: "production",
    targetStep: "suno",
    label: "Suno AI",
    description: "AI 음악 생성",
    icon: Music2,
    colorClass: "text-pink-400",
    priority: 10,
  },
];

/** Preset suggestions */
interface PresetSuggestion {
  id: string;
  label: string;
  description: string;
  category: "auteur" | "genre" | "platform" | "general";
  keywords: string[];
  icon: LucideIcon;
  colorClass: string;
}

const PRESETS: PresetSuggestion[] = [
  // Auteur presets
  {
    id: "preset_bong",
    label: "봉준호 스타일",
    description: "사회 비판적 스릴러, 장르 혼합",
    category: "auteur",
    keywords: ["봉준호", "기생충", "스릴러"],
    icon: Sparkles,
    colorClass: "text-amber-400",
  },
  {
    id: "preset_wong",
    label: "왕가위 스타일",
    description: "몽환적 색감, 슬로우 모션",
    category: "auteur",
    keywords: ["왕가위", "화양연화", "멜랑콜리"],
    icon: Sparkles,
    colorClass: "text-pink-400",
  },
  {
    id: "preset_kubrick",
    label: "큐브릭 스타일",
    description: "대칭 구도, 완벽주의적 디테일",
    category: "auteur",
    keywords: ["큐브릭", "샤이닝", "시네마틱"],
    icon: Sparkles,
    colorClass: "text-cyan-400",
  },

  // Platform presets
  {
    id: "preset_youtube",
    label: "YouTube 숏폼",
    description: "빠른 컷, 훅 강조, 세로 포맷",
    category: "platform",
    keywords: ["유튜브", "shorts", "숏폼"],
    icon: Video,
    colorClass: "text-red-400",
  },
  {
    id: "preset_tiktok",
    label: "TikTok 스타일",
    description: "트렌디, 빠른 전환, 음악 싱크",
    category: "platform",
    keywords: ["틱톡", "tiktok", "릴스"],
    icon: Video,
    colorClass: "text-slate-400",
  },

  // General presets
  {
    id: "preset_cinematic",
    label: "시네마틱 일반",
    description: "영화적 퀄리티, 16:9, 고품질",
    category: "general",
    keywords: ["시네마틱", "영화", "cinematic"],
    icon: Video,
    colorClass: "text-violet-400",
  },
];

// =============================================================================
// Classification Logic
// =============================================================================

/**
 * Classify user input and return sorted suggestions
 */
function classifyIntent(
  query: string,
  currentApp?: MegaAppId
): IntentSuggestion[] {
  if (!query.trim()) return [];

  const normalizedQuery = query.toLowerCase().trim();
  const suggestions: IntentSuggestion[] = [];

  // Match against intent patterns
  for (const pattern of INTENT_PATTERNS) {
    const matchedKeywords = pattern.keywords.filter((kw) =>
      normalizedQuery.includes(kw.toLowerCase())
    );

    if (matchedKeywords.length > 0) {
      // Calculate confidence based on match quality
      const confidence = Math.min(
        100,
        matchedKeywords.length * 30 + (currentApp === pattern.targetApp ? 20 : 0)
      );

      suggestions.push({
        id: `intent_${pattern.intent}_${pattern.targetStep || "default"}`,
        intent: pattern.intent,
        label: pattern.label,
        description: pattern.description,
        confidence,
        targetApp: pattern.targetApp,
        targetStep: pattern.targetStep,
        icon: pattern.icon,
        colorClass: pattern.colorClass,
        matchedKeywords,
        isPreset: false,
      });
    }
  }

  // Match against presets
  for (const preset of PRESETS) {
    const matchedKeywords = preset.keywords.filter((kw) =>
      normalizedQuery.includes(kw.toLowerCase())
    );

    if (matchedKeywords.length > 0) {
      suggestions.push({
        id: preset.id,
        intent: "aesthetic_direct",
        label: preset.label,
        description: preset.description,
        confidence: matchedKeywords.length * 25,
        targetApp: "dna-lab",
        targetStep: "ad",
        icon: preset.icon,
        colorClass: preset.colorClass,
        matchedKeywords,
        isPreset: true,
        presetCategory: preset.category,
      });
    }
  }

  // Sort by confidence (descending)
  return suggestions.sort((a, b) => b.confidence - a.confidence).slice(0, 6);
}

/**
 * Get quick preset pills for display
 */
function getQuickPresets(): PresetSuggestion[] {
  return PRESETS.filter((p) => p.category === "auteur" || p.category === "general").slice(0, 4);
}

// =============================================================================
// Sub-Components
// =============================================================================

/**
 * Suggestion item in dropdown
 */
function SuggestionItem({
  suggestion,
  isHighlighted,
  onClick,
}: {
  suggestion: IntentSuggestion;
  isHighlighted: boolean;
  onClick: () => void;
}) {
  const Icon = suggestion.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-3 py-2.5 text-left rounded-lg transition-colors",
        isHighlighted ? "bg-white/10" : "hover:bg-white/5"
      )}
    >
      <div
        className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0",
          suggestion.colorClass.replace("text-", "bg-").replace("-400", "-500/20")
        )}
      >
        <Icon className={cn("w-4 h-4", suggestion.colorClass)} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-white text-sm">{suggestion.label}</span>
          {suggestion.isPreset && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-400">
              프리셋
            </span>
          )}
        </div>
        <p className="text-xs text-white/50 truncate">{suggestion.description}</p>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        <span className="text-[10px] text-white/30 uppercase">
          {suggestion.targetApp.replace("-", " ")}
        </span>
        <ChevronRight className="w-4 h-4 text-white/30" />
      </div>
    </button>
  );
}

/**
 * Quick preset pill button
 */
function PresetPill({
  preset,
  onClick,
}: {
  preset: PresetSuggestion;
  onClick: () => void;
}) {
  const Icon = preset.icon;

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 px-3 py-1.5 rounded-full",
        "bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20",
        "transition-colors text-sm"
      )}
    >
      <Icon className={cn("w-3.5 h-3.5", preset.colorClass)} />
      <span className="text-white/70">{preset.label}</span>
    </button>
  );
}

/**
 * Recent search item
 */
function RecentSearchItem({
  query,
  onClick,
  onRemove,
}: {
  query: string;
  onClick: () => void;
  onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 hover:bg-white/5 rounded-lg group">
      <Clock className="w-4 h-4 text-white/30" />
      <button
        type="button"
        onClick={onClick}
        className="flex-1 text-left text-sm text-white/60 hover:text-white/80"
      >
        {query}
      </button>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onRemove();
        }}
        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-white/10 rounded transition-opacity"
      >
        <X className="w-3 h-3 text-white/40" />
      </button>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

/**
 * IntentSearchBar - Intent-aware search with recommendations
 *
 * @example
 * ```tsx
 * <IntentSearchBar
 *   onSelect={(suggestion) => {
 *     router.push(`/${suggestion.targetApp}?step=${suggestion.targetStep}`);
 *   }}
 *   currentApp="dna-lab"
 *   showPresets
 *   showRecent
 * />
 * ```
 */
export function IntentSearchBar({
  onSelect,
  placeholder = "무엇을 만들고 싶으세요? (예: 봉준호 스타일 스릴러)",
  showRecent = true,
  showPresets = true,
  currentApp,
  compact = false,
  className,
}: IntentSearchBarProps) {
  const [query, setQuery] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("intent_recent_searches");
      if (stored) {
        try {
          setRecentSearches(JSON.parse(stored).slice(0, 5));
        } catch {
          // Ignore parse errors
        }
      }
    }
  }, []);

  // Classify intent based on query
  const suggestions = useMemo(
    () => classifyIntent(query, currentApp),
    [query, currentApp]
  );

  // Quick presets for pills
  const quickPresets = useMemo(() => getQuickPresets(), []);

  // Show dropdown when focused and has content
  const showDropdown = isFocused && (query.length > 0 || showRecent || showPresets);

  // Handle selection
  const handleSelect = useCallback(
    (suggestion: IntentSuggestion) => {
      // Save to recent searches
      if (query.trim()) {
        const newRecent = [
          query.trim(),
          ...recentSearches.filter((s) => s !== query.trim()),
        ].slice(0, 5);
        setRecentSearches(newRecent);
        localStorage.setItem("intent_recent_searches", JSON.stringify(newRecent));
      }

      onSelect(suggestion);
      setQuery("");
      setIsFocused(false);
      inputRef.current?.blur();
    },
    [query, recentSearches, onSelect]
  );

  // Handle preset pill click
  const handlePresetClick = useCallback(
    (preset: PresetSuggestion) => {
      const suggestion: IntentSuggestion = {
        id: preset.id,
        intent: "aesthetic_direct",
        label: preset.label,
        description: preset.description,
        confidence: 100,
        targetApp: "dna-lab",
        targetStep: "ad",
        icon: preset.icon,
        colorClass: preset.colorClass,
        matchedKeywords: preset.keywords,
        isPreset: true,
        presetCategory: preset.category,
      };
      handleSelect(suggestion);
    },
    [handleSelect]
  );

  // Handle recent search click
  const handleRecentClick = useCallback((searchQuery: string) => {
    setQuery(searchQuery);
    inputRef.current?.focus();
  }, []);

  // Remove recent search
  const handleRemoveRecent = useCallback(
    (searchQuery: string) => {
      const newRecent = recentSearches.filter((s) => s !== searchQuery);
      setRecentSearches(newRecent);
      localStorage.setItem("intent_recent_searches", JSON.stringify(newRecent));
    },
    [recentSearches]
  );

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!showDropdown) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setHighlightedIndex((prev) =>
            Math.min(prev + 1, suggestions.length - 1)
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setHighlightedIndex((prev) => Math.max(prev - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (suggestions[highlightedIndex]) {
            handleSelect(suggestions[highlightedIndex]);
          }
          break;
        case "Escape":
          e.preventDefault();
          setIsFocused(false);
          inputRef.current?.blur();
          break;
      }
    },
    [showDropdown, suggestions, highlightedIndex, handleSelect]
  );

  // Handle input change
  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setHighlightedIndex(0);
  }, []);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsFocused(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Search Input */}
      <div
        className={cn(
          "relative flex items-center gap-2 rounded-xl border transition-all",
          isFocused
            ? "bg-white/10 border-white/20 ring-2 ring-white/10"
            : "bg-white/5 border-white/10 hover:bg-white/[0.07]",
          compact ? "px-3 py-2" : "px-4 py-3"
        )}
      >
        <Search className={cn("flex-shrink-0 text-white/40", compact ? "w-4 h-4" : "w-5 h-5")} />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleChange}
          onFocus={() => setIsFocused(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={cn(
            "flex-1 bg-transparent text-white placeholder-white/40 outline-none",
            compact ? "text-sm" : "text-base"
          )}
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-4 h-4 text-white/40" />
          </button>
        )}
        <div className="flex items-center gap-1 text-white/30">
          <Zap className="w-4 h-4" />
          <span className="text-xs">AI</span>
        </div>
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute z-50 top-full left-0 right-0 mt-2 p-2 rounded-xl bg-[#0F0F1A] border border-white/10 shadow-xl">
          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="mb-2">
              <div className="px-3 py-1.5 text-[10px] font-medium text-white/40 uppercase tracking-wider">
                추천
              </div>
              {suggestions.map((suggestion, index) => (
                <SuggestionItem
                  key={suggestion.id}
                  suggestion={suggestion}
                  isHighlighted={index === highlightedIndex}
                  onClick={() => handleSelect(suggestion)}
                />
              ))}
            </div>
          )}

          {/* Quick Presets */}
          {showPresets && !query && (
            <div className="mb-2">
              <div className="px-3 py-1.5 text-[10px] font-medium text-white/40 uppercase tracking-wider">
                빠른 시작
              </div>
              <div className="flex flex-wrap gap-2 px-2 py-2">
                {quickPresets.map((preset) => (
                  <PresetPill
                    key={preset.id}
                    preset={preset}
                    onClick={() => handlePresetClick(preset)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recent Searches */}
          {showRecent && !query && recentSearches.length > 0 && (
            <div>
              <div className="px-3 py-1.5 text-[10px] font-medium text-white/40 uppercase tracking-wider">
                최근 검색
              </div>
              {recentSearches.map((search) => (
                <RecentSearchItem
                  key={search}
                  query={search}
                  onClick={() => handleRecentClick(search)}
                  onRemove={() => handleRemoveRecent(search)}
                />
              ))}
            </div>
          )}

          {/* Empty state */}
          {query && suggestions.length === 0 && (
            <div className="px-3 py-4 text-center text-white/40 text-sm">
              &ldquo;{query}&rdquo;에 대한 결과가 없습니다.
              <br />
              <span className="text-xs">다른 키워드로 검색해보세요.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default IntentSearchBar;
