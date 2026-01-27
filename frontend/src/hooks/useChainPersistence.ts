/**
 * useChainPersistence - Server synchronization for chain data
 *
 * Provides:
 * - Auto-save to server with debounce
 * - Load from server on mount/URL param
 * - Version conflict detection and resolution
 * - localStorage backup for offline resilience
 *
 * P7+ Chain UX Enhancement
 */

"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useDimensionChain } from "@/contexts/DimensionChainContext";
import { api, ChainSessionResponse, ChainSessionListItem } from "@/lib/api";
import { chainStorage, StoredChainState } from "@/lib/chain-storage";

interface ConflictState {
  serverVersion: number;
  localVersion: number;
  serverData: ChainSessionResponse;
  localData: StoredChainState;
}

interface UseChainPersistenceOptions {
  /** Auto-save changes to server (default: true) */
  autoSave?: boolean;
  /** Auto-save debounce in ms (default: 2000) */
  autoSaveDebounce?: number;
  /** IP slug for project-specific storage */
  ipSlug?: string;
}

interface UseChainPersistenceReturn {
  /** Current server session ID */
  sessionId: string | null;
  /** Current version for optimistic locking */
  version: number;
  /** Whether currently saving to server */
  isSaving: boolean;
  /** Last successful save timestamp */
  lastSaved: Date | null;
  /** Whether local changes are unsaved */
  isDirty: boolean;
  /** Version conflict state (if any) */
  conflictState: ConflictState | null;
  /** Sync status */
  syncStatus: "idle" | "syncing" | "synced" | "error" | "conflict";

  /** Save current state to server */
  saveToServer: () => Promise<void>;
  /** Load state from server by session ID */
  loadFromServer: (sessionId: string) => Promise<boolean>;
  /** Create a new server session */
  createNewSession: (title?: string) => Promise<string>;
  /** List user's sessions */
  listSessions: () => Promise<ChainSessionListItem[]>;
  /** Resolve version conflict */
  resolveConflict: (strategy: "keep_local" | "use_server") => Promise<void>;
  /** Clear conflict state */
  clearConflict: () => void;
}

