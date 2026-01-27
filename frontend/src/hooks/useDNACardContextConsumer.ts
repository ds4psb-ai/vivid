"use client";

/**
 * useDNACardContextConsumer - DNA 카드 컨텍스트 소비 훅
 *
 * DNA 카드 클릭 시 메가앱 패널에서 컨텍스트를 자동 로드합니다.
 *
 * Features:
 * - Zustand 스토어에서 컨텍스트 소비
 * - URL 파라미터 fallback (master, cardId, cardType)
 * - 타입별 콜백 (master, masterpiece, character)
 * - 자동 컨텍스트 클리어 옵션
 *
 * @example
 * ```tsx
 * useDNACardContextConsumer({
 *   onMasterContext: (auteurKey, metadata) => {
 *     setSelectedMaster(auteurKey);
 *   },
 *   onMasterpieceContext: (ipId, metadata) => {
 *     setLogicVector(metadata.logicVectorSummary);
 *   },
 * });
 * ```
 */

import { useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { useDNACardContext } from "@/stores/dnaCardContextStore";
import { AUTEUR_SPECIFIC_DATA } from "@/components/dna-card/constants";
import type {
  DNACard,
  MasterDNAMetadata,
  MasterpieceDNAMetadata,
  CharacterDNAMetadata,
} from "@/types/dna-card";

interface UseDNACardConsumerOptions {
  /** 거장 DNA 컨텍스트 수신 시 콜백 */
  onMasterContext?: (auteurKey: string, metadata: MasterDNAMetadata) => void;
  /** 작품 DNA 컨텍스트 수신 시 콜백 */
  onMasterpieceContext?: (ipId: string, metadata: MasterpieceDNAMetadata) => void;
  /** 캐릭터 DNA 컨텍스트 수신 시 콜백 */
  onCharacterContext?: (characterId: string, metadata: CharacterDNAMetadata) => void;
  /** 자동으로 컨텍스트 소비 후 클리어 (기본: true) */
  autoConsume?: boolean;
}

interface UseDNACardConsumerReturn {
  /** 컨텍스트가 존재하는지 여부 */
  hasContext: boolean;
  /** 활성 카드 타입 */
  cardType: string | null;
  /** 활성 카드 ID */
  cardId: string | null;
  /** 프리로드된 데이터 */
  preloadedData: Record<string, unknown> | null;
  /** 활성 카드 정보 */
  activeCard: DNACard | null;
  /** 컨텍스트 해제 함수 */
  dismissContext: () => void;
  /** 로드된 거장 키 (URL fallback 포함) */
  loadedMasterKey: string | null;
}

export function useDNACardContextConsumer(
  options: UseDNACardConsumerOptions = {}
): UseDNACardConsumerReturn {
  const searchParams = useSearchParams();
  const { activeCard, preloadedData, clearContext } = useDNACardContext();

  // URL 파라미터에서 컨텍스트 복원 (fallback)
  const cardType = searchParams.get("cardType");
  const cardId = searchParams.get("cardId");
  const masterKey = searchParams.get("master");

  // 컨텍스트가 처리되었는지 추적 (중복 처리 방지) - useRef로 리렌더 방지
  const hasProcessedRef = useRef(false);

  // 로드된 거장 키 - 직접 계산 (렌더링 시점 계산)
  const loadedMasterKey = (() => {
    if (activeCard?.type === "master") {
      return (activeCard.metadata as MasterDNAMetadata).auteurKey;
    }
    if (masterKey && AUTEUR_SPECIFIC_DATA[masterKey]) {
      return masterKey;
    }
    return null;
  })();

  // 컨텍스트 해제 함수
  const dismissContext = useCallback(() => {
    clearContext();
    hasProcessedRef.current = false;
  }, [clearContext]);

  useEffect(() => {
    // 이미 처리된 경우 스킵
    if (hasProcessedRef.current) return;

    // Zustand 스토어에서 컨텍스트가 있으면 사용
    if (activeCard) {
      hasProcessedRef.current = true;

      if (activeCard.type === "master" && options.onMasterContext) {
        const metadata = activeCard.metadata as MasterDNAMetadata;
        options.onMasterContext(metadata.auteurKey, metadata);
      }

      if (activeCard.type === "masterpiece" && options.onMasterpieceContext) {
        const metadata = activeCard.metadata as MasterpieceDNAMetadata;
        options.onMasterpieceContext(metadata.ipId, metadata);
      }

      if (activeCard.type === "character" && options.onCharacterContext) {
        const metadata = activeCard.metadata as CharacterDNAMetadata;
        options.onCharacterContext(metadata.characterId, metadata);
      }

      // 자동 소비 후 클리어
      if (options.autoConsume !== false) {
        // 딜레이를 두어 UI가 먼저 업데이트되도록 함
        setTimeout(() => {
          clearContext();
        }, 100);
      }

      return;
    }

    // URL 파라미터 fallback (master 키만 있을 경우)
    if (masterKey && options.onMasterContext) {
      const metadata = AUTEUR_SPECIFIC_DATA[masterKey];
      if (metadata) {
        hasProcessedRef.current = true;
        options.onMasterContext(masterKey, metadata);
      }
    }
  }, [
    activeCard,
    masterKey,
    options,
    clearContext,
  ]);

  return {
    hasContext: !!activeCard || !!masterKey,
    cardType: activeCard?.type ?? cardType,
    cardId: activeCard?.id ?? cardId,
    preloadedData,
    activeCard,
    dismissContext,
    loadedMasterKey,
  };
}
