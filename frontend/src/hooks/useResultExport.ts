"use client";

import { useState, useCallback } from "react";

/**
 * Return type for useResultExport hook.
 */
export interface UseResultExportReturn {
  /**
   * Export data as a downloadable JSON file.
   * @param data - Object to export
   * @param filename - Optional filename (default: result-{timestamp}.json)
   */
  exportJSON: (data: object, filename?: string) => void;

  /**
   * Copy text to clipboard with fallback for older browsers.
   * @param text - Text to copy
   * @returns Promise that resolves to true if successful
   */
  copyToClipboard: (text: string) => Promise<boolean>;

  /**
   * Copy object as formatted JSON to clipboard.
   * @param data - Object to copy
   * @returns Promise that resolves to true if successful
   */
  copyJSON: (data: object) => Promise<boolean>;

  /**
   * Download content as a file.
   * @param content - File content
   * @param filename - Filename with extension
   * @param mimeType - MIME type (default: text/plain)
   */
  downloadFile: (content: string, filename: string, mimeType?: string) => void;

  /**
   * True for 2 seconds after successful copy.
   */
  isCopied: boolean;

  /**
   * Error message if copy failed.
   */
  copyError: string | null;
}

/**
 * Generate a timestamp string for filenames.
 */
function getTimestamp(): string {
  const now = new Date();
  return now
    .toISOString()
    .replace(/[:.]/g, "-")
    .slice(0, 19);
}

/**
 * Hook for exporting and copying operation results.
 *
 * @example
 * ```tsx
 * const { exportJSON, copyToClipboard, isCopied } = useResultExport();
 *
 * // Export result as JSON file
 * exportJSON(result, 'my-prompt.json');
 *
 * // Copy prompt text to clipboard
 * await copyToClipboard(result.prompt);
 *
 * // Show feedback
 * {isCopied && <span>복사됨!</span>}
 * ```
 */
export function useResultExport(): UseResultExportReturn {
  const [isCopied, setIsCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);

  /**
   * Export data as downloadable JSON file.
   */
  const exportJSON = useCallback((data: object, filename?: string) => {
    const finalFilename = filename || `result-${getTimestamp()}.json`;
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = finalFilename;
    link.style.display = "none";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Clean up the URL object
    setTimeout(() => URL.revokeObjectURL(url), 100);
  }, []);

  /**
   * Copy text to clipboard with modern API and fallback.
   */
  const copyToClipboard = useCallback(async (text: string): Promise<boolean> => {
    setCopyError(null);

    try {
      // Modern Clipboard API
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
        return true;
      }

      // Fallback for older browsers or non-secure contexts
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.top = "-9999px";
      textarea.setAttribute("readonly", "");

      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();

      const success = document.execCommand("copy");
      document.body.removeChild(textarea);

      if (success) {
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
        return true;
      } else {
        setCopyError("복사에 실패했습니다.");
        return false;
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "클립보드 접근에 실패했습니다.";
      setCopyError(errorMessage);
      console.error("Clipboard copy failed:", err);
      return false;
    }
  }, []);

  /**
   * Copy object as formatted JSON to clipboard.
   */
  const copyJSON = useCallback(
    async (data: object): Promise<boolean> => {
      const jsonString = JSON.stringify(data, null, 2);
      return copyToClipboard(jsonString);
    },
    [copyToClipboard]
  );

  /**
   * Download content as a file with specified MIME type.
   */
  const downloadFile = useCallback(
    (content: string, filename: string, mimeType: string = "text/plain") => {
      const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.style.display = "none";

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up the URL object
      setTimeout(() => URL.revokeObjectURL(url), 100);
    },
    []
  );

  return {
    exportJSON,
    copyToClipboard,
    copyJSON,
    downloadFile,
    isCopied,
    copyError,
  };
}

export default useResultExport;
