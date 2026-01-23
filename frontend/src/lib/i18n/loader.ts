/**
 * Dynamic Translation Loader
 * 
 * This module provides lazy-loading for translations to reduce initial bundle size.
 * The full translations object (81KB) is only loaded when actually needed.
 * 
 * Usage:
 *   const t = await loadTranslations('ko');
 *   console.log(t.appName); // "비비드 노드 캔버스"
 * 
 * For synchronous access (when translations are already loaded):
 *   import { translations } from '@/lib/translations'; // Still works
 */

import type { Language } from "../translations";

// Cache for loaded translations
let cachedTranslations: Record<string, Record<string, string>> | null = null;

/**
 * Dynamically load translations
 * Uses dynamic import to defer loading until needed
 */
export async function loadTranslations(
    lang: Language = "ko"
): Promise<Record<string, string>> {
    if (!cachedTranslations) {
        const translationModule = await import("../translations");
        cachedTranslations = translationModule.translations;
    }
    return cachedTranslations[lang];
}

/**
 * Get translation key with fallback
 */
export function t(
    translations: Record<string, string>,
    key: string,
    fallback?: string
): string {
    return translations[key] ?? fallback ?? key;
}

/**
 * Preload translations (call during initial app load)
 */
export function preloadTranslations(): void {
    // Fire-and-forget preload
    void import("../translations");
}

// Re-export type
export type { Language };
