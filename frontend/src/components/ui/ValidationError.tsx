"use client";

/**
 * ValidationError - Display Zod validation errors
 *
 * Phase -1: F2 API Contract Implementation
 *
 * Features:
 * - Display field-specific or all errors
 * - Supports ZodErrorTree structure from z.treeifyError()
 * - Animated appearance
 * - Dismissible option
 */

import { useState, useEffect } from "react";
import { AlertCircle, X } from "lucide-react";
import type { ZodErrorTree } from "@/lib/schemas/validated-fetch";

// =============================================================================
// Types
// =============================================================================

export interface ValidationErrorProps {
  /** Error tree from z.treeifyError() */
  errors: ZodErrorTree | null;
  /** Specific field to show errors for (optional, shows all if not provided) */
  field?: string;
  /** Custom class name */
  className?: string;
  /** Show dismiss button */
  dismissible?: boolean;
  /** Callback when dismissed */
  onDismiss?: () => void;
  /** Variant style */
  variant?: "inline" | "banner" | "toast";
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Extract errors for a specific field from error tree
 * Zod v4 treeifyError returns { errors: [], properties: { field: { errors: [] } } }
 */
function getFieldErrors(tree: ZodErrorTree, field: string): string[] {
  if (tree.properties && tree.properties[field]) {
    return tree.properties[field].errors || [];
  }
  return [];
}

/**
 * Extract all errors from error tree (flattened)
 * Zod v4 treeifyError returns { errors: [], properties: { field: { errors: [] } } }
 */
function getAllErrors(tree: ZodErrorTree): string[] {
  const errors: string[] = [...(tree.errors || [])];

  if (tree.properties) {
    for (const [key, nested] of Object.entries(tree.properties)) {
      if (nested.errors && nested.errors.length > 0) {
        nested.errors.forEach((err) => {
          errors.push(`${key}: ${err}`);
        });
      }
    }
  }

  return errors;
}

// =============================================================================
// Component
// =============================================================================

export function ValidationError({
  errors,
  field,
  className = "",
  dismissible = false,
  onDismiss,
  variant = "inline",
}: ValidationErrorProps) {
  const [isVisible, setIsVisible] = useState(true);

  // Reset visibility when errors change
  useEffect(() => {
    if (errors) {
      setIsVisible(true);
    }
  }, [errors]);

  if (!errors || !isVisible) return null;

  const errorMessages = field
    ? getFieldErrors(errors, field)
    : getAllErrors(errors);

  if (errorMessages.length === 0) return null;

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  // Variant styles
  const variantStyles = {
    inline: "text-sm text-red-400 mt-1",
    banner:
      "p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400",
    toast:
      "fixed bottom-4 right-4 p-4 bg-red-500/90 text-white rounded-xl shadow-lg max-w-sm z-50",
  };

  if (variant === "inline") {
    return (
      <div
        className={`${variantStyles.inline} ${className} animate-in fade-in slide-in-from-top-1 duration-200`}
      >
        {errorMessages.map((err, i) => (
          <p key={i} className="flex items-start gap-1">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
            <span>{err}</span>
          </p>
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${variantStyles[variant]} ${className} animate-in fade-in slide-in-from-top-2 duration-200`}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
        <div className="flex-1 space-y-1">
          {errorMessages.map((err, i) => (
            <p key={i} className="text-sm">
              {err}
            </p>
          ))}
        </div>
        {dismissible && (
          <button
            onClick={handleDismiss}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Field-specific Error Component
// =============================================================================

export interface FieldErrorProps {
  /** Error tree from z.treeifyError() */
  errors: ZodErrorTree | null;
  /** Field name to show errors for */
  field: string;
  /** Custom class name */
  className?: string;
}

/**
 * Simplified component for showing single field errors
 *
 * @example
 * <input name="topic" />
 * <FieldError errors={validationErrors} field="topic" />
 */
export function FieldError({ errors, field, className = "" }: FieldErrorProps) {
  if (!errors) return null;

  const fieldErrors = getFieldErrors(errors, field);
  if (fieldErrors.length === 0) return null;

  return (
    <p
      className={`text-xs text-red-400 mt-1 animate-in fade-in duration-150 ${className}`}
    >
      {fieldErrors[0]}
    </p>
  );
}

// =============================================================================
// Exports
// =============================================================================

export default ValidationError;
