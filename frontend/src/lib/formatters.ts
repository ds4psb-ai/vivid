export const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

export const formatDateTime = (
  value: string | number | Date | null | undefined,
  locale?: string,
  options?: Intl.DateTimeFormatOptions,
): string | null => {
  if (value === null || value === undefined || value === "") return null;
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  if (options) return date.toLocaleString(locale, options);
  if (locale) return date.toLocaleString(locale);
  return date.toLocaleString();
};

export const formatNumber = (
  value: number | null | undefined,
  locale?: string,
  options?: Intl.NumberFormatOptions,
  fallback = "-",
): string => {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback;
  return new Intl.NumberFormat(locale, options).format(value);
};
