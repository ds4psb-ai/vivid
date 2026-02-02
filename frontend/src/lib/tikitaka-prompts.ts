/**
 * Tikitaka 6-Step Workflow Prompts
 *
 * SSoT Documentation: viral-video-automation/templates/MODE_TIKITAKA.md
 *
 * This file contains the prompt templates for the 6-step Dual AI workflow.
 * Backend manages state (current step, outputs); Frontend handles prompts and UI.
 */

export type TikitakaAiRole = "gemini" | "claude" | "user";

export interface TikitakaAttachment {
  name: string;
  description: string;
  required: boolean;
}

export interface TikitakaStepConfig {
  name: string;
  aiRole: TikitakaAiRole;
  promptTemplate: string;
  attachments: TikitakaAttachment[];
  expectedOutput: string;
  tips: string[];
}

export const TIKITAKA_STEPS: Record<number, TikitakaStepConfig> = {
  1: {
    name: "Success Brief",
    aiRole: "gemini",
    promptTemplate: `[영상 파일 첨부]

이 영상을 분석해서 아래 항목을 정의해줘:

### 성공 기준
1. **핵심 인물**: 누가 나오는가? (모든 사람, 흐릿해도)
2. **구도**: 정확히 어떤 구도인가? (shot type, angle)
3. **조명**: 색온도, 방향, 분위기
4. **시대**: 1990s vs 2020s
5. **감정**: 어떤 분위기를 전달해야 하는가?

### 잠재적 문제
- 이 씬에서 AI가 실수할 수 있는 것들
- 예: "배경 인물을 서양인으로 생성할 수 있음"

### 출력 형식
JSON으로 구조화해서 출력`,
    attachments: [
      { name: "원본 영상", description: "분석할 원본 영상 파일", required: true },
      { name: "키프레임", description: "추출된 키프레임 (있다면)", required: false },
    ],
    expectedOutput: "JSON 형식의 성공 기준 정의",
    tips: [
      "Gemini CLI에서 @파일명 형식으로 영상 첨부",
      "영상 전체 분위기와 세부 요소 모두 분석하도록 요청",
      "잠재적 문제점을 미리 파악하는 것이 핵심",
    ],
  },
  2: {
    name: "Draft",
    aiRole: "claude",
    promptTemplate: `아래 JSON을 기반으로 각 씬의 프롬프트 초안을 만들어줘.

[Gemini JSON 붙여넣기]

### 규칙
1. ALL PEOPLE Rule 적용 (모든 인물 한국인 명시)
2. 복수 레퍼런스 시 라벨링 필수
3. 도구별 형식 (NanoBanana = 한글, MJ = 영어+파라미터)
4. error_prevention → --no 변환`,
    attachments: [
      { name: "Gemini JSON", description: "STEP 1에서 받은 JSON 출력", required: true },
    ],
    expectedOutput: "도구별 프롬프트 초안 (NanoBanana, MJ, Kling, Veo)",
    tips: [
      "ALL PEOPLE Rule: 배경 인물 포함 모든 사람 한국인 명시",
      "복수 이미지 참조 시 Image 1, Image 2 라벨링",
      "각 도구 형식에 맞게 변환",
    ],
  },
  3: {
    name: "Critique",
    aiRole: "gemini",
    promptTemplate: `[원본 영상 파일 첨부]

아래 프롬프트 초안을 원본 영상과 비교하며 비평해줘.

[Claude 초안 붙여넣기]

### 비평 관점
1. **완전성**: 원본 영상의 모든 인물이 한국인으로 명시되었는가?
2. **구체성**: 모호한 표현이 있는가?
3. **일관성**: ANCHOR와 다른 씬이 연결되는가?
4. **에러 방지**: --no에 빠진 항목이 있는가?
5. **도구 적합성**: 도구별 형식이 맞는가?

### 출력 형식
각 씬별로:
- 문제점
- 개선 제안`,
    attachments: [
      { name: "원본 영상", description: "원본 영상 파일 (프롬프트와 비교용)", required: true },
      { name: "Claude 초안", description: "STEP 2에서 만든 프롬프트 초안", required: true },
    ],
    expectedOutput: "씬별 문제점과 개선 제안",
    tips: [
      "원본 영상을 꼭 첨부해서 비교 분석하도록",
      "5가지 비평 관점 모두 체크하도록 요청",
      "구체적인 개선 방향이 나오도록 유도",
    ],
  },
  4: {
    name: "Revise",
    aiRole: "claude",
    promptTemplate: `Gemini 비평을 반영해서 프롬프트를 수정해줘.

### 원본 초안
[STEP 2 결과]

### Gemini 비평
[STEP 3 결과]

### 수정 규칙
1. 비평에서 지적한 모든 문제 해결
2. 새로운 문제 만들지 않기
3. 변경 사항 설명 포함`,
    attachments: [
      { name: "STEP 2 초안", description: "원본 프롬프트 초안", required: true },
      { name: "STEP 3 비평", description: "Gemini 비평 결과", required: true },
    ],
    expectedOutput: "수정된 프롬프트 + 변경 사항 설명",
    tips: [
      "비평의 모든 지적사항 해결 여부 확인",
      "수정하면서 새로운 문제가 생기지 않도록 주의",
      "변경 사항을 명시적으로 설명",
    ],
  },
  5: {
    name: "Generate + Review",
    aiRole: "user",
    promptTemplate: `### 생성 도구에서 프롬프트 실행

아래 수정된 프롬프트를 선택한 도구에서 실행하세요.

[STEP 4 수정 프롬프트]

### QA 체크리스트
- [ ] 모든 인물 한국인?
- [ ] 배경 인물도 한국인 피부톤?
- [ ] 의상 색깔 원본과 동일?
- [ ] 구도 정확?
- [ ] 조명 맞음?

### 점수 기준
- 85점 이상: PASS (다음 단계)
- 60-84점: REVISE (STEP 6으로)
- 60점 미만: REJECT (STEP 2로)`,
    attachments: [
      { name: "STEP 4 프롬프트", description: "수정 완료된 최종 프롬프트", required: true },
    ],
    expectedOutput: "생성된 이미지/영상 + QA 체크리스트 점수",
    tips: [
      "도구별 프롬프트 탭에서 해당 도구 형식 복사",
      "생성 후 QA 체크리스트로 품질 확인",
      "85점 이상이면 PASS, 아니면 STEP 6으로",
    ],
  },
  6: {
    name: "Micro-adjust",
    aiRole: "user",
    promptTemplate: `### 미세 조정 (재생성 없이)

STEP 5 결과물의 문제점을 미세 조정합니다.

### 일반적인 문제 → 해결책

| 문제 | 해결책 |
|------|--------|
| 배경 인물 서양인 | \`--no background caucasian\` 추가 |
| 케이크 2개 | \`--no cake on table, duplicate cake\` 추가 |
| 의상 색깔 다름 | 프롬프트에 색깔 더 강조 |
| 얼굴 불일치 | \`--cw 80-100\` 올리기 |
| 손 왜곡 | "hands hidden" 또는 단순 포즈 |

### 수정 후
- 85점 이상: PASS → 완료!
- 84점 이하: STEP 5로 돌아가 재생성`,
    attachments: [
      { name: "STEP 5 결과물", description: "생성된 이미지/영상", required: true },
      { name: "QA 피드백", description: "어떤 문제가 있는지", required: true },
    ],
    expectedOutput: "수정된 --no 파라미터 또는 프롬프트 조정",
    tips: [
      "작은 문제는 --no 파라미터로 해결 시도",
      "큰 문제는 STEP 2로 돌아가 근본적 수정",
      "반복하며 85점 이상 도달할 때까지",
    ],
  },
} as const;

