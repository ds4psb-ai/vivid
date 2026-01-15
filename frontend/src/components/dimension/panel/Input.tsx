"use client";

/**
 * Input - DimensionPanel.Input compound component
 *
 * Unified input field with dimension-themed focus ring.
 */

import { forwardRef, type InputHTMLAttributes, useId } from "react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "className"> {
  /** Field label */
  label: string;
  /** Error message */
  error?: string;
  /** Helper text below input */
  helperText?: string;
  /** Show character count */
  showCount?: boolean;
  /** Additional className */
  className?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  {
    label,
    error,
    helperText,
    showCount = false,
    maxLength,
    value,
    className = "",
    id: providedId,
    disabled,
    ...props
  },
  ref
) {
  const { styles, isLoading } = useDimensionPanel();
  const generatedId = useId();
  const id = providedId || generatedId;
  const isDisabled = disabled || isLoading;

  const currentLength = typeof value === "string" ? value.length : 0;

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Label */}
      <label
        htmlFor={id}
        className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1"
      >
        {label}
      </label>

      {/* Input Field */}
      <input
        ref={ref}
        id={id}
        value={value}
        maxLength={maxLength}
        disabled={isDisabled}
        className={`w-full ${styles.input} ${
          error
            ? "border-red-500/50 focus:border-red-500/50 focus:ring-red-500/30"
            : ""
        } disabled:opacity-50 disabled:cursor-not-allowed`}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
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
            <p id={`${id}-helper`} className="text-xs text-slate-400 dark:text-white/40">
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
});

Input.displayName = "DimensionPanel.Input";