export function useChainPersistence(
  options: UseChainPersistenceOptions = {}
): UseChainPersistenceReturn {
  const { autoSave = true, autoSaveDebounce = 2000, ipSlug } = options;

  const chain = useDimensionChain();

  const [sessionId, setSessionId] = useState<string | null>(() =>
    chainStorage.getServerSessionId()
  );
  const [version, setVersion] = useState<number>(() => chainStorage.getVersion());
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [conflictState, setConflictState] = useState<ConflictState | null>(null);
  const [syncStatus, setSyncStatus] = useState<
    "idle" | "syncing" | "synced" | "error" | "conflict"
  >("idle");

  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastChainDataRef = useRef<string>("");

  /**
   * Build state object for storage
   */
  const buildStoredState = useCallback((): StoredChainState => {
    return {
      chainData: chain.chainData,
      accumulatedEvidenceRefs: chain.accumulatedEvidenceRefs,
      navigationHistory: chain.history.map((h) => h.dimensionKey),
      currentDimension: chain.currentDimension,
      serverSessionId: sessionId,
      version,
      savedAt: Date.now(),
    };
  }, [
    chain.chainData,
    chain.accumulatedEvidenceRefs,
    chain.history,
    chain.currentDimension,
    sessionId,
    version,
  ]);

  /**
   * Save to localStorage backup
   */
  const saveLocalBackup = useCallback(() => {
    const state = buildStoredState();

    if (ipSlug) {
      chainStorage.saveForIp(ipSlug, state);
    } else {
      chainStorage.saveAll(state);
    }
  }, [buildStoredState, ipSlug]);

  /**
   * Save current chain state to server
   */
  const saveToServer = useCallback(async (): Promise<void> => {
    if (!sessionId) {
      console.warn("[ChainPersistence] No session ID, skipping server save");
      return;
    }

    setIsSaving(true);
    setSyncStatus("syncing");

    try {
      const response = await api.updateChainSession(sessionId, {
        version,
        chain_data: Object.fromEntries(
          Object.entries(chain.chainData).map(([key, data]) => [
            key,
            {
              dimension_key: data.dimensionKey,
              output: data.output,
              title: data.summary || "",
              evidence_refs: data.evidenceRefs || [],
              created_at: new Date(data.timestamp).toISOString(),
            },
          ])
        ),
        accumulated_evidence_refs: chain.accumulatedEvidenceRefs,
        navigation_history: chain.history.map((h) => h.dimensionKey),
        current_dimension: chain.currentDimension || undefined,
      });

      setVersion(response.version);
      chainStorage.setVersion(response.version);
      setLastSaved(new Date());
      setIsDirty(false);
      setSyncStatus("synced");

      // Update local backup with new version
      saveLocalBackup();
    } catch (error: unknown) {
      // Check for version conflict (409)
      if (error instanceof Error && error.message.includes("409")) {
        try {
          // Fetch current server state
          const serverState = await api.getChainSession(sessionId);
          setConflictState({
            serverVersion: serverState.version,
            localVersion: version,
            serverData: serverState,
            localData: buildStoredState(),
          });
          setSyncStatus("conflict");
        } catch {
          setSyncStatus("error");
        }
      } else {
        console.error("[ChainPersistence] Save failed:", error);
        setSyncStatus("error");
      }
    } finally {
      setIsSaving(false);
    }
  }, [
    sessionId,
    version,
    chain.chainData,
    chain.accumulatedEvidenceRefs,
    chain.history,
    chain.currentDimension,
    buildStoredState,
    saveLocalBackup,
  ]);

  /**
   * Load chain state from server
   */
  const loadFromServer = useCallback(
    async (loadSessionId: string): Promise<boolean> => {
      try {
        setSyncStatus("syncing");
        const response = await api.getChainSession(loadSessionId);

        // Update context with server data
        // Note: This requires the context to have a way to bulk-set chain data
        // For now, we just update local storage and let the context hydrate

        const state: StoredChainState = {
          chainData: Object.fromEntries(
            Object.entries(response.chain_data).map(([key, data]) => [
              key,
              {
                dimensionKey: data.dimension_key,
                output: data.output,
                timestamp: new Date(data.created_at).getTime(),
                summary: data.title,
                evidenceRefs: data.evidence_refs,
              },
            ])
          ),
          accumulatedEvidenceRefs: response.accumulated_evidence_refs,
          navigationHistory: response.navigation_history,
          currentDimension: response.current_dimension,
          serverSessionId: response.id,
          version: response.version,
          savedAt: Date.now(),
        };

        chainStorage.saveAll(state);
        setSessionId(response.id);
        chainStorage.setServerSessionId(response.id);
        setVersion(response.version);
        setIsDirty(false);
        setSyncStatus("synced");

        return true;
      } catch (error) {
        console.error("[ChainPersistence] Load failed:", error);
        setSyncStatus("error");
        return false;
      }
    },
    []
  );

  /**
   * Create a new server session
   */
  const createNewSession = useCallback(
    async (title?: string): Promise<string> => {
      try {
        setSyncStatus("syncing");
        const response = await api.createChainSession({
          title,
          ip_slug: ipSlug,
        });

        setSessionId(response.id);
        chainStorage.setServerSessionId(response.id);
        setVersion(response.version);
        setIsDirty(false);
        setSyncStatus("synced");

        return response.id;
      } catch (error) {
        console.error("[ChainPersistence] Create session failed:", error);
        setSyncStatus("error");
        throw error;
      }
    },
    [ipSlug]
  );

  /**
   * List user's sessions
   */
  const listSessions = useCallback(async (): Promise<ChainSessionListItem[]> => {
    try {
      return await api.listChainSessions();
    } catch (error) {
      console.error("[ChainPersistence] List sessions failed:", error);
      return [];
    }
  }, []);

  /**
   * Resolve version conflict
   */
  const resolveConflict = useCallback(
    async (strategy: "keep_local" | "use_server"): Promise<void> => {
      if (!conflictState || !sessionId) return;

      if (strategy === "use_server") {
        // Discard local changes, use server version
        await loadFromServer(sessionId);
        setConflictState(null);
      } else {
        // Keep local changes, force update with new version
        setVersion(conflictState.serverVersion);
        chainStorage.setVersion(conflictState.serverVersion);
        setConflictState(null);

        // Retry save with correct version
        await saveToServer();
      }
    },
    [conflictState, sessionId, loadFromServer, saveToServer]
  );

  /**
   * Clear conflict state
   */
  const clearConflict = useCallback(() => {
    setConflictState(null);
    setSyncStatus("idle");
  }, []);

  /**
   * Track chain data changes for dirty detection
   */
  useEffect(() => {
    const currentDataStr = JSON.stringify(chain.chainData);
    if (currentDataStr !== lastChainDataRef.current) {
      lastChainDataRef.current = currentDataStr;
      setIsDirty(true);

      // Always save to local backup
      saveLocalBackup();

      // Auto-save to server if enabled
      if (autoSave && sessionId) {
        // Clear existing timeout
        if (saveTimeoutRef.current) {
          clearTimeout(saveTimeoutRef.current);
        }

        // Set new debounced save
        saveTimeoutRef.current = setTimeout(() => {
          saveToServer();
        }, autoSaveDebounce);
      }
    }
  }, [chain.chainData, autoSave, sessionId, autoSaveDebounce, saveLocalBackup, saveToServer]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  /**
   * Restore from local storage on mount
   */
  useEffect(() => {
    const restored = ipSlug
      ? chainStorage.getForIp(ipSlug)
      : chainStorage.restore();

    if (restored) {
      // Set local state from restored data
      if (restored.serverSessionId) {
        setSessionId(restored.serverSessionId);
      }
      if (restored.version) {
        setVersion(restored.version);
      }
    }
  }, [ipSlug]);

  return {
    sessionId,
    version,
    isSaving,
    lastSaved,
    isDirty,
    conflictState,
    syncStatus,
    saveToServer,
    loadFromServer,
    createNewSession,
    listSessions,
    resolveConflict,
    clearConflict,
  };
}
