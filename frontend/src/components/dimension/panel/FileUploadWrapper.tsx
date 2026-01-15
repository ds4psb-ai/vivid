"use client";

/**
 * FileUploadWrapper - DimensionPanel.FileUpload compound component
 *
 * Wraps existing FileUploader component with dimension theming.
 */

import { type ComponentProps } from "react";
import FileUploader from "../FileUploader";
import { type ThemeColor as FileUploaderThemeColor } from "@/lib/dimension-theme";
import { useDimensionPanel } from "./DimensionPanelContext";

type FileUploaderProps = ComponentProps<typeof FileUploader>;

export interface FileUploadWrapperProps extends Omit<FileUploaderProps, "themeColor"> {
  /** Additional className */
  className?: string;
}

// Map tokens.ts ThemeColor to dimension-theme.ts ThemeColor
const THEME_COLOR_MAP: Record<string, FileUploaderThemeColor> = {
  violet: "violet",
  cyan: "cyan",
  emerald: "emerald",
  amber: "amber",
  rose: "rose",
  fuchsia: "fuchsia",
  indigo: "indigo",
  sky: "sky",
  purple: "violet", // Fallback
  red: "rose", // Fallback
};

export function FileUploadWrapper({
  className = "",
  ...props
}: FileUploadWrapperProps) {
  const { token, isLoading } = useDimensionPanel();

  // Map themeColor to FileUploader supported color
  const mappedThemeColor = THEME_COLOR_MAP[token.themeColor] || "emerald";

  return (
    <div className={className}>
      <FileUploader
        {...props}
        themeColor={mappedThemeColor}
        disabled={props.disabled || isLoading}
      />
    </div>
  );
}

FileUploadWrapper.displayName = "DimensionPanel.FileUpload";