/**
 * Get step configuration by step number
 */
export function getTikitakaStep(step: number): TikitakaStepConfig | undefined {
  return TIKITAKA_STEPS[step];
}

/**
 * Get AI role icon
 */
export function getAiRoleIcon(role: TikitakaAiRole): string {
  switch (role) {
    case "gemini":
      return "G"; // Google Gemini
    case "claude":
      return "C"; // Anthropic Claude
    case "user":
      return "U"; // User action
  }
}

/**
 * Get AI role display name
 */
export function getAiRoleDisplayName(role: TikitakaAiRole): string {
  switch (role) {
    case "gemini":
      return "Gemini";
    case "claude":
      return "Claude";
    case "user":
      return "You";
  }
}

/**
 * Get AI role color class
 */
export function getAiRoleColorClass(role: TikitakaAiRole): string {
  switch (role) {
    case "gemini":
      return "text-blue-500 bg-blue-500/10";
    case "claude":
      return "text-orange-500 bg-orange-500/10";
    case "user":
      return "text-green-500 bg-green-500/10";
  }
}

/**
 * Parameter Guide for tool-specific prompts
 */
export interface ParameterGuide {
  param: string;
  description: string;
  example: string;
  impact: "critical" | "important" | "optional";
}

export interface CommonIssue {
  problem: string;
  solution: string;
}

