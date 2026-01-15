"use client";

/**
 * DimensionPanelContext - React 19 Optimized Context Provider
 *
 * Features:
 * - Compound Component state sharing
 * - Design token integration from lib/tokens.ts
 * - Memoized style utilities
 * - React 19 simplified Context syntax
 *
 * @see PANEL_DESIGN_UNITY_SPEC.md
 */

import {
  createContext,
  useContext,
  useState,
  useMemo,
  useCallback,
  type ReactNode,
} from "react";
import {
  type DimensionCode,
  type ThemeColor,
  type DimensionToken,
  type ThemeColorClasses,
  getDimensionToken,
  getDimensionThemeClasses,
  getDimensionGradient,
  getDimensionGlow,
  getDimensionGlassStyle,
  getDimensionInputStyle,
  getDimensionButtonStyle,
  getDimensionResultStyle,
} from "@/lib/tokens";

// =============================================================================
// TYPES
// =============================================================================

export interface DimensionPanelStyles {
  /** Gradient for buttons */
  gradient: string;
  /** Medium glow shadow */
  glow: string;
  /** Small glow shadow */
  glowSm: string;
  /** Large glow shadow */
  glowLg: string;
  /** Glassmorphism panel style */
  glass: string;
  /** Input field style */
  input: string;
  /** Generate button style */
  button: string;
  /** Result card style */
  result: string;
}

export interface DimensionPanelContextValue {
  // Token Integration
  dimensionCode: DimensionCode;
  themeColor: ThemeColor;
  token: DimensionToken;
  classes: ThemeColorClasses;
  styles: DimensionPanelStyles;

  // State Management
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  error: Error | null;
  setError: (error: Error | null) => void;
  result: unknown;
  setResult: (result: unknown) => void;
  responseId: string | null;
  setResponseId: (id: string | null) => void;

  // Computed
  hasResult: boolean;
  hasError: boolean;

  // Actions
  reset: () => void;
}

// =============================================================================
// CONTEXT
// =============================================================================

const DimensionPanelContext = createContext<DimensionPanelContextValue | null>(null);

/**
 * Hook to access DimensionPanel context (required)
 * @throws Error if used outside DimensionPanelProvider
 */
export function useDimensionPanel(): DimensionPanelContextValue {
  const context = useContext(DimensionPanelContext);
  if (!context) {
    throw new Error(
      "useDimensionPanel must be used within DimensionPanel. " +
      "Make sure your component is wrapped with <DimensionPanel>."
    );
  }
  return context;
}

/**
 * Optional hook - returns null if outside provider (no throw)
 * Useful for components that can work both inside and outside the panel
 */
export function useDimensionPanelOptional(): DimensionPanelContextValue | null {
  return useContext(DimensionPanelContext);
}

// =============================================================================
// PROVIDER
// =============================================================================

export interface DimensionPanelProviderProps {
  /** Dimension code for theming */
  dimensionCode: DimensionCode;
  /** Child components */
  children: ReactNode;
  /** Initial loading state */
  initialLoading?: boolean;
  /** Initial result */
  initialResult?: unknown;
}

export function DimensionPanelProvider({
  dimensionCode,
  children,
  initialLoading = false,
  initialResult = null,
}: DimensionPanelProviderProps) {
  // State
  const [isLoading, setLoading] = useState(initialLoading);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<unknown>(initialResult);
  const [responseId, setResponseId] = useState<string | null>(null);

  // Token data (stable reference)
  const token = getDimensionToken(dimensionCode);
  const classes = getDimensionThemeClasses(dimensionCode);

  // Memoize style utilities to prevent re-computation
  const styles = useMemo<DimensionPanelStyles>(() => ({
    gradient: getDimensionGradient(dimensionCode),
    glow: getDimensionGlow(dimensionCode, "md"),
    glowSm: getDimensionGlow(dimensionCode, "sm"),
    glowLg: getDimensionGlow(dimensionCode, "lg"),
    glass: getDimensionGlassStyle(dimensionCode),
    input: getDimensionInputStyle(dimensionCode),
    button: getDimensionButtonStyle(dimensionCode),
    result: getDimensionResultStyle(dimensionCode),
  }), [dimensionCode]);

  // Reset action
  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResult(null);
    setResponseId(null);
  }, []);

  // Memoize context value to prevent unnecessary re-renders
  const value = useMemo<DimensionPanelContextValue>(() => ({
    // Token Integration
    dimensionCode,
    themeColor: token.themeColor,
    token,
    classes,
    styles,

    // State Management
    isLoading,
    setLoading,
    error,
    setError,
    result,
    setResult,
    responseId,
    setResponseId,

    // Computed
    hasResult: result !== null,
    hasError: error !== null,

    // Actions
    reset,
  }), [
    dimensionCode,
    token,
    classes,
    styles,
    isLoading,
    error,
    result,
    responseId,
    reset,
  ]);

  return (
    <DimensionPanelContext.Provider value={value}>
      {children}
    </DimensionPanelContext.Provider>
  );
}

// =============================================================================
// DISPLAY NAME (for React DevTools)
// =============================================================================

DimensionPanelContext.displayName = "DimensionPanelContext";
