import { translations, type Language } from "@/lib/translations";

export type ConfidenceLevel = "high" | "medium" | "low";

const REASON_CODE_KEYS: Record<string, keyof typeof translations.ko> = {
  "genre:romance": "reasonCodeGenreRomance",
  "genre:horror": "reasonCodeGenreHorror",
  "genre:action": "reasonCodeGenreAction",
  "genre:drama": "reasonCodeGenreDrama",
  "genre:comedy": "reasonCodeGenreComedy",
  "genre:thriller": "reasonCodeGenreThriller",
  "genre:fantasy": "reasonCodeGenreFantasy",
  "genre:sci-fi": "reasonCodeGenreSciFi",
  "genre:documentary": "reasonCodeGenreDocumentary",
  "genre:animation": "reasonCodeGenreAnimation",
  "auteur:bong": "reasonCodeAuteurBong",
  "auteur:epoch": "reasonCodeAuteurEpoch",
  "auteur:prism": "reasonCodeAuteurPrism",
  "auteur:voltage": "reasonCodeAuteurVoltage",
  "auteur:ghibli": "reasonCodeAuteurGhibli",
  "auteur:abyss": "reasonCodeAuteurAbyss",
  "auteur:yoon": "reasonCodeAuteurYoon",
  "auteur:wes_anderson": "reasonCodeAuteurWesAnderson",
  "auteur:seoyeon": "reasonCodeAuteurSeoyeon",
  "auteur:nova": "reasonCodeAuteurNova",
  "dimension:1D": "reasonCodeDimension1D",
  "dimension:2D": "reasonCodeDimension2D",
  "dimension:3D": "reasonCodeDimension3D",
  "dimension:4D": "reasonCodeDimension4D",
  "dimension:AD": "reasonCodeDimensionAD",
  "dimension:QC": "reasonCodeDimensionQC",
  "dimension:VEO": "reasonCodeDimensionVEO",
  "dimension:STORY": "reasonCodeDimensionSTORY",
  "dimension:SOUND": "reasonCodeDimensionSOUND",
  "dimension:AI": "reasonCodeDimensionAI",
  "shot:closeup": "reasonCodeShotCloseup",
  "shot:wide": "reasonCodeShotWide",
  "shot:establishing": "reasonCodeShotEstablishing",
  "shot:pov": "reasonCodeShotPov",
  "shot:tracking": "reasonCodeShotTracking",
  "shot:aerial": "reasonCodeShotAerial",
  "shot:handheld": "reasonCodeShotHandheld",
  "shot:static": "reasonCodeShotStatic",
  "shot:dolly": "reasonCodeShotDolly",
  "shot:crane": "reasonCodeShotCrane",
  "shot:action": "reasonCodeShotAction",
  "shot:dialogue": "reasonCodeShotDialogue",
  "shot:montage": "reasonCodeShotMontage",
  "context:worldbuilding": "reasonCodeContextWorldbuilding",
  "context:character": "reasonCodeContextCharacter",
  "context:setting": "reasonCodeContextSetting",
  "context:theme": "reasonCodeContextTheme",
  "context:mood": "reasonCodeContextMood",
  "context:narrative": "reasonCodeContextNarrative",
  "context:visual_style": "reasonCodeContextVisualStyle",
  "context:color_palette": "reasonCodeContextColorPalette",
  "context:pacing": "reasonCodeContextPacing",
  "context:workflow_preset": "reasonCodeContextWorkflowPreset",
  "history:frequently_used": "reasonCodeHistoryFrequentlyUsed",
  "history:recently_used": "reasonCodeHistoryRecentlyUsed",
  "history:workflow_pattern": "reasonCodeHistoryWorkflowPattern",
  "history:similar_project": "reasonCodeHistorySimilarProject",
};

export function getReasonCodeLabel(code: string, language: Language): string {
  const key = REASON_CODE_KEYS[code];
  if (!key) return code;
  return translations[language]?.[key] || code;
}

export function scoreToConfidenceLevel(score?: number): ConfidenceLevel {
  const value = score ?? 0;
  if (value >= 0.75) return "high";
  if (value >= 0.5) return "medium";
  return "low";
}

export function getConfidenceLabel(level: ConfidenceLevel, language: Language): string {
  const key =
    level === "high"
      ? "confidenceHigh"
      : level === "medium"
      ? "confidenceMedium"
      : "confidenceLow";
  return translations[language]?.[key] || level.toUpperCase();
}
