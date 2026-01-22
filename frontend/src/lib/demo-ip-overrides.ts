/**
 * Demo IP Overrides - Soft Overlay Pattern
 *
 * 투자자 데모용 IP 데이터를 단일 파일에서 관리합니다.
 * 실제 DB 데이터가 없을 때 fallback으로 사용됩니다.
 *
 * 포스트 데모 정리: 이 파일만 삭제하면 됩니다.
 */

export interface DemoWorkflow {
  id: string;
  title: string;
  titleKo: string;
  description: string;
  descriptionKo: string;
  icon: string; // lucide-react icon name
  href: string; // 실제 dimension 경로
  badge?: string;
  stepNumber?: number; // Rail 2 (복잡한 워크플로우)용 순서
}

/**
 * 콘텐츠 유형별 분류
 * - vertical-shortform: 세로 숏폼 웹드라마 (9:16)
 * - horizontal-anime-mv: 가로 애니메이션 MV (16:9)
 */
export type ContentType = "vertical-shortform" | "horizontal-anime-mv";

export interface DemoIPOverride {
  // 기본 정보
  slug: string;
  titleKo: string;
  titleEn: string;
  descKo: string;
  descEn: string;
  genre: string;

  // 콘텐츠 유형 (Rail 분류용)
  contentType?: ContentType;

  // 비디오 방향 (9:16 세로 vs 16:9 가로)
  aspectRatio?: "9:16" | "16:9";

  // 미디어 (optional - 실제 데이터 우선)
  previewVideoUrl?: string;
  detailVideoUrl?: string;
  thumbnailUrl?: string;
  localVideoPath?: string; // 로컬 비디오 파일 경로 (개발용)

  // 메타 정보
  isHot?: boolean;
  isNew?: boolean;
  viewCount?: string;

  // 워크플로우 추천
  workflows: DemoWorkflow[];
}

/**
 * 데모 IP 오버라이드 데이터
 * slug를 key로 사용하여 빠른 조회 지원
 */
