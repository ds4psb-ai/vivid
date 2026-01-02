const NETWORK_PATTERNS = [
  "failed to reach api",
  "failed to fetch",
  "network error",
  "networkerror",
  "request failed",
];

// Technical error patterns that should be hidden from users
const TECHNICAL_ERROR_PATTERNS = [
  "importerror",
  "syntaxerror",
  "typeerror",
  "valueerror",
  "keyerror",
  "attributeerror",
  "modulenotfounderror",
  "filenotfounderror",
  "traceback",
  "exception:",
  "internal server error",
  "500:",
];

const getErrorMessage = (error: unknown): string => {
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message;
  if (error && typeof error === "object") {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
  }
  return "";
};

export const isNetworkError = (error: unknown): boolean => {
  const normalized = getErrorMessage(error).trim();
  if (!normalized) return false;
  const lowered = normalized.toLowerCase();
  return NETWORK_PATTERNS.some((pattern) => lowered.includes(pattern));
};

const isTechnicalError = (message: string): boolean => {
  const lowered = message.toLowerCase();
  return TECHNICAL_ERROR_PATTERNS.some((pattern) => lowered.includes(pattern));
};

export const normalizeApiError = (error: unknown, fallback: string): string => {
  if (error && typeof error === "object") {
    const detail = (error as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) {
      // Hide technical errors from users
      if (isTechnicalError(detail)) {
        return fallback;
      }
      return detail.trim();
    }
  }

  const normalized = getErrorMessage(error).trim();
  if (!normalized) return fallback;
  if (isNetworkError(error)) return fallback;
  if (isTechnicalError(normalized)) return fallback;
  return normalized;
};
