import { create } from "zustand";
import type { DNACard } from "@/types/dna-card";

interface DNACardContextStore {
  // 상태
  activeCard: DNACard | null;
  preloadedData: Record<string, unknown> | null;
  isSidePanelOpen: boolean;

  // 액션
  setActiveCard: (card: DNACard, data?: Record<string, unknown>) => void;
  clearContext: () => void;
  openSidePanel: (card: DNACard) => void;
  closeSidePanel: () => void;
}

export const useDNACardContext = create<DNACardContextStore>((set) => ({
  activeCard: null,
  preloadedData: null,
  isSidePanelOpen: false,

  setActiveCard: (card, data) => {
    set({
      activeCard: card,
      preloadedData: data ?? null,
    });
  },

  clearContext: () => {
    set({
      activeCard: null,
      preloadedData: null,
      isSidePanelOpen: false,
    });
  },

  openSidePanel: (card) => {
    set({
      activeCard: card,
      isSidePanelOpen: true,
    });
  },

  closeSidePanel: () => {
    set({
      isSidePanelOpen: false,
    });
  },
}));

// NOTE: useDNACardContextConsumer 훅은 hooks/useDNACardContextConsumer.ts에 있습니다.
// 그 훅은 URL 파라미터 fallback과 타입별 콜백을 지원합니다.