export const DEMO_IP_OVERRIDES: Record<string, DemoIPOverride> = {
  // ============================================================================
  // Rail 1: 세로 숏폼 웹드라마 (9:16)
  // ============================================================================
  "umbrella-encounter": {
    slug: "umbrella-encounter",
    titleKo: "우산 속 만남",
    titleEn: "Umbrella Encounter",
    descKo: "실수로 모르는 여자애 우산 속에 들어갔을 때 - 비 오는 날의 우연한 만남이 시작되는 로맨스",
    descEn: "A rainy day chance encounter - Romance begins when accidentally sharing an umbrella with a stranger",
    genre: "로맨스/숏폼",
    contentType: "vertical-shortform",
    aspectRatio: "9:16",
    localVideoPath: "/demo-video/umbrella-encounter.mp4",
    previewVideoUrl: "/demo-video/umbrella-encounter.mp4",
    detailVideoUrl: "/demo-video/umbrella-encounter.mp4",
    thumbnailUrl: "/demo-video/umbrella-encounter-thumb.jpg",
    isNew: true,
    viewCount: "1.2M",
    workflows: [
      {
        id: "analyze",
        title: "Reference Decode",
        titleKo: "레퍼런스 분석",
        description: "Analyze video frames, extract style and mood patterns",
        descriptionKo: "영상 프레임 분석, 스타일과 무드 패턴 추출",
        icon: "Eye",
        href: "/dimension/reference-decoder",
        badge: "4D",
        stepNumber: 1,
      },
      {
        id: "persona",
        title: "Persona Remix",
        titleKo: "페르소나 변주",
        description: "Analyze character psychology and create variations",
        descriptionKo: "캐릭터 심리 분석 및 페르소나 변주 생성",
        icon: "Brain",
        href: "/dimension/abyss",
        badge: "AI",
        stepNumber: 2,
      },
      {
        id: "story",
        title: "Story Variation",
        titleKo: "스토리 변주",
        description: "Same situation, different personality - create story variations",
        descriptionKo: "같은 상황, 다른 성격 - 스토리 변주 생성",
        icon: "BookOpen",
        href: "/dimension/story-architect",
        badge: "2D",
        stepNumber: 3,
      },
      {
        id: "generate",
        title: "Generate Shortform",
        titleKo: "숏폼 생성",
        description: "Generate new vertical shortform with Veo 3.1 (9:16)",
        descriptionKo: "Veo 3.1로 새로운 세로 숏폼 생성 (9:16)",
        icon: "Video",
        href: "/dimension/video-maker",
        badge: "VEO",
        stepNumber: 4,
      },
    ],
  },

  // ============================================================================
  // Rail 2: 가로 애니 뮤비 (16:9) - 복잡한 씬 일관성 워크플로우
  // ============================================================================
  "cooking-anime-mv": {
    slug: "cooking-anime-mv",
    titleKo: "흑백요리사2 애니 오프닝",
    titleEn: "Culinary Battle Anime OP",
    descKo: "흑백요리사2 애니메이션 오프닝 'MOVING ON' - AI 생성 애니 뮤직비디오",
    descEn: "Culinary Battle Season 2 Anime Opening 'MOVING ON' - AI Generated Anime Music Video",
    genre: "애니메이션/MV",
    contentType: "horizontal-anime-mv",
    aspectRatio: "16:9",
    localVideoPath: "/demo-video/cooking-anime-mv.mp4",
    previewVideoUrl: "/demo-video/cooking-anime-mv.mp4",
    detailVideoUrl: "/demo-video/cooking-anime-mv.mp4",
    thumbnailUrl: "/demo-video/cooking-anime-mv-thumb.jpg",
    isHot: true,
    viewCount: "3.5M",
    workflows: [
      {
        id: "scene-analyze",
        title: "Scene Analysis",
        titleKo: "씬별 분석",
        description: "Analyze video by scenes - extract frames, composition, lighting, movement",
        descriptionKo: "씬별 영상 분석 - 프레임, 구도, 조명, 무브먼트 추출",
        icon: "Eye",
        href: "/dimension/reference-decoder",
        badge: "필수",
        stepNumber: 1,
      },
      {
        id: "character-dna",
        title: "Character DNA",
        titleKo: "캐릭터 DNA",
        description: "Extract visual and psychological DNA for each character (max 3)",
        descriptionKo: "캐릭터별 시각적+심리적 DNA 추출 (최대 3명)",
        icon: "Brain",
        href: "/dimension/abyss",
        badge: "필수",
        stepNumber: 2,
      },
      {
        id: "style-guide",
        title: "Style Guide",
        titleKo: "스타일 가이드",
        description: "Auteur blending, color palette, lighting rules, composition guide",
        descriptionKo: "오뜨르 블렌딩, 색감 팔레트, 조명 규칙, 구도 가이드",
        icon: "Palette",
        href: "/dimension/aesthetic",
        badge: "스타일",
        stepNumber: 3,
      },
      {
        id: "character-setup",
        title: "Character Consistency",
        titleKo: "캐릭터 일관성",
        description: "Register character references (StoryMem + Veo Ingredients)",
        descriptionKo: "캐릭터 참조 이미지 등록 (StoryMem + Veo Ingredients)",
        icon: "Users",
        href: "/dimension/visual-realizer",
        badge: "일관성",
        stepNumber: 4,
      },
      {
        id: "bgm",
        title: "BGM Generation",
        titleKo: "BGM 생성",
        description: "Generate similar style BGM with Suno V5 (4min track)",
        descriptionKo: "Suno V5로 유사 스타일 BGM 생성 (4분 트랙)",
        icon: "Music",
        href: "/dimension/suno",
        badge: "BGM",
        stepNumber: 5,
      },
      {
        id: "scene-generate",
        title: "Scene Generation",
        titleKo: "씬별 영상 생성",
        description: "Generate scenes with VEO/Kling + Character Ingredients + Scene Extension",
        descriptionKo: "VEO/Kling으로 씬 생성 + 캐릭터 인그레디언트 + 씬 연결",
        icon: "Video",
        href: "/dimension/kling",
        badge: "씬생성",
        stepNumber: 6,
      },
    ],
  },
};

/**
 * 홈페이지 IP 카드 리스트용
 * DEMO_IP_OVERRIDES의 값을 배열로 변환
 */
export const DEMO_IP_LIST = Object.values(DEMO_IP_OVERRIDES);

/**
 * 콘텐츠 유형별 IP 필터링
 */
export function getIPsByContentType(contentType: ContentType): DemoIPOverride[] {
  return DEMO_IP_LIST.filter((ip) => ip.contentType === contentType);
}

/**
 * Rail 1: 세로 숏폼 웹드라마 (9:16)
 */
export const VERTICAL_SHORTFORM_IPS = getIPsByContentType("vertical-shortform");

/**
 * Rail 2: 가로 애니 뮤비 (16:9)
 */
export const HORIZONTAL_ANIME_MV_IPS = getIPsByContentType("horizontal-anime-mv");

/**
 * slug로 데모 IP 오버라이드 조회
 * @param slug IP slug
 * @returns DemoIPOverride 또는 null
 */
export function getDemoIPOverride(slug: string): DemoIPOverride | null {
  return DEMO_IP_OVERRIDES[slug] ?? null;
}

/**
 * IP 데이터에서 비디오 URL을 우선순위에 따라 선택
 * 우선순위: demo.detailVideoUrl → ip.preview_video_url → ip.banner_url → ip.thumbnail_url
 */
