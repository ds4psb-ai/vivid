/**
 * API Module Index
 * 
 * This is the main entry point for all API types and utilities.
 * It re-exports all domain-specific types for backward compatibility.
 * 
 * Usage:
 *   import type { Canvas, CreditBalance } from '@/lib/api';  // Still works
 *   import type { Canvas } from '@/lib/api/canvas.types';    // Direct import (tree-shakeable)
 */

// Core types
export * from "./types";

// Domain types
export * from "./canvas.types";
export * from "./credits.types";
export * from "./agent.types";
export * from "./dimension.types";
export * from "./admin.types";
