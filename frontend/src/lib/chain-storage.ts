/**
 * Chain Storage - Multi-layer storage for workflow chain persistence
 *
 * Provides three storage tiers:
 * 1. sessionStorage - Fast, tab-scoped (existing behavior)
 * 2. localStorage - Survives tab close, same-device persistence
 * 3. Server - Cross-device, permanent persistence (via API)
 *
 * P7+ Chain UX Enhancement
 */

import type { ChainData } from "@/contexts/DimensionChainContext";

const CHAIN_SESSION_KEY = "vivid_chain_session";
const CHAIN_DATA_KEY = "vivid_chain_data";
const CHAIN_VERSION_KEY = "vivid_chain_version";
const CHAIN_EVIDENCE_KEY = "vivid_chain_evidence";
const CHAIN_HISTORY_KEY = "vivid_chain_history";

interface StoredChainState {
  chainData: Record<string, ChainData>;
  accumulatedEvidenceRefs: string[];
  navigationHistory: string[];
  currentDimension: string | null;
  serverSessionId: string | null;
  version: number;
  savedAt: number;
}

/**
 * Chain storage utility with multi-tier persistence
 */
export const chainStorage = {
  // =========================================================================
  // Session Storage (Fast, tab-scoped)
  // =========================================================================

  /**
   * Get chain state from sessionStorage
   */
  getFromSession: (): StoredChainState | null => {
    if (typeof window === "undefined") return null;

    try {
      const stored = sessionStorage.getItem(CHAIN_DATA_KEY);
      if (!stored) return null;
      return JSON.parse(stored) as StoredChainState;
    } catch {
      return null;
    }
  },

  /**
   * Save chain state to sessionStorage
   */
  saveToSession: (state: StoredChainState): void => {
    if (typeof window === "undefined") return;

    try {
      sessionStorage.setItem(CHAIN_DATA_KEY, JSON.stringify(state));
    } catch (e) {
      console.warn("[ChainStorage] Failed to save to sessionStorage:", e);
    }
  },

  /**
   * Clear sessionStorage chain data
   */
  clearSession: (): void => {
    if (typeof window === "undefined") return;
    sessionStorage.removeItem(CHAIN_DATA_KEY);
  },

  // =========================================================================
  // Local Storage (Survives tab close)
  // =========================================================================

  /**
   * Get chain state from localStorage (backup)
   */
  getFromLocal: (): StoredChainState | null => {
    if (typeof window === "undefined") return null;

    try {
      const stored = localStorage.getItem(CHAIN_DATA_KEY);
      if (!stored) return null;
      return JSON.parse(stored) as StoredChainState;
    } catch {
      return null;
    }
  },

  /**
   * Save chain state to localStorage (backup)
   */
  saveToLocal: (state: StoredChainState): void => {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(CHAIN_DATA_KEY, JSON.stringify(state));
    } catch (e) {
      console.warn("[ChainStorage] Failed to save to localStorage:", e);
    }
  },

  /**
   * Clear localStorage chain data
   */
  clearLocal: (): void => {
    if (typeof window === "undefined") return;
    localStorage.removeItem(CHAIN_DATA_KEY);
  },

  // =========================================================================
  // Version Tracking (for Optimistic Locking)
  // =========================================================================

  /**
   * Get current version number
   */
  getVersion: (): number => {
    if (typeof window === "undefined") return 1;

    try {
      const version = localStorage.getItem(CHAIN_VERSION_KEY);
      return version ? parseInt(version, 10) : 1;
    } catch {
      return 1;
    }
  },

  /**
   * Set version number
   */
  setVersion: (version: number): void => {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(CHAIN_VERSION_KEY, version.toString());
    } catch {
      // Ignore
    }
  },

  // =========================================================================
  // Server Session ID
  // =========================================================================

  /**
   * Get server session ID
   */
  getServerSessionId: (): string | null => {
    if (typeof window === "undefined") return null;

    try {
      return localStorage.getItem(CHAIN_SESSION_KEY);
    } catch {
      return null;
    }
  },

  /**
   * Set server session ID
   */
  setServerSessionId: (sessionId: string | null): void => {
    if (typeof window === "undefined") return;

    try {
      if (sessionId) {
        localStorage.setItem(CHAIN_SESSION_KEY, sessionId);
      } else {
        localStorage.removeItem(CHAIN_SESSION_KEY);
      }
    } catch {
      // Ignore
    }
  },

  // =========================================================================
  // Recovery Logic
  // =========================================================================

  /**
   * Restore chain state with fallback priority:
   * 1. sessionStorage (current tab)
   * 2. localStorage (previous session)
   */
  restore: (): StoredChainState | null => {
    // Try sessionStorage first (current tab)
    const session = chainStorage.getFromSession();
    if (session && Object.keys(session.chainData || {}).length > 0) {
      return session;
    }

    // Fall back to localStorage (previous session)
    const local = chainStorage.getFromLocal();
    if (local && Object.keys(local.chainData || {}).length > 0) {
      // Restore to sessionStorage for this tab
      chainStorage.saveToSession(local);
      return local;
    }

    return null;
  },

  /**
   * Save to both session and local storage
   */
  saveAll: (state: StoredChainState): void => {
    chainStorage.saveToSession(state);
    chainStorage.saveToLocal(state);
    if (state.version) {
      chainStorage.setVersion(state.version);
    }
  },

  /**
   * Clear all local chain storage
   */
  clearAll: (): void => {
    chainStorage.clearSession();
    chainStorage.clearLocal();
    chainStorage.setServerSessionId(null);

    if (typeof window === "undefined") return;

    try {
      localStorage.removeItem(CHAIN_VERSION_KEY);
    } catch {
      // Ignore
    }
  },

  // =========================================================================
  // IP-Specific Storage (for project isolation)
  // =========================================================================

  /**
   * Get chain state for a specific IP/project
   */
  getForIp: (ipSlug: string): StoredChainState | null => {
    if (typeof window === "undefined") return null;

    try {
      const stored = sessionStorage.getItem(`${CHAIN_DATA_KEY}_${ipSlug}`);
      if (!stored) return null;
      return JSON.parse(stored) as StoredChainState;
    } catch {
      return null;
    }
  },

  /**
   * Save chain state for a specific IP/project
   */
  saveForIp: (ipSlug: string, state: StoredChainState): void => {
    if (typeof window === "undefined") return;

    try {
      sessionStorage.setItem(`${CHAIN_DATA_KEY}_${ipSlug}`, JSON.stringify(state));
      // Also backup to localStorage
      localStorage.setItem(`${CHAIN_DATA_KEY}_${ipSlug}`, JSON.stringify(state));
    } catch (e) {
      console.warn("[ChainStorage] Failed to save for IP:", e);
    }
  },

  /**
   * Check if IP has stored chain data
   */
  hasDataForIp: (ipSlug: string): boolean => {
    if (typeof window === "undefined") return false;

    const stored =
      sessionStorage.getItem(`${CHAIN_DATA_KEY}_${ipSlug}`) ||
      localStorage.getItem(`${CHAIN_DATA_KEY}_${ipSlug}`);
    return !!stored;
  },
};

export type { StoredChainState };
