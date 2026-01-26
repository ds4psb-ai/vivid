"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import type { DNACard } from "@/types/dna-card";
import { useDNACardContext } from "@/stores/dnaCardContextStore";

interface UseDNACardNavigationOptions {
  onBeforeNavigate?: (card: DNACard) => boolean | void;
  source?: string; // P1: Analytics source tracking
}

export function useDNACardNavigation(options?: UseDNACardNavigationOptions) {
  const router = useRouter();
  const setActiveCard = useDNACardContext((s) => s.setActiveCard);

  const navigateToMegaApp = useCallback(
    (card: DNACard) => {
      // 네비게이션 전 콜백 (취소 가능)
      if (options?.onBeforeNavigate) {
        const result = options.onBeforeNavigate(card);
        if (result === false) return;
      }

      // P1: Analytics 이벤트 (gtag가 있다면)
      if (typeof window !== "undefined" && (window as any).gtag) {
        (window as any).gtag("event", "dna_card_click", {
          card_id: card.id,
          card_type: card.type,
          target_app: card.megaAppEntry.app,
          target_tab: card.megaAppEntry.tab,
          source: options?.source ?? "unknown",
        });
      }

      // P0: Zustand 스토어에 컨텍스트 저장
      setActiveCard(card, {
        // 타입별 프리로드 데이터
        ...(card.type === "master" && {
          colorPalettes: (card.metadata as any).colorPalettes,
          signatureTechniques: (card.metadata as any).signatureTechniques,
        }),
        ...(card.type === "masterpiece" && {
          logicVectorSummary: (card.metadata as any).logicVectorSummary,
        }),
        ...(card.type === "character" && {
          primaryImageUrl: (card.metadata as any).primaryImageUrl,
          tags: (card.metadata as any).tags,
        }),
      });

      // URL 구성
      const params = new URLSearchParams();
      params.set("tab", card.megaAppEntry.tab);

      // 프리로드 파라미터 추가
      if (card.megaAppEntry.preloadParams) {
        Object.entries(card.megaAppEntry.preloadParams).forEach(
          ([key, value]) => {
            params.set(key, value);
          }
        );
      }

      // 카드 컨텍스트 전달 (URL fallback)
      params.set("cardId", card.id);
      params.set("cardType", card.type);

      const url = `/${card.megaAppEntry.app}?${params.toString()}`;
      router.push(url);
    },
    [router, options, setActiveCard]
  );

  return { navigateToMegaApp };
}
