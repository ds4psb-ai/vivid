type TextSource = Record<string, unknown>;

const coerceText = (value: unknown): string | null => {
  if (typeof value === "string") {
    const cleaned = value.trim();
    return cleaned ? cleaned : null;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : null;
  }
  return null;
};

const pickText = (source: TextSource, keys: string[]): string | null => {
  for (const key of keys) {
    const text = coerceText(source[key]);
    if (text) return text;
  }
  return null;
};

export const getBeatLabel = (beat: unknown): string | null => {
  if (!beat) return null;
  if (typeof beat === "string") return coerceText(beat);
  if (typeof beat === "object") {
    const entry = beat as TextSource;
    return (
      pickText(entry, ["note", "summary", "text"]) ??
      pickText(entry, ["beat", "beat_id", "id"])
    );
  }
  return null;
};

export const getStoryboardLabel = (card: unknown): string | null => {
  if (!card) return null;
  if (typeof card === "string") return coerceText(card);
  if (typeof card === "object") {
    const entry = card as TextSource;
    const label =
      pickText(entry, ["note", "description", "summary"]) ??
      pickText(entry, ["composition", "shot"]);
    if (label) return label;
    const numericShot = entry.shot;
    if (typeof numericShot === "number" && Number.isFinite(numericShot)) {
      return `Shot ${numericShot}`;
    }
  }
  return null;
};

export const getStoryboardShotType = (card: unknown): string | null => {
  if (!card || typeof card !== "object") return null;
  const entry = card as TextSource;
  return (
    pickText(entry, ["shot_type"]) ??
    pickText(entry, ["shot"]) ??
    pickText(entry, ["composition"])
  );
};
