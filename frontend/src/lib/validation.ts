"use client";

/**
 * Form Validation Library
 *
 * Zod-based validation utilities for real-time form validation.
 * Provides reusable schemas and hooks for dimension panel forms.
 *
 * 2026 UX Pattern: Immediate feedback with clear error messages
 */

import { z } from "zod";
import { useState, useCallback } from "react";

// =============================================================================
// Validation Schemas
// =============================================================================

/**
 * Prompt field validation schema
 * - Min 10 characters for meaningful input
 * - Max 3000 characters for API limits
 */
export const promptSchema = z
  .string()
  .min(10, "최소 10자 이상 입력해주세요")
  .max(3000, "3000자를 초과할 수 없습니다");

/**
 * Short prompt for titles, names, etc.
 * - Min 2 characters
 * - Max 100 characters
 */
export const shortPromptSchema = z
  .string()
  .min(2, "최소 2자 이상 입력해주세요")
  .max(100, "100자를 초과할 수 없습니다");

/**
 * URL validation schema
 */
export const urlSchema = z
  .string()
  .url("올바른 URL을 입력해주세요")
  .refine(
    (url) => url.startsWith("http://") || url.startsWith("https://"),
    "http:// 또는 https://로 시작하는 URL을 입력해주세요"
  );

/**
 * Optional URL validation
 */
export const optionalUrlSchema = z
  .string()
  .url("올바른 URL을 입력해주세요")
  .optional()
  .or(z.literal(""));

/**
 * Email validation schema
 */
export const emailSchema = z
  .string()
  .email("올바른 이메일 주소를 입력해주세요");

/**
 * Integer validation with range
 */
export function integerSchema(min: number, max: number) {
  return z
    .number()
    .int(`정수를 입력해주세요`)
    .min(min, `최소 ${min} 이상이어야 합니다`)
    .max(max, `최대 ${max} 이하여야 합니다`);
}

/**
 * Enum/select validation
 */
export function selectSchema<T extends string>(options: readonly T[], label = "옵션") {
  return z.enum(options as [T, ...T[]], {
    message: `유효한 ${label}을(를) 선택해주세요`,
  });
}

// =============================================================================
// Validation Hook
// =============================================================================

export interface UseFieldValidationOptions {
  /** Validate on every keystroke (default: false) */
  validateOnChange?: boolean;
  /** Validate on blur (default: true) */
  validateOnBlur?: boolean;
}

export interface FieldValidationResult {
  /** Current error message (null if valid) */
  error: string | null;
  /** Whether the field is currently valid */
  isValid: boolean;
  /** Whether validation has been triggered at least once */
  isTouched: boolean;
  /** Validate a value and return whether it's valid */
  validate: (value: unknown) => boolean;
  /** Mark field as touched (triggers validation display) */
  touch: () => void;
  /** Reset validation state */
  reset: () => void;
  /** Set error manually (for server-side errors) */
  setError: (message: string | null) => void;
}

/**
 * Hook for real-time field validation
 *
 * @example
 * ```tsx
 * const { error, isValid, validate, touch } = useFieldValidation(promptSchema);
 *
 * <Input
 *   value={value}
 *   onChange={(e) => {
 *     setValue(e.target.value);
 *     validate(e.target.value);
 *   }}
 *   onBlur={touch}
 *   error={error}
 * />
 * ```
 */
