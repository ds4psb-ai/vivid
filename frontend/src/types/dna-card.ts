import type { LucideIcon } from "lucide-react";

// 카드 타입 (3종)
export type DNACardType = "master" | "masterpiece" | "character";

// 메가앱 진입 정보
export interface MegaAppEntry {
  app: "dna-lab" | "story-engine" | "production";
  tab: string;
  preloadParams?: Record<string, string>;
}

// 거장 DNA 메타데이터
export interface MasterDNAMetadata {
  auteurKey: string; // 'bong', 'epoch', etc.
  signatureTechniques: string[];
  signatureMoods: string[];
  colorPalettes: string[][]; // HEX colors
  films: string[];
}

// 작품 DNA 메타데이터
export interface MasterpieceDNAMetadata {
  ipId: string;
  auteurKey?: string; // Hidden (sealed)
  genres: string[];
  logicVectorSummary?: {
    compositionStyle: string;
    lightingPattern: string;
    pacingSignature: string;
  };
}

// 캐릭터 DNA 메타데이터
export interface CharacterDNAMetadata {
  characterId: string;
  primaryImageUrl: string;
  tags: string[];
  memoryKeyframeCount: number;
  consistencyScore?: number; // 0-1
}

// 통합 DNA 카드 인터페이스
export interface DNACard {
  id: string;
  type: DNACardType;

  // 기본 정보
  name: string;
  nameEn?: string;
  description: string;
  thumbnailUrl: string;

  // 타입별 메타데이터 (Union)
  metadata: MasterDNAMetadata | MasterpieceDNAMetadata | CharacterDNAMetadata;

  // 메가앱 연결
  megaAppEntry: MegaAppEntry;

  // UI 힌트
  badgeText?: string; // "NEW", "HOT", etc.
  badgeColor?: string;
  hue?: number; // Oklch 색상 (테마)

  // 시간 정보
  createdAt?: string;
  updatedAt?: string;
}

// 타입 가드
export function isMasterCard(
  card: DNACard
): card is DNACard & { metadata: MasterDNAMetadata } {
  return card.type === "master";
}

export function isMasterpieceCard(
  card: DNACard
): card is DNACard & { metadata: MasterpieceDNAMetadata } {
  return card.type === "masterpiece";
}

export function isCharacterCard(
  card: DNACard
): card is DNACard & { metadata: CharacterDNAMetadata } {
  return card.type === "character";
}
