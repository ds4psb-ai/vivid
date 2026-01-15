"use client";

/**
 * Select - DimensionPanel.Select compound component
 *
 * Unified select dropdown with dimension-themed focus ring.
 */

import { forwardRef, useId, type SelectHTMLAttributes } from "react";
import { ChevronDown } from "lucide-react";
import { useDimensionPanel } from "./DimensionPanelContext";

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

export interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "className"> {
  /** Field label */
  label: string;
  /** Options to display */
  options: SelectOption[];
  /** Error message */
  error?: string;
  /** Helper text */
  helperText?: string;
  /** Placeholder option */
  placeholder?: string;
  /** Additional className */
  className?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  function Select(
    {
      label,
      options,
      error,
      helperText,
      placeholder,
      className = "",
      id: providedId,
      disabled,
      ...props
    },
    ref
  ) {
    const { styles, isLoading, classes } = useDimensionPanel();
    const generatedId = useId();
    const id = providedId || generatedId;
    const isDisabled = disabled || isLoading;

    return (
      <div className={`space-y-2 ${className}`}>
        {/* Label */}
        <label
          htmlFor={id}
          className="text-[10px] font-bold text-slate-500 dark:text-zinc-500 uppercase tracking-widest ml-1"
        >
          {label}
        </label>

        {/* Select Container */}
        <div className="relative">
          <select
            ref={ref}
            id={id}
            disabled={isDisabled}
            className={`w-full appearance-none ${styles.input} pr-10 ${
              error
                ? "border-red-500/50 focus:border-red-500/50 focus:ring-red-500/30"
                : ""
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${id}-error` : helperText ? `${id}-helper` : undefined
            }
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
                className="bg-white dark:bg-[#0F0F1A] text-slate-900 dark:text-white"
              >
                {option.label}
              </option>
            ))}
          </select>

          {/* Dropdown Icon */}
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 dark:text-white/30">
            <ChevronDown className="h-4 w-4" />
          </div>
        </div>

        {/* Error / Helper */}
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
    );
  }
);

Select.displayName = "DimensionPanel.Select";
