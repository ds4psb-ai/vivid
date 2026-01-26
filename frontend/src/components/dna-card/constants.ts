import { Palette, Film, User } from "lucide-react";
import type { DNACardType, MasterDNAMetadata } from "@/types/dna-card";

export const DNA_CARD_CONFIG: Record<
  DNACardType,
  {
    icon: typeof Palette;
    label: string;
    labelEn: string;
    hue: number;
    megaApp: string;
    defaultTab: string;
  }
> = {
  master: {
    icon: Palette,
    label: "거장 DNA",
    labelEn: "Master DNA",
    hue: 45,
    megaApp: "dna-lab",
    defaultTab: "ad",
  },
  masterpiece: {
    icon: Film,
    label: "작품 DNA",
    labelEn: "Work DNA",
    hue: 148,
    megaApp: "dna-lab",
    defaultTab: "vpe",
  },
  character: {
    icon: User,
    label: "캐릭터 DNA",
    labelEn: "Character DNA",
    hue: 280,
    megaApp: "story-engine",
    defaultTab: "story",
  },
};

// P0: AI Auteur 페르소나 메타데이터 (법적 안전성 + 창의적 자유)
export const AUTEUR_SPECIFIC_DATA: Record<string, MasterDNAMetadata> = {
  kang: {
    auteurKey: "kang",
    signatureTechniques: ["수직 블로킹", "비대칭 프레이밍", "장면 간 대비"],
    signatureMoods: ["블랙 코미디", "사회 비판", "긴장감"],
    colorPalettes: [["#1a1a2e", "#16213e", "#0f3460", "#e94560"]],
    films: ["The Vertical Divide", "Threshold Society", "Mirrored Class"],
  },
  epoch: {
    auteurKey: "epoch",
    signatureTechniques: ["비선형 내러티브", "IMAX 촬영", "실제 스턴트"],
    signatureMoods: ["서사적 규모", "시간 왜곡", "철학적 탐구"],
    colorPalettes: [["#0a0a0a", "#1c1c1c", "#3d5a80", "#98c1d9"]],
    films: ["Temporal Fold", "The Fifth Dimension", "Gravity's Edge"],
  },
  velvet: {
    auteurKey: "velvet",
    signatureTechniques: ["스텝 프린팅", "스모키 렌즈", "네온 조명"],
    signatureMoods: ["멜랑콜리", "도시적 고독", "감각적 로맨스"],
    colorPalettes: [["#ff6b6b", "#c44569", "#546de5", "#303952"]],
    films: ["Neon Corridor", "Midnight Rain", "2AM Stories"],
  },
  voltage: {
    auteurKey: "voltage",
    signatureTechniques: ["트렁크 샷", "비선형 편집", "장면 긴장"],
    signatureMoods: ["팝 문화 오마주", "블랙 유머", "폭력의 미학"],
    colorPalettes: [["#e74c3c", "#f1c40f", "#2c3e50", "#ecf0f1"]],
    films: ["Voltage Rising", "Chapter Zero", "Blood Dialogue"],
  },
  yoon: {
    auteurKey: "yoon",
    signatureTechniques: ["대칭 구도", "색채 상징", "폭력 안무"],
    signatureMoods: ["복수 서사", "에로티시즘", "충격적 반전"],
    colorPalettes: [["#2d3436", "#636e72", "#b2bec3", "#dfe6e9"]],
    films: ["Obsidian Mirror", "The Elegant Revenge", "Crimson Silk"],
  },
  abyss: {
    auteurKey: "abyss",
    signatureTechniques: ["광활한 스케일", "사운드 디자인", "미니멀 대사"],
    signatureMoods: ["존재론적 불안", "장엄한 고독", "서서히 고조"],
    colorPalettes: [["#f5e6d3", "#d4a574", "#8b7355", "#2c2c2c"]],
    films: ["The Void Protocol", "Sand Empire", "First Contact"],
  },
  azure: {
    auteurKey: "azure",
    signatureTechniques: ["하이퍼 리얼리즘", "빛 산란 효과", "하늘/구름 묘사"],
    signatureMoods: ["청춘 그리움", "시간 초월 사랑", "자연과 도시"],
    colorPalettes: [["#74b9ff", "#0984e3", "#6c5ce7", "#fd79a8"]],
    films: ["Azure Crossing", "Light Years Apart", "Cloud Memories"],
  },
  prism: {
    auteurKey: "prism",
    signatureTechniques: ["원포인트 원근법", "롱 테이크", "대칭 구도"],
    signatureMoods: ["냉소적 관찰", "인간 본성 탐구", "완벽주의"],
    colorPalettes: [["#ffffff", "#ff0000", "#000000", "#2d3436"]],
    films: ["Geometric Madness", "The Perfect Frame", "Symmetry"],
  },
  seoyeon: {
    auteurKey: "seoyeon",
    signatureTechniques: ["핸드헬드 카메라", "자연광", "긴박한 편집"],
    signatureMoods: ["거친 리얼리즘", "긴박한 서스펜스", "심리적 공포"],
    colorPalettes: [["#1a1a1a", "#2d2d2d", "#4a4a4a", "#8b0000"]],
    films: ["Tempest Village", "The Chase", "Raw Tension"],
  },
};