export function useFieldValidation<T>(
  schema: z.ZodType<T>,
  options: UseFieldValidationOptions = {}
): FieldValidationResult {
  const { validateOnBlur = true } = options;

  const [error, setErrorState] = useState<string | null>(null);
  const [isValid, setIsValid] = useState(false);
  const [isTouched, setIsTouched] = useState(false);

  const validate = useCallback(
    (value: unknown): boolean => {
      const result = schema.safeParse(value);

      if (result.success) {
        setErrorState(null);
        setIsValid(true);
        return true;
      } else {
        const errorMessage = result.error.issues[0]?.message || "유효하지 않은 값입니다";
        setErrorState(errorMessage);
        setIsValid(false);
        return false;
      }
    },
    [schema]
  );

  const touch = useCallback(() => {
    setIsTouched(true);
    if (validateOnBlur) {
      // Re-validate on blur to show errors
    }
  }, [validateOnBlur]);

  const reset = useCallback(() => {
    setErrorState(null);
    setIsValid(false);
    setIsTouched(false);
  }, []);

  const setError = useCallback((message: string | null) => {
    setErrorState(message);
    setIsValid(message === null);
    setIsTouched(true);
  }, []);

  return {
    error: isTouched ? error : null, // Only show error after touched
    isValid,
    isTouched,
    validate,
    touch,
    reset,
    setError,
  };
}

// =============================================================================
// Simple Form Validation
// =============================================================================

/**
 * Validate a value against a schema and return error message
 */
export function validateField<T>(schema: z.ZodType<T>, value: unknown): string | null {
  const result = schema.safeParse(value);
  if (result.success) return null;
  return result.error.issues[0]?.message || "유효하지 않은 값입니다";
}

/**
 * Check if a value is valid against a schema
 */
export function isValidField<T>(schema: z.ZodType<T>, value: unknown): boolean {
  return schema.safeParse(value).success;
}

// =============================================================================
// Validation Error Formatters
// =============================================================================

/**
 * Get user-friendly error message for common HTTP status codes
 */
export function getHttpErrorMessage(status: number): string {
  const messages: Record<number, string> = {
    400: "요청이 잘못되었습니다. 입력값을 확인해주세요.",
    401: "인증이 필요합니다. 다시 로그인해주세요.",
    402: "크레딧이 부족합니다.",
    403: "접근 권한이 없습니다.",
    404: "요청한 리소스를 찾을 수 없습니다.",
    409: "충돌이 발생했습니다. 새로고침 후 다시 시도해주세요.",
    413: "파일이 너무 큽니다.",
    429: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
    500: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
    502: "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.",
    503: "서비스를 일시적으로 사용할 수 없습니다.",
    504: "요청 시간이 초과되었습니다. 다시 시도해주세요.",
  };

  return messages[status] || `오류가 발생했습니다 (${status})`;
}

/**
 * Categorize error for UI treatment
 */
export type ErrorCategory = "user" | "system" | "network";

export function categorizeError(error: unknown): ErrorCategory {
  if (error instanceof TypeError && error.message.includes("fetch")) {
    return "network";
  }

  if (error instanceof Error) {
    const message = error.message.toLowerCase();
    if (
      message.includes("network") ||
      message.includes("offline") ||
      message.includes("timeout")
    ) {
      return "network";
    }
  }

  // HTTP status code errors
  if (typeof error === "object" && error !== null && "status" in error) {
    const status = (error as { status: number }).status;
    if (status >= 400 && status < 500) {
      return "user"; // Client errors - user can fix
    }
    if (status >= 500) {
      return "system"; // Server errors
    }
  }

  return "system"; // Default to system error
}

/**
 * Get error styling based on category
 */
export function getErrorStyle(category: ErrorCategory): {
  bgColor: string;
  borderColor: string;
  textColor: string;
  icon: "warning" | "error" | "wifi-off";
} {
  switch (category) {
    case "user":
      return {
        bgColor: "bg-amber-500/10",
        borderColor: "border-amber-500/30",
        textColor: "text-amber-400",
        icon: "warning",
      };
    case "network":
      return {
        bgColor: "bg-gray-500/10",
        borderColor: "border-gray-500/30",
        textColor: "text-gray-400",
        icon: "wifi-off",
      };
    case "system":
    default:
      return {
        bgColor: "bg-red-500/10",
        borderColor: "border-red-500/30",
        textColor: "text-red-400",
        icon: "error",
      };
  }
}
