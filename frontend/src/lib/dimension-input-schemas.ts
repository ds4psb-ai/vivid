/**
 * Dimension Input Schemas - SSoT for inputFields across all dimension tools.
 *
 * This module centralizes all input field configurations that were previously
 * scattered across DimensionPortalModal and individual Panel components.
 */

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
                placeholder: "분석할 레퍼런스 영상을 설명하세요",
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
                label: "타입",
                type: "select",
                defaultValue: "prompt",
                options: [
                    { value: "prompt", label: "프롬프트" },
                    { value: "storyboard", label: "스토리보드" },
                    { value: "general", label: "일반" },
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
                defaultValue: "wong",
                options: [
                    { value: "wong", label: "왕가위" },
                    { value: "bong", label: "봉준호" },
                    { value: "park", label: "박찬욱" },
                    { value: "shinkai", label: "신카이 마코토" },
                    { value: "nolan", label: "크리스토퍼 놀란" },
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
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get input fields for a specific dimension.
 * Returns empty array if dimension not found.
 */
export function getInputFieldsByDimension(dimension: string): InputFieldConfig[] {
    return DIMENSION_INPUT_SCHEMAS[dimension]?.inputFields ?? [];
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
