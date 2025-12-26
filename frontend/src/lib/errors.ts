export const normalizeApiError = (error: unknown, fallback: string): string => {
  if (error && typeof error === "object") {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail.trim();
    }
  }

  const message =
    typeof error === "string"
      ? error
      : error instanceof Error
        ? error.message
        : "";

  const normalized = message.trim();
  if (!normalized) return fallback;

  const lowered = normalized.toLowerCase();
  const genericPatterns = [
    "failed to reach api",
    "failed to fetch",
    "network error",
    "networkerror",
    "request failed",
  ];
  if (genericPatterns.some((pattern) => lowered.includes(pattern))) {
    return fallback;
  }

  return normalized;
};