export interface ToolConfig {
  id: string;
  name: string;
  url: string;
  format: "korean" | "english" | "english_with_params";
  icon: string;
  parameterGuide?: ParameterGuide[];
  commonIssues?: CommonIssue[];
}

/**
 * Tool configurations with parameter guides
 */
export const TOOL_CONFIGS: Record<string, ToolConfig> = {
  nanobanana: {
    id: "nanobanana",
    name: "NanoBanana",
    url: "https://nanobanana.ai",
    format: "korean",
    icon: "NB",
    parameterGuide: [
      { param: "--no", description: "제거 요소", example: "--no caucasian background", impact: "critical" },
      { param: "--seed", description: "재현성", example: "--seed 42", impact: "optional" },
      { param: "--ar", description: "화면비", example: "--ar 16:9", impact: "important" },
    ],
    commonIssues: [
      { problem: "배경 인물 서양인", solution: "--no background caucasian 추가" },
      { problem: "중복 요소 생성", solution: "--no duplicate 추가" },
    ],
  },
  midjourney: {
    id: "midjourney",
    name: "MJ V7",
    url: "https://discord.com/channels/@me",
    format: "english_with_params",
    icon: "MJ",
    parameterGuide: [
      { param: "--cw", description: "캐릭터 가중치", example: "--cw 80-100", impact: "critical" },
      { param: "--cref", description: "캐릭터 레퍼런스", example: "--cref <url>", impact: "critical" },
      { param: "--ar", description: "화면비", example: "--ar 16:9", impact: "important" },
      { param: "--v", description: "버전", example: "--v 7", impact: "important" },
      { param: "--no", description: "제거 요소", example: "--no deformed hands", impact: "critical" },
      { param: "--style", description: "스타일", example: "--style raw", impact: "optional" },
    ],
    commonIssues: [
      { problem: "얼굴 불일치", solution: "--cw 90-100으로 올리기" },
      { problem: "손 왜곡", solution: "--no deformed hands 또는 hands hidden 포즈" },
      { problem: "배경 인물 서양인", solution: "--no caucasian background people 추가" },
    ],
  },
  kling: {
    id: "kling",
    name: "Kling 2.6",
    url: "https://klingai.com",
    format: "english",
    icon: "KL",
    parameterGuide: [
      { param: "duration", description: "영상 길이", example: "3-5초 권장", impact: "important" },
      { param: "camera", description: "카메라 움직임", example: "subtle pan, dolly", impact: "optional" },
      { param: "reference", description: "이미지 레퍼런스", example: "Upload reference image", impact: "critical" },
    ],
    commonIssues: [
      { problem: "급격한 움직임", solution: "subtle, slow motion 키워드 추가" },
      { problem: "캐릭터 불일치", solution: "Strong reference image 업로드" },
    ],
  },
  veo: {
    id: "veo",
    name: "Veo 3.1",
    url: "https://labs.google/fx/tools/veo",
    format: "english",
    icon: "VE",
    parameterGuide: [
      { param: "duration", description: "영상 길이", example: "4-6초 최적", impact: "important" },
      { param: "motion", description: "움직임 명시", example: "smooth dolly forward", impact: "critical" },
      { param: "style", description: "스타일", example: "photorealistic, cinematic", impact: "optional" },
    ],
    commonIssues: [
      { problem: "정적인 영상", solution: "camera movement 명시적 기술" },
      { problem: "인물 왜곡", solution: "subtle movement만 요청" },
    ],
  },
};

export type ToolId = keyof typeof TOOL_CONFIGS;

/**
 * Critique verdict thresholds
 */
export const VERDICT_THRESHOLDS = {
  PASS: 85,
  REVISE_MIN: 60,
} as const;

/**
 * Get verdict based on score
 */
export function getVerdict(score: number): "PASS" | "REVISE" | "REJECT" {
  if (score >= VERDICT_THRESHOLDS.PASS) return "PASS";
  if (score >= VERDICT_THRESHOLDS.REVISE_MIN) return "REVISE";
  return "REJECT";
}

/**
 * Get verdict color class
 */
export function getVerdictColorClass(verdict: "PASS" | "REVISE" | "REJECT"): string {
  switch (verdict) {
    case "PASS":
      return "text-green-500 bg-green-500/10";
    case "REVISE":
      return "text-yellow-500 bg-yellow-500/10";
    case "REJECT":
      return "text-red-500 bg-red-500/10";
  }
}
