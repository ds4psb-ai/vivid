export const normalizeAllowedType = (value: string): string | null => {
  if (!value) return null;
  let cleaned = value.trim().toLowerCase();
  if (!cleaned) return null;
  if (cleaned.includes("/")) {
    const prefix = cleaned.split("/", 1)[0];
    if (prefix === "text" || prefix === "application") {
      cleaned = "doc";
    } else {
      cleaned = prefix;
    }
  }
  if (cleaned === "text" || cleaned === "application") {
    cleaned = "doc";
  }
  return cleaned;
};