// AI Auteur 목록 (프론트엔드 표시용)
export const MASTER_AUTEURS = [
  {
    key: "kang",
    name: "강주노",
    nameEn: "Kang Juno",
    thumbnail: "https://lh3.googleusercontent.com/aida-public/AB6AXuDmZbsTDohHKrLvWDAJW6YKBY5B51PSK51jHIwI05UFaJ581DHCSk4HvI8FzINcN5SAPzc_46FUQr0_QLNXGUUktKB2OoLuqXMPCM2pnmU8o6ZE0bDYUUM11u4susQwTxvLj8M4cxhVfqRZiiVPsjrCaUvH2hK1ldD-yuJrAtDv8PbbRfcpIS6dSJTI9Wr06gB0bM-YdFgNMNinvP56CiGGnB1iM0xARl6Z2XsTgW4zopO0L2LPGwX9DAlukMEUk1GRWNfnJXcDD1o0",
  },
  {
    key: "epoch",
    name: "테오 에포크",
    nameEn: "Theo Epoch",
    thumbnail: "https://lh3.googleusercontent.com/aida-public/AB6AXuAJOPykG5xBtx5szVkAE3UcvlZAYq2U9cXAf_u3-mT-KQe3kP1MFKU1x2tFbHtf-rvFSxYknHMUev3qCrHMs1Hnhz-JBMG0pc8e0OhnQGrWiNMXhj2qXDUG_XtZbjcLo6ScymYfD6eovoH0XI7g7pLxfmQWSmWHb5qtIhfokCUbGA0tf-DrtlrgpLk1yy0PJGZtVzX-xV8FPmtTLd3qF1w3c6SOdeWbdlg1APyqH4lwZdCUH3RVSsFkF-OzM0eo_Tk0xq3ULKDHlSQy",
  },
  {
    key: "velvet",
    name: "렌 벨벳",
    nameEn: "Ren Velvet",
    thumbnail: "https://lh3.googleusercontent.com/aida-public/AB6AXuDtgoCJNxgP9QdGJgiMsEr4hGITFu1bediw5FT9AGvhQiYMYPkYc2IZdUuhsn7sAnPxR1RJqWT4H5jD-7kcyELu9s5EQX3aJ3JFTtZCzb3Hf-pQKEpFFhhOBPoOjCkoxq6d3D9E40QrSC1IsrO7cocLNahh7M23tJk9pKu179gCLpmaoxkTcHUO1O1Zb5DTH375YL8swN7lsW4CeL45lp5WANoZkYHXxPxN4Y12_83auODbKUVIv2ENYz1U5s26pZuCWJ1VBw7xChac",
  },
  {
    key: "voltage",
    name: "렉스 볼티지",
    nameEn: "Rex Voltage",
    thumbnail: "https://lh3.googleusercontent.com/aida-public/AB6AXuDa3GtTxuQ8ZfgOJto08Cl2DqKprCrdEEyqApKvyUt0ucTdenJa7p7ZWtidLPl5tFNt5mSzjRJzlw6Y_XD8u3KqqIzpJBYnnScHlBYvxP6ERnOe8ppAKOb48f8jLyH5Hetz0D85-E6Ox0U1H_O8GX8xWTY90xRkZgvJzI_jMh63R7JSHGDlB4QLdNJvCHRPkhxQ8tk9PhW728AQU-Y05pfFWmHWj5N44GU7wVYCwVSvnA7BJ7PKyvWDCxk74caB2nzESqJjo1x2BhGh",
  },
  {
    key: "yoon",
    name: "윤수하",
    nameEn: "Yoon Suha",
    thumbnail: "/auteurs/yoon.jpg",
  },
  {
    key: "abyss",
    name: "오리온 어비스",
    nameEn: "Orion Abyss",
    thumbnail: "/auteurs/abyss.jpg",
  },
  {
    key: "azure",
    name: "소라 아주르",
    nameEn: "Sora Azure",
    thumbnail: "/auteurs/azure.jpg",
  },
  {
    key: "prism",
    name: "마일로 프리즘",
    nameEn: "Milo Prism",
    thumbnail: "/auteurs/prism.jpg",
  },
  {
    key: "seoyeon",
    name: "민서연",
    nameEn: "Min Seoyeon",
    thumbnail: "/auteurs/seoyeon.jpg",
  },
];

// AI Auteur별 hue 값 매핑
export const AUTEUR_HUE_MAP: Record<string, number> = {
  kang: 45, // Gold/Amber - 양면의 시선
  epoch: 220, // Blue - 시간의 설계자
  velvet: 340, // Magenta/Pink - 네온 속 감정
  voltage: 15, // Red-Orange - 폭발적 에너지
  yoon: 180, // Cyan - 어둠의 미학
  abyss: 35, // Sand/Desert - 우주의 심연
  azure: 200, // Sky Blue - 하늘빛 서정
  prism: 0, // Red - 기하학적 완벽
  seoyeon: 270, // Purple - 폭풍의 긴장
};
