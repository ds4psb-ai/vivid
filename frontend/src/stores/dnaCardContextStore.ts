import { create } from "zustand";
import type { DNACard, MasterDNAMetadata } from "@/types/dna-card";

interface DNACardContextStore {
  // 상태
  activeCard: DNACard | null;
  preloadedData: Record<string, unknown> | null;

  // 액션
  setActiveCard: (card: DNACard, data?: Record<string, unknown>) => void;
  clearContext: () => void;
}

export const useDNACardContext = create<DNACardContextStore>((set) => ({
  activeCard: null,
  preloadedData: null,

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
    });
  },
}));

// 헬퍼: 메가앱에서 컨텍스트 소비
export function useDNACardContextConsumer() {
  const { activeCard, preloadedData, clearContext } = useDNACardContext();

  const consumeContext = () => {
    const context = { activeCard, preloadedData };
    clearContext(); // 사용 후 정리
    return context;
  };

  return {
    activeCard,
    preloadedData,
    consumeContext,
    hasContext: !!activeCard,
  };
}
