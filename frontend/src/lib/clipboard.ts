export const canUseClipboard = (): boolean => {
  if (typeof navigator === "undefined") return false;
  return typeof navigator.clipboard?.writeText === "function";
};

export const copyToClipboard = async (value: string): Promise<boolean> => {
  if (!value || !canUseClipboard()) return false;
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
};
