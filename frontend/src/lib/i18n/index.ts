/**
 * i18n Module Index
 * 
 * Re-exports translation utilities for convenient imports.
 */

export { loadTranslations, t, preloadTranslations, type Language } from "./loader";

// For backward compatibility, also re-export the synchronous translations
export { translations } from "../translations";
