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

// P0: 거장별 고유 메타데이터 (AUTEUR_REGISTRY 기반)
export const AUTEUR_SPECIFIC_DATA: Record<string, MasterDNAMetadata> = {
  bong: {
    auteurKey: "bong",
    signatureTechniques: ["수직 블로킹", "비대칭 프레이밍", "장면 간 대비"],
    signatureMoods: ["블랙 코미디", "사회 비판", "긴장감"],
    colorPalettes: [["#1a1a2e", "#16213e", "#0f3460", "#e94560"]],
    films: ["기생충", "살인의 추억", "괴물", "마더", "옥자"],
  },
  nolan: {
    auteurKey: "nolan",
    signatureTechniques: ["비선형 내러티브", "IMAX 촬영", "실제 스턴트"],
    signatureMoods: ["서사적 규모", "시간 왜곡", "철학적 탐구"],
    colorPalettes: [["#0a0a0a", "#1c1c1c", "#3d5a80", "#98c1d9"]],
    films: ["다크 나이트", "인셉션", "인터스텔라", "테넷", "오펜하이머"],
  },
  wong: {
    auteurKey: "wong",
    signatureTechniques: ["스텝 프린팅", "스모키 렌즈", "네온 조명"],
    signatureMoods: ["멜랑콜리", "도시적 고독", "감각적 로맨스"],
    colorPalettes: [["#ff6b6b", "#c44569", "#546de5", "#303952"]],
    films: ["화양연화", "중경삼림", "2046", "해피 투게더"],
  },
  tarantino: {
    auteurKey: "tarantino",
    signatureTechniques: ["트렁크 샷", "비선형 편집", "장면 긴장"],
    signatureMoods: ["팝 문화 오마주", "블랙 유머", "폭력의 미학"],
    colorPalettes: [["#e74c3c", "#f1c40f", "#2c3e50", "#ecf0f1"]],
    films: ["펄프 픽션", "킬 빌", "장고: 분노의 추적자", "원스 어폰 어 타임"],
  },
  park: {
    auteurKey: "park",
    signatureTechniques: ["대칭 구도", "색채 상징", "폭력 안무"],
    signatureMoods: ["복수 서사", "에로티시즘", "충격적 반전"],
    colorPalettes: [["#2d3436", "#636e72", "#b2bec3", "#dfe6e9"]],
    films: ["올드보이", "아가씨", "친절한 금자씨", "박쥐"],
  },
  villeneuve: {
    auteurKey: "villeneuve",
    signatureTechniques: ["광활한 스케일", "사운드 디자인", "미니멀 대사"],
    signatureMoods: ["존재론적 불안", "장엄한 고독", "서서히 고조"],
    colorPalettes: [["#f5e6d3", "#d4a574", "#8b7355", "#2c2c2c"]],
    films: ["블레이드 러너 2049", "듄", "시카리오", "어라이벌"],
  },
  shinkai: {
    auteurKey: "shinkai",
    signatureTechniques: ["하이퍼 리얼리즘", "빛 산란 효과", "하늘/구름 묘사"],
    signatureMoods: ["청춘 그리움", "시간 초월 사랑", "자연과 도시"],
    colorPalettes: [["#74b9ff", "#0984e3", "#6c5ce7", "#fd79a8"]],
    films: ["너의 이름은", "날씨의 아이", "스즈메의 문단속", "초속 5센티미터"],
  },
  kubrick: {
    auteurKey: "kubrick",
    signatureTechniques: ["원포인트 원근법", "롱 테이크", "대칭 구도"],
    signatureMoods: ["냉소적 관찰", "인간 본성 탐구", "완벽주의"],
    colorPalettes: [["#ffffff", "#ff0000", "#000000", "#2d3436"]],
    films: [
      "2001 스페이스 오디세이",
      "샤이닝",
      "시계태엽 오렌지",
      "풀 메탈 재킷",
    ],
  },
};

// 거장 목록 (프론트엔드 표시용)
export const MASTER_AUTEURS = [
  {
    key: "bong",
    name: "봉준호",
    nameEn: "Bong Joon-ho",
    thumbnail: "/auteurs/bong.jpg",
  },
  {
    key: "nolan",
    name: "크리스토퍼 놀란",
    nameEn: "Christopher Nolan",
    thumbnail: "/auteurs/nolan.jpg",
  },
  {
    key: "wong",
    name: "왕가위",
    nameEn: "Wong Kar-wai",
    thumbnail: "/auteurs/wong.jpg",
  },
  {
    key: "tarantino",
    name: "쿠엔틴 타란티노",
    nameEn: "Quentin Tarantino",
    thumbnail: "/auteurs/tarantino.jpg",
  },
  {
    key: "park",
    name: "박찬욱",
    nameEn: "Park Chan-wook",
    thumbnail: "/auteurs/park.jpg",
  },
  {
    key: "villeneuve",
    name: "드니 빌뇌브",
    nameEn: "Denis Villeneuve",
    thumbnail: "/auteurs/villeneuve.jpg",
  },
  {
    key: "shinkai",
    name: "신카이 마코토",
    nameEn: "Makoto Shinkai",
    thumbnail: "/auteurs/shinkai.jpg",
  },
  {
    key: "kubrick",
    name: "스탠리 큐브릭",
    nameEn: "Stanley Kubrick",
    thumbnail: "/auteurs/kubrick.jpg",
  },
];

// 거장별 hue 값 매핑
export const AUTEUR_HUE_MAP: Record<string, number> = {
  bong: 45, // Gold/Amber - 기생충의 황금빛
  nolan: 220, // Blue - 인터스텔라의 우주
  wong: 340, // Magenta/Pink - 화양연화의 붉은 색감
  tarantino: 15, // Red-Orange - 피와 폭력
  park: 180, // Cyan - 차가운 복수
  villeneuve: 35, // Sand/Desert - 듄의 사막
  shinkai: 200, // Sky Blue - 하늘과 구름
  kubrick: 0, // Red - 샤이닝의 붉은색
};
