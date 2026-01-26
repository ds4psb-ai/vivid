/**
 * Dimension Input Schemas - SSoT for inputFields across all dimension tools.
 *
 * This module centralizes all input field configurations that were previously
 * scattered across DimensionPortalModal and individual Panel components.
 */

import { dimensionIdToCode } from "@/lib/tokens";

// =============================================================================
// Types
// =============================================================================

export interface InputFieldOption {
    value: string;
    label: string;
}

export interface InputFieldConfig {
    key: string;
    label: string;
    type: "text" | "textarea" | "select" | "toggle";
    placeholder?: string;
    options?: InputFieldOption[];
    required?: boolean;
    defaultValue?: string;
}

export interface DimensionInputSchema {
    inputFields: InputFieldConfig[];
}

// =============================================================================
// Input Schemas by Dimension
// =============================================================================

export const DIMENSION_INPUT_SCHEMAS: Record<string, DimensionInputSchema> = {
    "1D": {
        inputFields: [
            {
                key: "topic",
                label: "주제",
                type: "textarea",
                placeholder: "영상의 핵심 주제를 입력하세요...",
                required: true,
            },
            {
                key: "style",
                label: "스타일",
                type: "select",
                defaultValue: "cinematic",
                options: [
                    { value: "cinematic", label: "시네마틱" },
                    { value: "documentary", label: "다큐멘터리" },
                    { value: "commercial", label: "광고/커머셜" },
                    { value: "artistic", label: "아트/실험" },
                    { value: "vlog", label: "브이로그" },
                ],
            },
            {
                key: "mood",
                label: "무드",
                type: "select",
                defaultValue: "neutral",
                options: [
                    { value: "neutral", label: "중립" },
                    { value: "dramatic", label: "드라마틱" },
                    { value: "calm", label: "차분함" },
                    { value: "energetic", label: "에너지틱" },
                    { value: "melancholic", label: "멜랑콜릭" },
                ],
            },
            {
                key: "duration",
                label: "길이",
                type: "select",
                defaultValue: "15 seconds",
                options: [
                    { value: "5 seconds", label: "5초" },
                    { value: "10 seconds", label: "10초" },
                    { value: "15 seconds", label: "15초" },
                    { value: "30 seconds", label: "30초" },
                    { value: "60 seconds", label: "60초" },
                ],
            },
            {
                key: "language",
                label: "언어",
                type: "select",
                defaultValue: "ko",
                options: [
                    { value: "ko", label: "한국어" },
                    { value: "en", label: "English" },
                ],
            },
            {
                key: "model",
                label: "AI 모델",
                type: "select",
                defaultValue: "gemini-3-flash-preview",
                options: [
                    { value: "gemini-3-flash-preview", label: "Flash (빠름)" },
                    { value: "gemini-3-pro-preview", label: "Pro (고품질)" },
                ],
            },
        ],
    },

    "2D": {
        inputFields: [
            {
                key: "concept",
                label: "컨셉",
                type: "textarea",
                placeholder: "스토리보드로 만들 컨셉을 입력하세요",
                required: true,
            },
            {
                key: "scene_count",
                label: "장면 수",
                type: "select",
                defaultValue: "5",
                options: [
                    { value: "3", label: "3장면" },
                    { value: "5", label: "5장면" },
                    { value: "7", label: "7장면" },
                    { value: "10", label: "10장면" },
                ],
            },
        ],
    },

    "3D": {
        inputFields: [
            {
                key: "description",
                label: "장면 설명",
                type: "textarea",
                placeholder: "시각화할 장면을 설명하세요",
                required: true,
            },
            {
                key: "aspect_ratio",
                label: "화면 비율",
                type: "select",
                defaultValue: "16:9",
                options: [
                    { value: "16:9", label: "16:9 (와이드)" },
                    { value: "9:16", label: "9:16 (세로)" },
                    { value: "1:1", label: "1:1 (정방형)" },
                ],
            },
        ],
    },

    "4D": {
        inputFields: [
            {
                key: "video_description",
                label: "영상 설명",
                type: "textarea",
                placeholder: "분석할 레퍼런스 영상을 설명하세요 (또는 URL 입력)",
                required: true,
            },
            {
                key: "focus_areas",
                label: "분석 초점",
                type: "select",
                defaultValue: "composition",
                options: [
                    { value: "composition", label: "구도" },
                    { value: "lighting", label: "조명" },
                    { value: "color", label: "색감" },
                    { value: "movement", label: "움직임" },
                    { value: "editing", label: "편집" },
                    { value: "sound", label: "사운드" },
                    { value: "narrative", label: "내러티브" },
                ],
            },
            {
                key: "analysis_depth",
                label: "분석 깊이",
                type: "select",
                defaultValue: "standard",
                options: [
                    { value: "quick", label: "빠른 분석" },
                    { value: "standard", label: "표준 분석" },
                    { value: "deep", label: "심층 분석" },
                ],
            },
            {
                key: "output_format",
                label: "출력 형식",
                type: "select",
                defaultValue: "structured",
                options: [
                    { value: "structured", label: "구조화된 리포트" },
                    { value: "narrative", label: "서술형" },
                    { value: "bullet", label: "포인트 정리" },
                ],
            },
        ],
    },

    "QC": {
        inputFields: [
            {
                key: "content",
                label: "검수 대상",
                type: "textarea",
                placeholder: "품질 검수할 콘텐츠를 입력하세요",
                required: true,
            },
            {
                key: "content_type",
                label: "콘텐츠 타입",
                type: "select",
                defaultValue: "prompt",
                options: [
                    { value: "prompt", label: "프롬프트" },
                    { value: "storyboard", label: "스토리보드" },
                    { value: "scenario", label: "시나리오" },
                    { value: "image", label: "이미지 설명" },
                    { value: "video", label: "비디오 설명" },
                    { value: "general", label: "일반" },
                ],
            },
            {
                key: "inspection_mode",
                label: "검수 모드",
                type: "select",
                defaultValue: "comprehensive",
                options: [
                    { value: "comprehensive", label: "종합 검수" },
                    { value: "quick", label: "빠른 검수" },
                    { value: "cinematic", label: "영화적 품질" },
                    { value: "consistency", label: "일관성 검사" },
                ],
            },
            {
                key: "threshold",
                label: "품질 기준",
                type: "select",
                defaultValue: "0.7",
                options: [
                    { value: "0.5", label: "기본 (50%)" },
                    { value: "0.7", label: "표준 (70%)" },
                    { value: "0.85", label: "고품질 (85%)" },
                    { value: "0.95", label: "엄격 (95%)" },
                ],
            },
        ],
    },

    "AD": {
        inputFields: [
            {
                key: "concept",
                label: "컨셉",
                type: "textarea",
                placeholder: "미학 방향을 설정할 컨셉",
                required: true,
            },
            {
                key: "reference_style",
                label: "감독 스타일",
                type: "select",
                defaultValue: "bong",
                options: [
                    { value: "bong", label: "강주노" },
                    { value: "park", label: "박찬욱" },
                    { value: "na", label: "나홍진" },
                    { value: "hong", label: "홍상수" },
                    { value: "lee", label: "이창동" },
                    { value: "wong", label: "렌 벨벳" },
                    { value: "epoch", label: "테오 에포크" },
                    { value: "abyss", label: "오리온 어비스" },
                    { value: "azure", label: "신카이 마코토" },
                    { value: "voltage", label: "렉스 볼티지" },
                ],
            },
            {
                key: "lighting_style",
                label: "조명 스타일",
                type: "select",
                defaultValue: "natural",
                options: [
                    { value: "natural", label: "자연광" },
                    { value: "high-key", label: "하이키" },
                    { value: "low-key", label: "로우키" },
                    { value: "dramatic", label: "드라마틱" },
                    { value: "soft", label: "소프트" },
                ],
            },
            {
                key: "color_mood",
                label: "색감/무드",
                type: "select",
                defaultValue: "neutral",
                options: [
                    { value: "neutral", label: "중립" },
                    { value: "warm", label: "따뜻한" },
                    { value: "cool", label: "차가운" },
                    { value: "desaturated", label: "탈색" },
                    { value: "vibrant", label: "비비드" },
                ],
            },
        ],
    },

    "AI": {
        inputFields: [
            {
                key: "subject",
                label: "분석 주제",
                type: "textarea",
                placeholder: "분석할 주제나 대상을 설명하세요",
                required: true,
            },
            {
                key: "user_message",
                label: "메시지",
                type: "textarea",
                placeholder: "추가 컨텍스트를 입력하세요",
                required: false,
            },
        ],
    },

    "VEO": {
        inputFields: [
            {
                key: "prompt",
                label: "비디오 프롬프트",
                type: "textarea",
                placeholder: "생성할 비디오를 설명하세요",
                required: true,
            },
            {
                key: "duration",
                label: "길이",
                type: "select",
                defaultValue: "8",
                options: [
                    { value: "4", label: "4초" },
                    { value: "6", label: "6초" },
                    { value: "8", label: "8초" },
                ],
            },
            {
                key: "aspect_ratio",
                label: "화면 비율",
                type: "select",
                defaultValue: "16:9",
                options: [
                    { value: "16:9", label: "16:9" },
                    { value: "9:16", label: "9:16" },
                    { value: "1:1", label: "1:1" },
                ],
            },
        ],
    },

    "STORY": {
        inputFields: [
            {
                key: "concept",
                label: "컨셉",
                type: "textarea",
                placeholder: "시나리오로 만들 아이디어를 설명하세요",
                required: true,
            },
            {
                key: "genre",
                label: "장르",
                type: "select",
                defaultValue: "drama",
                options: [
                    { value: "drama", label: "드라마" },
                    { value: "thriller", label: "스릴러" },
                    { value: "comedy", label: "코미디" },
                    { value: "documentary", label: "다큐멘터리" },
                    { value: "horror", label: "호러" },
                    { value: "scifi", label: "SF" },
                    { value: "ad", label: "광고" },
                    { value: "mv", label: "뮤직비디오" },
                    { value: "short", label: "숏폼" },
                ],
            },
            {
                key: "structure",
                label: "구조",
                type: "select",
                defaultValue: "3-act",
                options: [
                    { value: "3-act", label: "3막 구조" },
                    { value: "5-act", label: "5막 구조" },
                    { value: "hero-journey", label: "영웅의 여정" },
                    { value: "hook-body-cta", label: "훅-본론-CTA" },
                    { value: "problem-solution", label: "문제-해결" },
                    { value: "story-arc", label: "스토리 아크" },
                    { value: "nonlinear", label: "비선형" },
                    { value: "slice-of-life", label: "일상물" },
                    { value: "montage", label: "몽타주" },
                ],
            },
            {
                key: "duration",
                label: "목표 길이",
                type: "select",
                defaultValue: "60",
                options: [
                    { value: "15", label: "15초 (숏폼)" },
                    { value: "30", label: "30초" },
                    { value: "60", label: "1분" },
                    { value: "180", label: "3분" },
                    { value: "300", label: "5분" },
                ],
            },
            {
                key: "language",
                label: "언어",
                type: "select",
                defaultValue: "ko",
                options: [
                    { value: "ko", label: "한국어" },
                    { value: "en", label: "English" },
                ],
            },
        ],
    },

    "SOUND": {
        inputFields: [
            {
                key: "description",
                label: "사운드 설명",
                type: "textarea",
                placeholder: "원하는 사운드/음악을 설명하세요",
                required: true,
            },
            {
                key: "sound_type",
                label: "사운드 유형",
                type: "select",
                defaultValue: "bgm",
                options: [
                    { value: "bgm", label: "배경음악" },
                    { value: "sfx", label: "효과음" },
                    { value: "ambient", label: "앰비언트" },
                    { value: "voice", label: "보이스오버" },
                ],
            },
            {
                key: "mood",
                label: "무드",
                type: "select",
                defaultValue: "neutral",
                options: [
                    { value: "neutral", label: "중립" },
                    { value: "tense", label: "긴장감" },
                    { value: "upbeat", label: "경쾌함" },
                    { value: "melancholic", label: "멜랑콜릭" },
                    { value: "epic", label: "웅장함" },
                ],
            },
            {
                key: "tempo",
                label: "템포",
                type: "select",
                defaultValue: "medium",
                options: [
                    { value: "slow", label: "느림" },
                    { value: "medium", label: "보통" },
                    { value: "fast", label: "빠름" },
                ],
            },
        ],
    },
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get input fields for a specific dimension.
 * Returns empty array if dimension not found.
 */
export function getInputFieldsByDimension(dimension: string): InputFieldConfig[] {
    const direct = DIMENSION_INPUT_SCHEMAS[dimension];
    if (direct) return direct.inputFields;

    const code = dimensionIdToCode(dimension);
    if (!code) return [];

    const normalized = code.toUpperCase().replace(/-/g, "_");
    return DIMENSION_INPUT_SCHEMAS[normalized]?.inputFields ?? [];
}

/**
 * Get default values for a dimension's inputs.
 * Useful for initializing form state.
 */
export function getDefaultInputValues(dimension: string): Record<string, string> {
    const fields = getInputFieldsByDimension(dimension);
    const defaults: Record<string, string> = {};

    for (const field of fields) {
        if (field.defaultValue) {
            defaults[field.key] = field.defaultValue;
        } else if (field.options && field.options.length > 0) {
            defaults[field.key] = field.options[0].value;
        }
    }

    return defaults;
}