export function resolveVideoUrl(
  ipData: {
    preview_video_url?: string | null;
    banner_url?: string | null;
    thumbnail_url?: string | null;
  },
  demoOverride: DemoIPOverride | null
): { videoUrl: string | null; posterUrl: string | null } {
  const videoUrl =
    demoOverride?.detailVideoUrl ||
    ipData.preview_video_url ||
    null;

  const posterUrl =
    ipData.banner_url ||
    ipData.thumbnail_url ||
    demoOverride?.thumbnailUrl ||
    null;

  return { videoUrl, posterUrl };
}

/**
 * DemoIPOverride를 IPDetail 형식으로 변환
 * 백엔드 없이 데모 IP 상세 페이지를 렌더링하기 위한 synthetic 데이터 생성
 */
export interface SyntheticIPDetail {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  thumbnail_url: string | null;
  banner_url: string | null;
  preview_video_url: string | null;
  genre: string[];
  tags: string[];
  worldbuilding: Record<string, unknown>;
  license_status: "allowed" | "restricted" | "prohibited";
  preset_count: number;
  generation_count: number;
  presets: SyntheticPreset[];
}

export interface SyntheticPreset {
  id: string;
  name_ko: string;
  name_en: string;
  description_ko: string | null;
  description_en: string | null;
  thumbnail_url: string | null;
  preset_type: string;
  estimated_credits: number;
  estimated_duration_seconds: number;
  is_featured: boolean;
}

export interface SyntheticIPRights {
  license_status: "allowed" | "restricted" | "prohibited";
  territory: string[];
  blocked_territory: string[];
  scope: string;
  commercial_ok: boolean;
  expiry: string | null;
}

/**
 * 데모 IP가 존재하는지 확인
 */
export function isDemoIP(slug: string): boolean {
  return slug in DEMO_IP_OVERRIDES;
}

/**
 * DemoIPOverride를 IPDetail 형식으로 변환
 */
export function createSyntheticIPDetail(demo: DemoIPOverride): SyntheticIPDetail {
  // 기본 프리셋 생성 (데모용)
  const defaultPresets: SyntheticPreset[] = [
    {
      id: `${demo.slug}-preset-1`,
      name_ko: "기본 생성",
      name_en: "Default Generation",
      description_ko: "이 IP의 스타일로 새로운 콘텐츠를 생성합니다",
      description_en: "Generate new content in this IP's style",
      thumbnail_url: demo.thumbnailUrl || null,
      preset_type: "generation",
      estimated_credits: 50,
      estimated_duration_seconds: 180,
      is_featured: true,
    },
    {
      id: `${demo.slug}-preset-2`,
      name_ko: "스타일 변주",
      name_en: "Style Variation",
      description_ko: "다른 아트 스타일로 변환합니다",
      description_en: "Transform to different art styles",
      thumbnail_url: demo.thumbnailUrl || null,
      preset_type: "variation",
      estimated_credits: 30,
      estimated_duration_seconds: 120,
      is_featured: false,
    },
  ];

  return {
    id: `demo-${demo.slug}`,
    slug: demo.slug,
    name_ko: demo.titleKo,
    name_en: demo.titleEn,
    description_ko: demo.descKo,
    description_en: demo.descEn,
    thumbnail_url: demo.thumbnailUrl || null,
    banner_url: demo.thumbnailUrl || null,
    preview_video_url: demo.detailVideoUrl || demo.previewVideoUrl || null,
    genre: [demo.genre],
    tags: demo.contentType ? [demo.contentType, demo.aspectRatio || "16:9"] : [],
    worldbuilding: {},
    license_status: "allowed",
    preset_count: defaultPresets.length,
    generation_count: parseInt(demo.viewCount?.replace(/[^0-9]/g, "") || "0") || 1000,
    presets: defaultPresets,
  };
}

/**
 * 데모 IP의 기본 권리 정보 생성
 */
export function createSyntheticIPRights(): SyntheticIPRights {
  return {
    license_status: "allowed",
    territory: ["KR", "US", "JP", "WW"],
    blocked_territory: [],
    scope: "fan_creation",
    commercial_ok: false,
    expiry: null,
  };
}

/**
 * slug로 데모 IP의 synthetic 데이터 조회
 * @returns { ipDetail, ipRights } 또는 null
 */
export function getDemoIPData(slug: string): { ipDetail: SyntheticIPDetail; ipRights: SyntheticIPRights } | null {
  const demo = getDemoIPOverride(slug);
  if (!demo) return null;

  return {
    ipDetail: createSyntheticIPDetail(demo),
    ipRights: createSyntheticIPRights(),
  };
}
