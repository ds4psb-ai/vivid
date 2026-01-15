"use client";

/**
 * Textarea - DimensionPanel.Textarea compound component
 *
 * Unified textarea with dimension-themed focus ring and optional auto-resize.
 */

import {
  forwardRef,
  useId,
  useEffect,
  useRef,
  type TextareaHTMLAttributes,
} from "react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface TextareaProps
  extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className"> {
  /** Field label */
  label: string;
  /** Error message */
  error?: string;
  /** Helper text below input */
  helperText?: string;
  /** Show character count */
  showCount?: boolean;
  /** Auto-resize height based on content */
  autoResize?: boolean;
  /** Min height (default: 8rem) */
  minHeight?: string;
  /** Max height for auto-resize (default: 16rem) */
  maxHeight?: string;
  /** Additional className */
  className?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea(
    {
      label,
      error,
      helperText,
      showCount = false,
      autoResize = false,
      minHeight = "8rem",
      maxHeight = "16rem",
      maxLength,
      value,
      className = "",
      id: providedId,
      disabled,
      onChange,
      ...props
    },
    ref
  ) {
    const { styles, isLoading } = useDimensionPanel();
    const generatedId = useId();
    const id = providedId || generatedId;
    const isDisabled = disabled || isLoading;

    const currentLength = typeof value === "string" ? value.length : 0;

    // Internal ref for auto-resize
    const internalRef = useRef<HTMLTextAreaElement>(null);
    const textareaRef = (ref as React.RefObject<HTMLTextAreaElement>) || internalRef;

    // Auto-resize effect
    useEffect(() => {
      if (autoResize && textareaRef.current) {
        const textarea = textareaRef.current;
        textarea.style.height = "auto";
        const scrollHeight = textarea.scrollHeight;
        const maxHeightPx = parseInt(maxHeight) * 16; // Convert rem to px (assuming 16px base)
        textarea.style.height = `${Math.min(scrollHeight, maxHeightPx)}px`;
      }
    }, [value, autoResize, maxHeight, textareaRef]);

    return (
      <div className={`space-y-2 ${className}`}>
        {/* Label */}
        <label
          htmlFor={id}
          className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1"
        >
          {label}
        </label>

        {/* Textarea Field */}
        <textarea
          ref={textareaRef}
          id={id}
          value={value}
          maxLength={maxLength}
          disabled={isDisabled}
          onChange={onChange}
          style={{
            minHeight,
            maxHeight: autoResize ? maxHeight : undefined,
          }}
          className={`w-full resize-none ${styles.input} ${
            error
              ? "border-red-500/50 focus:border-red-500/50 focus:ring-red-500/30"
              : ""
          } disabled:opacity-50 disabled:cursor-not-allowed text-sm font-light leading-relaxed`}
          aria-invalid={!!error}
          aria-describedby={
            error ? `${id}-error` : helperText ? `${id}-helper` : undefined
          }
          {...props}
        />

        {/* Error / Helper / Count */}
        <div className="flex justify-between items-center">
          <div className="flex-1">
            {error ? (
              <p id={`${id}-error`} className="text-xs text-red-400" role="alert">
                {error}
              </p>
            ) : helperText ? (
              <p
                id={`${id}-helper`}
                className="text-xs text-slate-400 dark:text-white/40"
              >
                {helperText}
              </p>
            ) : null}
          </div>

          {showCount && maxLength && (
            <span
              className={`text-[10px] ${
                currentLength >= maxLength
                  ? "text-red-400"
                  : "text-slate-400 dark:text-white/30"
              }`}
            >
              {currentLength}/{maxLength}
            </span>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = "DimensionPanel.Textarea";
