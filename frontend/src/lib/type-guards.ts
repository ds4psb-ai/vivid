/**
 * Centralized Type Guards
 *
 * Common type guard utilities for safe runtime type checking.
 * Use these instead of inline type assertions for better maintainability.
 */

/**
 * Safely get a string value from an unknown object.
 *
 * @param obj - The object to extract from
 * @param key - The key to look up
 * @returns The string value if valid, undefined otherwise
 */
export function getStringValue(obj: unknown, key: string): string | undefined {
  if (obj && typeof obj === "object" && key in obj) {
    const val = (obj as Record<string, unknown>)[key];
    return typeof val === "string" ? val : undefined;
  }
  return undefined;
}

/**
 * Safely get a number value from an unknown object.
 *
 * @param obj - The object to extract from
 * @param key - The key to look up
 * @returns The number value if valid, undefined otherwise
 */
export function getNumberValue(obj: unknown, key: string): number | undefined {
  if (obj && typeof obj === "object" && key in obj) {
    const val = (obj as Record<string, unknown>)[key];
    return typeof val === "number" ? val : undefined;
  }
  return undefined;
}

/**
 * Check if a value is a non-null record (plain object).
 *
 * @param value - The value to check
 * @returns True if value is a record
 */
export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Check if a value is a non-empty string.
 *
 * @param value - The value to check
 * @returns True if value is a non-empty string
 */
export function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

/**
 * Check if a value is an array.
 *
 * @param value - The value to check
 * @returns True if value is an array
 */
export function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

/**
 * Safely extract a nested value from an object path.
 *
 * @param obj - The object to extract from
 * @param path - Dot-separated path (e.g., "user.profile.name")
 * @returns The value at the path, or undefined
 */
export function getNestedValue(obj: unknown, path: string): unknown {
  const keys = path.split(".");
  let current: unknown = obj;

  for (const key of keys) {
    if (!isRecord(current)) return undefined;
    current = current[key];
  }

  return current;
}
