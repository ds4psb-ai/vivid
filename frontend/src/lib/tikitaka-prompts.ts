/**
 * Tikitaka 6-Step Workflow Prompts
 *
 * SSoT Documentation:
 * - viral-video-automation/templates/MODE_TIKITAKA.md
 * - viral-video-automation/templates/STAGE1_ANALYSIS.md
 * - viral-video-automation/templates/PROMPTS_NANOBANANA.md
 * - viral-video-automation/templates/PROMPTS_MIDJOURNEY.md
 * - viral-video-automation/templates/VIDEO_KLING.md
 * - viral-video-automation/templates/VIDEO_VEO.md
 * - viral-video-automation/templates/CRITIQUE_IMAGE.md
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

export interface TikitakaActionGuide {
  goal: string;           // 목표
  tool: string;           // 열기
  attachPath?: string;    // 첨부
  savePath: string;       // 저장
}

export interface TikitakaStepConfig {
  name: string;
  aiRole: TikitakaAiRole;
  promptTemplate: string;
  attachments: TikitakaAttachment[];
  expectedOutput: string;
  tips: string[];
  actionGuide: TikitakaActionGuide;
}

// =============================================================================
// STEP 1: SUCCESS BRIEF (Gemini) - STAGE1_ANALYSIS.md 전체 반영
// =============================================================================

const STEP1_PROMPT_TEMPLATE = `[영상 파일 첨부]

당신은 영상 분석 전문가입니다. 첨부된 영상을 분석해주세요.

## 요청 사항

### 1. 컷 분해 테이블 (0.01초 정밀도)
각 씬을 0.01초 단위로 정밀하게 분석하여 아래 테이블을 완성하세요:

| Scene | Start | End | Duration | Camera | Subject | Action |
|-------|-------|-----|----------|--------|---------|--------|
| 1 | 0:00.00 | 0:02.34 | 2.34s | Medium shot | 가족 | 케이크 들고 입장 |
| 2 | 0:02.34 | 0:05.67 | 3.33s | Close-up | 아이 | 촛불 바라보기 |
| ... | ... | ... | ... | ... | ... | ... |

### 2. 캐릭터 프로파일
등장하는 모든 인물에 대해:

**주인공 (아이)**
- 예상 나이: 7세
- 성별: 남아
- 민족: 한국인 (필수 명시)
- 피부톤: 한국인 피부톤
- 헤어스타일: 단발머리 (1990년대 스타일)
- 의상: 스트라이프 티셔츠 (색상 명시)
- 표정/감정: 수줍은 설렘, 기대감
- 특징: 홑꺼풀, 동그란 볼

**부모/가족**
- 아빠: 초록 셔츠, 한국인, 위치(왼쪽 배경)
- 엄마: 빨간 스웨터, 한국인, 위치(오른쪽 배경)
- 기타 배경 인물: 모두 한국인 명시

### 3. 비주얼 스타일 분석
- **색온도**: [K 값] (예: 3200K 텅스텐, 6500K LED)
- **컬러 팔레트**: [지배적 HEX 코드들]
- **필름 스타일**: [Kodak Portra 400, 디지털 샤프 등]
- **조명 방향**: [언더라이팅, 키라이트 등]
- **시대 분위기**: [1990s vs 2020s]

### 4. ANCHOR 씬 추천 (매우 중요)
캐릭터 일관성을 위해 "앵커"로 사용할 가장 좋은 씬을 추천하세요.

**선정 기준:**
- 얼굴이 가장 선명하게 보이는 씬
- 조명이 균일하고 좋은 씬
- 표정이 중립적이거나 자연스러운 씬
- 정면 또는 3/4 앵글인 씬

**추천 형식:**
- 추천 씬 번호: Scene [N]
- 선정 이유: [구체적 근거]
- 타임스탬프: [시작-끝]

### 5. 9-Grid 위치 시스템
각 씬의 주요 피사체 위치를 9-Grid로 표시:

\`\`\`
[1][2][3]
[4][5][6]  → 중앙(5), 왼쪽(4), 오른쪽(6)
[7][8][9]
\`\`\`

### 6. 잠재적 문제 (Error Prevention)
이 씬에서 AI가 실수할 수 있는 것들을 미리 파악:

- "배경 인물을 서양인으로 생성할 수 있음"
- "1990년대인데 스마트폰이 등장할 수 있음"
- "LED 조명을 사용할 수 있음 (시대 오류)"
- "의상 색깔을 다르게 생성할 수 있음"
- "손가락이 6개로 생성될 수 있음"

### 7. 시대별 금지 요소 (--no 리스트)

**1990년대 씬:**
\`--no western features, caucasian skin, blonde, blue eyes, smartphones, LED lights, modern furniture, sharp digital look\`

**2020년대 씬:**
\`--no warm lighting, candles, tungsten, genuine happiness, film grain, retro furniture\`

### 출력 형식
JSON으로 구조화해서 출력:

\`\`\`json
{
  "project_name": "생일 영상",
  "total_scenes": 8,
  "total_duration": "45.32s",
  "era": "1990s",
  "anchor_scene": {
    "scene_number": 2,
    "timestamp": "0:02.34-0:05.67",
    "reason": "얼굴 가장 선명, 조명 최적"
  },
  "scenes": [...],
  "characters": {...},
  "visual_style": {...},
  "error_prevention": [...]
}
\`\`\``;

// =============================================================================
// STEP 2: DRAFT (Claude) - 도구별 프롬프트 생성
// =============================================================================

const STEP2_PROMPT_TEMPLATE = `아래 Gemini JSON을 기반으로 각 씬의 프롬프트 초안을 만들어줘.

[Gemini JSON 붙여넣기]

## 핵심 규칙

### 1. ALL PEOPLE Rule (절대 규칙)
- **모든 인물**을 "한국인"으로 명시 (흐릿한 배경 인물 포함!)
- "Korean" 키워드 필수 사용
- 피부톤: "한국인 피부톤" 또는 "Korean skin tone"
- 눈: "홑꺼풀" 또는 "single eyelids"

### 2. 복수 레퍼런스 라벨링
2개 이상 이미지 참조 시:
- **Image 1 (구도용)**: [scene.png]
- **Image 2 (얼굴용)**: [ANCHOR.png]

### 3. 도구별 형식 변환
- NanoBanana = **한글** 프롬프트
- Midjourney = **영어** + 파라미터 (--iw, --cw, --oref, --no)

### 4. Error Prevention → --no 변환
JSON의 error_prevention 항목을 --no 파라미터로 변환:
\`--no western features, caucasian skin, blonde, modern furniture\`

---

## 출력 형식

각 도구별로 프롬프트를 생성해줘:

### NanoBanana (한글)
### Midjourney V7 (영어 + 파라미터)
### Kling 2.6 (영상)
### Veo 3.1 (대사 있는 영상)`;

// =============================================================================
// STEP 3: CRITIQUE (Gemini) - CRITIQUE_IMAGE.md 5차원 평가 반영
// =============================================================================

const STEP3_PROMPT_TEMPLATE = `[원본 영상 파일 첨부]

아래 프롬프트 초안을 원본 영상과 비교하며 비평해줘.

[Claude 초안 붙여넣기]

---

## 5차원 23항목 평가 체크리스트

### 1. 프롬프트 준수 (Prompt Adherence) - 6항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| **주제(Subject)** 정확히 표현됨 | | |
| **배경/환경** 의도대로 명시됨 | | |
| **조명/색감** K값 명시, 방향 정확 | | |
| **스타일** 요청(1990s/2020s) 반영 | | |
| **누락된 요소** 없음 | | |
| **불필요한 추가 요소** 없음 | | |

### 2. 미적 품질 (Aesthetic Quality) - 4항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| **구도** 원본과 동일 (삼각/역삼각 등) | | |
| **색감 조화** 시대에 맞는 팔레트 | | |
| **조명** 자연스럽고 분위기 맞음 | | |
| **전체적 임팩트** 원본 감성 재현 | | |

### 3. 기술적 완성도 (Technical Quality) - 4항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| **해상도/선명도** 충분히 요청됨 | | |
| **텍스처** 필름 그레인 등 명시 | | |
| **노이즈/그레인** 시대에 맞게 요청 | | |
| **아티팩트 방지** --no 포함 | | |

### 4. 캐릭터 일관성 (Consistency) - 5항목 ⭐ 가장 중요
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| **얼굴** ANCHOR 참조 명시 | | |
| **헤어스타일** 원본과 동일 명시 | | |
| **민족/피부톤** 한국인 명시 (ALL PEOPLE) | | |
| **의상** 색상/스타일 정확히 명시 | | |
| **나이** 적절하게 표현됨 | | |

### 5. 해부학/물리 방지 (Anatomy/Physics) - 4항목
| 항목 | ✅/❌ | 메모 |
|------|------|------|
| **손** --no 6 fingers, deformed hands 포함 | | |
| **얼굴** 왜곡 방지 문구 포함 | | |
| **신체 비율** 자연스러움 요청 | | |
| **물리적 논리** 중력, 그림자 언급 | | |

---

## 비평 관점 (5가지)

1. **완전성**: 원본 영상의 **모든 인물**이 한국인으로 명시되었는가?
   - 배경 흐릿한 인물도 포함되었는가?

2. **구체성**: 모호한 표현이 있는가?
   - "따뜻한 조명" → "3200K 텅스텐 조명"으로 구체화 필요

3. **일관성**: ANCHOR와 다른 씬이 연결되는가?
   - --oref, --cw 파라미터 적절한가?

4. **에러 방지**: --no에 빠진 항목이 있는가?
   - 시대별 금지 요소 모두 포함?

5. **도구 적합성**: 도구별 형식이 맞는가?
   - MJ: --iw, --oref, --cw, --ar, --v 7
   - NB: 한글, --no

---

## 출력 형식

### 총점: [XX]/100

### 판정
- ✅ **PASS** (85점 이상): 바로 사용 가능
- 🔄 **REVISE** (60-84점): 수정 후 재생성
- ❌ **REJECT** (60점 미만): 프롬프트 전면 재작성

### 강점 (Keep)
-

### 약점 (Fix)
-

### 씬별 개선 제안
| 씬 | 문제점 | 개선 방향 |
|----|--------|----------|
| Scene 1 | | |
| Scene 2 | | |

### 다음 프롬프트 수정 사항
\`\`\`
(구체적인 수정된 프롬프트 또는 파라미터)
\`\`\``;

// =============================================================================
// STEP 4: REVISE (Claude) - 비평 반영 수정
// =============================================================================

const STEP4_PROMPT_TEMPLATE = `Gemini 비평을 반영해서 프롬프트를 수정해줘.

### 원본 초안
[STEP 2 결과]

### Gemini 비평
[STEP 3 결과]

---

## 수정 규칙

### 1. 비평 지적사항 모두 해결
- 각 약점(Fix) 항목 하나씩 해결
- 씬별 개선 제안 모두 반영

### 2. 새로운 문제 만들지 않기
- 수정하면서 기존 강점(Keep) 유지
- --no 항목 삭제하지 않기

### 3. 변경 사항 명시적 설명
각 수정에 대해:
- Before: [원본]
- After: [수정본]
- 이유: [왜 수정했는지]

---

## 출력 형식

### 변경 로그
| 항목 | Before | After | 이유 |
|------|--------|-------|------|
| Scene 1 조명 | "따뜻한 조명" | "3200K 텅스텐" | 구체화 |
| Scene 2 인물 | "배경 인물" | "배경 한국인 친척들" | ALL PEOPLE |

### 수정된 프롬프트 (최종)

**NanoBanana (한글):**
[수정된 전체 프롬프트]

**Midjourney V7:**
[수정된 전체 프롬프트]

**Kling 2.6:**
[수정된 전체 프롬프트]

**Veo 3.1:**
[수정된 전체 프롬프트]`;

// =============================================================================
// STEP 5: GENERATE + REVIEW (User)
// =============================================================================

const STEP5_PROMPT_TEMPLATE = `### 생성 도구에서 프롬프트 실행

아래 수정된 프롬프트를 선택한 도구에서 실행하세요.

[STEP 4 수정 프롬프트]

---

## QA 체크리스트 (생성 후 확인)

### 캐릭터 일관성 (가장 중요)
- [ ] 모든 인물이 한국인인가? (피부톤, 눈 모양)
- [ ] 배경 인물도 한국인 피부톤인가?
- [ ] 주인공 얼굴이 ANCHOR와 일치하는가?
- [ ] 헤어스타일이 원본과 동일한가?

### 구도/조명
- [ ] 구도가 원본과 정확히 일치하는가?
- [ ] 의상 색깔이 원본과 동일한가?
- [ ] 조명 색온도가 맞는가? (3200K/6500K)
- [ ] 시대 분위기가 맞는가? (1990s/2020s)

### 기술적 품질
- [ ] 손가락 수가 정확한가? (5개)
- [ ] 얼굴 왜곡이 없는가?
- [ ] 아티팩트가 없는가?
- [ ] 해상도가 충분한가?

---

## 점수 기준

| 점수 | 판정 | 다음 액션 |
|------|------|----------|
| **85점 이상** | ✅ PASS | 다음 씬으로 진행 |
| **60-84점** | 🔄 REVISE | STEP 6 (Micro-adjust)로 |
| **60점 미만** | ❌ REJECT | STEP 2로 돌아가기 |

---

## 일반적인 문제 → 해결책

| 문제 | 해결책 |
|------|--------|
| 배경 인물 서양인 | \`--no background caucasian\` 추가 |
| 얼굴 불일치 | \`--cw 80-100\` 올리기, \`--oref\` 확인 |
| 손 왜곡 | \`--no deformed hands, 6 fingers\` 추가 |
| 의상 색깔 다름 | 프롬프트에 색깔 더 강조 (Korean::2) |
| 조명 안맞음 | K 값 명시 (3200K/6500K) |`;

// =============================================================================
// STEP 6: MICRO-ADJUST (User)
// =============================================================================

const STEP6_PROMPT_TEMPLATE = `### 미세 조정 (재생성 없이 파라미터 조정)

STEP 5 결과물의 문제점을 미세 조정합니다.

---

## 일반적인 문제 → 해결책

### 캐릭터 관련
| 문제 | 해결책 |
|------|--------|
| 배경 인물 서양인 | \`--no background caucasian, western features\` 추가 |
| 얼굴 불일치 | \`--cw 80-100\` 올리기 |
| 피부톤 밝음 | \`Korean skin tone::2\` 강조 |
| 헤어스타일 다름 | 구체적 스타일 명시 (bowl cut, 단발) |

### 구도/조명 관련
| 문제 | 해결책 |
|------|--------|
| 구도 무시됨 | \`--iw 2.5\` 또는 \`--iw 3.0\` 올리기 |
| 조명 차가움 | \`--no cold lighting, LED\` + \`3200K tungsten\` |
| 조명 따뜻함 | \`--no warm lighting, candles\` + \`6500K LED\` |

### 오브젝트 관련
| 문제 | 해결책 |
|------|--------|
| 케이크 2개 | \`--no duplicate cake, cake on table\` |
| 현대 가구 | \`--no modern furniture, IKEA style\` |
| 스마트폰 출현 | \`--no smartphones, modern devices\` |

### 해부학 관련
| 문제 | 해결책 |
|------|--------|
| 손가락 6개 | \`--no 6 fingers, extra fingers, deformed hands\` |
| 손 왜곡 | "hands hidden" 또는 단순 포즈 요청 |
| 얼굴 왜곡 | \`--no distorted face, asymmetric features\` |

---

## 수정 후 재확인

- **85점 이상**: ✅ PASS → 완료! 다음 씬으로
- **60-84점**: 🔄 한 번 더 미세 조정
- **60점 미만**: ❌ STEP 2로 돌아가 근본적 수정

---

## MJ V7 파라미터 Quick Reference

| 파라미터 | 범위 | 권장값 | 용도 |
|----------|------|--------|------|
| \`--iw\` | 0-3 | **2.0** | 레퍼런스 이미지 영향력 |
| \`--oref\` | URL | ANCHOR URL | Omni Reference (얼굴 고정) |
| \`--cw\` | 0-100 | **70-90** | 캐릭터 가중치 |
| \`--stylize\` | 0-1000 | 100-250 | 예술적 해석 |
| \`--style raw\` | flag | 사용 | 프롬프트 충실도 최대화 |

---

## Text Weight 활용

\`\`\`
Korean::2 boy        → "Korean"에 2배 가중치
warm tungsten::1.5   → "warm tungsten"에 1.5배
--no caucasian::2    → "caucasian" 강력 제외
\`\`\``;

// =============================================================================
// TIKITAKA STEPS CONFIG
// =============================================================================

export const TIKITAKA_STEPS: Record<number, TikitakaStepConfig> = {
  1: {
    name: "Success Brief",
    aiRole: "gemini",
    promptTemplate: STEP1_PROMPT_TEMPLATE,
    attachments: [
      { name: "원본 영상", description: "분석할 원본 영상 파일", required: true },
      { name: "키프레임", description: "추출된 키프레임 (있다면)", required: false },
    ],
    expectedOutput: "JSON 형식의 성공 기준 정의 (컷 분해, 캐릭터, 스타일, ANCHOR)",
    tips: [
      "Gemini CLI에서 @파일명 형식으로 영상 첨부",
      "0.01초 단위로 정밀하게 컷 분해 요청",
      "ANCHOR 씬 선정이 가장 중요 - 얼굴 선명, 조명 좋은 씬",
      "ALL PEOPLE Rule: 배경 인물도 한국인으로 명시되도록 요청",
      "시대별 --no 리스트 꼭 받기 (1990s vs 2020s)",
    ],
    actionGuide: {
      goal: "영상 분석 -> JSON 출력",
      tool: "Gemini CLI",
      attachPath: "reference/source.mp4",
      savePath: "docs/ANALYSIS.md",
    },
  },
  2: {
    name: "Draft",
    aiRole: "claude",
    promptTemplate: STEP2_PROMPT_TEMPLATE,
    attachments: [
      { name: "Gemini JSON", description: "STEP 1에서 받은 JSON 출력", required: true },
    ],
    expectedOutput: "도구별 프롬프트 초안 (NanoBanana, MJ V7, Kling, Veo)",
    tips: [
      "ALL PEOPLE Rule: 배경 인물 포함 모든 사람 한국인 명시",
      "복수 이미지 참조 시 Image 1, Image 2 라벨링 필수",
      "MJ V7: --iw 2.0, --oref, --cw 70-90 파라미터 필수",
      "error_prevention → --no 변환 빠짐없이",
      "NanoBanana는 한글, MJ는 영어+파라미터",
    ],
    actionGuide: {
      goal: "JSON -> 이미지 프롬프트 초안",
      tool: "Claude Antigravity",
      attachPath: "docs/ANALYSIS.md 내용 복사",
      savePath: "prompts/IMAGE_PROMPTS.md",
    },
  },
  3: {
    name: "Critique",
    aiRole: "gemini",
    promptTemplate: STEP3_PROMPT_TEMPLATE,
    attachments: [
      { name: "원본 영상", description: "원본 영상 파일 (프롬프트와 비교용)", required: true },
      { name: "Claude 초안", description: "STEP 2에서 만든 프롬프트 초안", required: true },
    ],
    expectedOutput: "5차원 23항목 평가 결과 (점수, 판정, 개선 제안)",
    tips: [
      "원본 영상을 꼭 첨부해서 비교 분석",
      "5차원 23항목 체크리스트 모두 평가 요청",
      "캐릭터 일관성(4번) 항목이 가장 중요",
      "구체적인 개선 방향이 나오도록 유도",
      "85점 이상 = PASS, 60-84점 = REVISE, 60점 미만 = REJECT",
    ],
    actionGuide: {
      goal: "프롬프트 초안 비평",
      tool: "Gemini CLI",
      attachPath: "reference/source.mp4 + prompts/IMAGE_PROMPTS.md",
      savePath: "docs/CRITIQUE_LOG.md",
    },
  },
  4: {
    name: "Revise",
    aiRole: "claude",
    promptTemplate: STEP4_PROMPT_TEMPLATE,
    attachments: [
      { name: "STEP 2 초안", description: "원본 프롬프트 초안", required: true },
      { name: "STEP 3 비평", description: "Gemini 비평 결과", required: true },
    ],
    expectedOutput: "수정된 프롬프트 + 변경 사항 로그",
    tips: [
      "비평의 모든 지적사항 해결 여부 확인",
      "수정하면서 새로운 문제가 생기지 않도록 주의",
      "변경 사항을 Before/After로 명시적으로 기록",
      "강점(Keep)은 유지, 약점(Fix)만 수정",
    ],
    actionGuide: {
      goal: "비평 반영 -> 프롬프트 수정",
      tool: "Claude Antigravity",
      attachPath: "prompts/IMAGE_PROMPTS.md + docs/CRITIQUE_LOG.md",
      savePath: "prompts/IMAGE_PROMPTS.md (덮어쓰기)",
    },
  },
  5: {
    name: "Generate + Review",
    aiRole: "user",
    promptTemplate: STEP5_PROMPT_TEMPLATE,
    attachments: [
      { name: "STEP 4 프롬프트", description: "수정 완료된 최종 프롬프트", required: true },
    ],
    expectedOutput: "생성된 이미지/영상 + QA 체크리스트 점수",
    tips: [
      "도구별 프롬프트 탭에서 해당 도구 형식 복사",
      "생성 후 QA 체크리스트로 품질 확인",
      "캐릭터 일관성(한국인, ANCHOR 일치) 가장 먼저 확인",
      "85점 이상이면 PASS, 60-84점이면 STEP 6으로",
    ],
    actionGuide: {
      goal: "이미지/영상 생성 + QA",
      tool: "NanoBanana / MJ V7 / Kling",
      attachPath: "prompts/IMAGE_PROMPTS.md에서 복사",
      savePath: "generated/images/",
    },
  },
  6: {
    name: "Micro-adjust",
    aiRole: "user",
    promptTemplate: STEP6_PROMPT_TEMPLATE,
    attachments: [
      { name: "STEP 5 결과물", description: "생성된 이미지/영상", required: true },
      { name: "QA 피드백", description: "어떤 문제가 있는지", required: true },
    ],
    expectedOutput: "수정된 --no 파라미터 또는 프롬프트 조정",
    tips: [
      "작은 문제는 --no 파라미터로 해결 시도",
      "Text Weight (Korean::2) 활용",
      "--iw 올리면 구도 더 정확, --cw 올리면 얼굴 더 정확",
      "큰 문제는 STEP 2로 돌아가 근본적 수정",
    ],
    actionGuide: {
      goal: "파라미터 미세 조정 -> 재생성",
      tool: "NanoBanana / MJ V7",
      attachPath: "generated/images/에서 문제 이미지 확인",
      savePath: "generated/images/ (재생성)",
    },
  },
} as const;

// =============================================================================
// TOOL-SPECIFIC TEMPLATES (SSoT 반영)
// =============================================================================

export interface ToolSpecificTemplate {
  id: string;
  name: string;
  language: "korean" | "english";
  singleRefTemplate: string;
  multiRefTemplate: string;
  parameterGuide: ParameterGuide[];
  eraSpecificNegatives: Record<string, string>;
  commonIssues: CommonIssue[];
}

// NanoBanana Template (PROMPTS_NANOBANANA.md)
export const NANOBANANA_TEMPLATE: ToolSpecificTemplate = {
  id: "nanobanana",
  name: "NanoBanana Pro",
  language: "korean",
  singleRefTemplate: `이 이미지를 기반으로:
- 구도, 조명, 배경을 정확히 유지
- 모든 인물을 한국인으로 교체
- 옷 색깔과 위치는 원본 그대로

스타일: {{ERA_STYLE}}

금지: {{NEGATIVE_PROMPTS}}`,
  multiRefTemplate: `**Image 1 (구도용)**: [scene.png]
**Image 2 (얼굴용)**: [ANCHOR.png]

Image 1에서 복사:
- 정확한 구도와 인물 배치
- 조명 방향과 색온도 ({{COLOR_TEMP}})
- 옷 색깔 ({{CLOTHING_COLORS}})
- 배경 ({{BACKGROUND}})

Image 2에서 복사:
- 아이 얼굴 ({{FACE_DESCRIPTION}})

교체 대상:
- 모든 인물 → 한국인 (한국인 피부톤, 눈 모양)
- 부모도 한국인 (흐릿해도!)

금지 요소: {{NEGATIVE_PROMPTS}}`,
  parameterGuide: [
    { param: "--no", description: "제거 요소", example: "--no caucasian background, western features", impact: "critical" },
    { param: "--seed", description: "재현성", example: "--seed 42", impact: "optional" },
    { param: "--ar", description: "화면비", example: "--ar 16:9", impact: "important" },
  ],
  eraSpecificNegatives: {
    "1990s": "서양인 특징, 백인 피부, 금발, 파란 눈, 스마트폰, LED 조명, 현대 가구, 샤프한 디지털 느낌",
    "2020s": "따뜻한 조명, 촛불, 텅스텐, 진심 어린 행복, 필름 그레인, 레트로 가구",
  },
  commonIssues: [
    { problem: "배경 인물 서양인", solution: '"흐릿해도 한국인 피부톤" 명시' },
    { problem: "옷 색깔 변경됨", solution: '"Image 1과 같은 옷 색깔" 강조' },
    { problem: "얼굴 불일치", solution: "Character Sheet 먼저 생성" },
    { problem: "텍스트 깨짐", solution: "Nano Banana Pro 사용 (Flash 말고)" },
  ],
};

// Midjourney V7 Template (PROMPTS_MIDJOURNEY.md)
export const MIDJOURNEY_TEMPLATE: ToolSpecificTemplate = {
  id: "midjourney",
  name: "Midjourney V7",
  language: "english",
  singleRefTemplate: `[ANCHOR_IMG.png URL]

Korean::2 {{SUBJECT}}, {{AGE}} years old, {{HAIR_STYLE}}, single eyelids,
{{EXPRESSION}}, {{ACTION}},
{{LIGHTING_DESCRIPTION}}, {{ERA_STYLE}}

--iw 2.0 --ar {{ASPECT_RATIO}} --v 7 --style raw
--no {{NEGATIVE_PROMPTS}}`,
  multiRefTemplate: `[scene.png URL] [ANCHOR.png URL]

**[Image 1: COMPOSITION]** - copy exact layout, positions, clothing colors
**[Image 2: CHARACTER]** - copy Korean {{CHARACTER_ROLE}} face for {{TARGET}}

Korean::2 {{SCENE_DESCRIPTION}}, {{COMPOSITION}},
{{LIGHTING_DESCRIPTION}}, {{ERA_STYLE}}

--iw 2.0 --oref [ANCHOR.png URL] --cw {{CW_VALUE}} --ar {{ASPECT_RATIO}} --v 7 --style raw
--no {{NEGATIVE_PROMPTS}}`,
  parameterGuide: [
    { param: "--iw", description: "Image Weight (레퍼런스 영향력)", example: "--iw 2.0 (권장)", impact: "critical" },
    { param: "--oref", description: "Omni Reference (얼굴/형태 유지)", example: "--oref [ANCHOR URL]", impact: "critical" },
    { param: "--cw", description: "Character Weight", example: "--cw 70-90", impact: "critical" },
    { param: "--stylize", description: "예술적 해석 강도", example: "--stylize 100-250", impact: "important" },
    { param: "--style raw", description: "프롬프트 충실도 최대화", example: "--style raw", impact: "important" },
    { param: "--ar", description: "화면비", example: "--ar 9:16", impact: "important" },
    { param: "--v", description: "버전", example: "--v 7", impact: "important" },
    { param: "--no", description: "제거 요소", example: "--no deformed hands, 6 fingers", impact: "critical" },
    { param: "--draft", description: "빠른 프로토타입 (저비용)", example: "--draft", impact: "optional" },
  ],
  eraSpecificNegatives: {
    "1990s": "western features, caucasian skin, blonde, blue eyes, smartphones, LED lights, modern furniture, sharp digital",
    "2020s": "warm lighting, candles, tungsten, genuine happiness, film grain, retro furniture",
  },
  commonIssues: [
    { problem: "구도 무시됨", solution: "--iw 2.5 또는 --iw 3.0으로 올리기" },
    { problem: "서양인 나옴", solution: "Korean::2 + --no caucasian" },
    { problem: "얼굴 불일치", solution: "--oref [anchor] + --cw 70-90" },
    { problem: "너무 예술적", solution: "--style raw + --stylize 100" },
    { problem: "프로토타입 필요", solution: "--draft 사용" },
  ],
};

// Kling 2.6 Template (VIDEO_KLING.md)
export const KLING_TEMPLATE: ToolSpecificTemplate = {
  id: "kling",
  name: "Kling 2.6",
  language: "english",
  singleRefTemplate: `**Elements:**
- Element 1: 주인공 얼굴 (ANCHOR.png)
- Element 2: 씬 구도 (scene.png)

**Text Prompt:**
{{SCENE_DESCRIPTION}}, {{LIGHTING}},
{{ACTION_DESCRIPTION}}, {{ERA_STYLE}}

**Beat Timing:**
- 0.0-0.5s: {{BEAT_1}}
- 0.5-1.0s: {{BEAT_2}}
- 1.0-1.5s: {{BEAT_3}}
- 1.5-2.0s: {{BEAT_4}}

**Motion:** {{MOTION_DESCRIPTION}}
**Camera:** {{CAMERA_MOVEMENT}}
**Duration:** {{DURATION}}s
**Creativity:** 0.4-0.6 (얼굴 보존 우선)
**Audio:** {{AUDIO_DESCRIPTION}}`,
  multiRefTemplate: `**Elements:**
1. ANCHOR.png (캐릭터 얼굴)
2. scene.png (구도)
3. (선택) 배경/의상 레퍼런스
4. (선택) 소품 레퍼런스

**Prompt:**
{{DETAILED_SCENE_DESCRIPTION}}

**Motion:**
- {{CHARACTER_1}}: {{MOTION_1}}
- {{CHARACTER_2}}: {{MOTION_2}}
- {{OBJECT}}: {{OBJECT_MOTION}}

**Camera:** {{CAMERA_MOVEMENT}}
**Duration:** {{DURATION}} seconds
**Audio:** {{AUDIO_DESCRIPTION}}`,
  parameterGuide: [
    { param: "Elements", description: "최대 4개 레퍼런스 이미지", example: "Element 1: 얼굴, Element 2: 구도", impact: "critical" },
    { param: "Motion Control", description: "레퍼런스 영상으로 동작 가이드", example: "Upload reference video", impact: "important" },
    { param: "Duration", description: "영상 길이", example: "3-5초 권장", impact: "important" },
    { param: "Camera", description: "카메라 움직임", example: "static, subtle dolly, pan", impact: "optional" },
    { param: "Creativity", description: "변형 허용도", example: "0.4-0.6 (얼굴 보존)", impact: "critical" },
  ],
  eraSpecificNegatives: {
    "1990s": "LED lighting, modern devices, cold color temperature",
    "2020s": "warm tungsten, candles, film grain",
  },
  commonIssues: [
    { problem: "캐릭터 얼굴 변함", solution: "Element 1에 얼굴 확실히 지정, Creativity 0.4-0.5" },
    { problem: "동작 부자연스러움", solution: "Motion Control 레퍼런스 영상 사용" },
    { problem: "조명 불일치", solution: "색온도(K) 명시 (3200K/6500K)" },
    { problem: "물리 왜곡", solution: "Omni One이 자동 보정, 심하면 재생성" },
    { problem: "오디오 안맞음", solution: "후편집 또는 재생성" },
  ],
};

// Veo 3.1 Template (VIDEO_VEO.md)
export const VEO_TEMPLATE: ToolSpecificTemplate = {
  id: "veo",
  name: "Veo 3.1",
  language: "english",
  singleRefTemplate: `[Reference Image URL]

**Scene Description:**
{{SCENE_DESCRIPTION}}
{{LIGHTING_DESCRIPTION}}, {{ERA_STYLE}}.

**Dialogue:**
[{{SPEAKER_1}} says, {{EMOTION_1}} and {{PACE_1}}: "{{LINE_1}}"]
[{{SPEAKER_2}} says, {{EMOTION_2}} and {{PACE_2}}: "{{LINE_2}}"]

**Visual Style:**
- Camera: {{CAMERA_TYPE}}, {{CAMERA_MOVEMENT}}
- Lighting: {{LIGHTING_DETAILS}}
- Color: {{COLOR_STYLE}}

**Audio Environment:**
- Room ambiance: {{AMBIANCE}}
- Background: {{BACKGROUND_AUDIO}}
- Music: {{MUSIC}}

**Duration:** {{DURATION}} seconds`,
  multiRefTemplate: `**Reference:** [ANCHOR.png for {{CHARACTER}} face]

**Scene:**
{{DETAILED_SCENE_SETUP}}

**Dialogue:**
[{{SPEAKER_1}} {{ACTION_1}}, {{EMOTION_1}}:]
"{{LINE_1}}"

[{{SPEAKER_2}} {{ACTION_2}}, {{EMOTION_2}}:]
"{{LINE_2}}"

**Emotion:** {{OVERALL_EMOTION}}
**Pacing:** {{PACING_STYLE}}
**Camera:** {{CAMERA_DETAILS}}
**Lighting:** {{LIGHTING_DETAILS}}
**Duration:** {{DURATION}} seconds`,
  parameterGuide: [
    { param: "Dialogue", description: "대사 (3-6초 제한)", example: '[BOY says, shy: "강아지 갖고 싶어요"]', impact: "critical" },
    { param: "Emotion", description: "감정 명시", example: "shy and excited, warm and gentle", impact: "critical" },
    { param: "Camera Angle", description: "정면/3/4만 가능 (측면 X)", example: "frontal view, three-quarter", impact: "critical" },
    { param: "Duration", description: "최대 60초", example: "15 seconds", impact: "important" },
    { param: "Audio", description: "대사 + 효과음 + 배경음악 동시", example: "Room ambiance + soft murmurs", impact: "important" },
  ],
  eraSpecificNegatives: {
    "1990s": "cold LED, modern devices, digital sharpness",
    "2020s": "warm tungsten, candles, genuine emotion, film grain",
  },
  commonIssues: [
    { problem: "립싱크 안맞음", solution: "대사 3-6초로 짧게" },
    { problem: "발음 부자연", solution: "감정 + 속도 명시 (slow, fast, whisper)" },
    { problem: "표정 안맞음", solution: "감정 키워드 추가 (shy, excited, warm)" },
    { problem: "다중 화자 혼란", solution: "턴테이킹 명확히 ([A says] → [B responds])" },
    { problem: "한국어 어색", solution: "자연스러운 구어체로 (생일 축하해! 소원 빌어)" },
  ],
};

// =============================================================================
// LIP-SYNC RULES (VEO 전용)
// =============================================================================

export const LIPSYNC_RULES = {
  maxDialogueDuration: "3-6초",
  allowedAngles: ["frontal view", "three-quarter angle"],
  forbiddenAngles: ["profile view (측면)", "back of head (뒷모습)"],
  plosiveConsonants: {
    korean: ["ㅂ", "ㅍ", "ㅁ"],
    description: "파열음에서 입술이 완전히 닫혀야 함",
  },
  emotionFormats: [
    "[SPEAKER says, EMOTION and PACE: \"LINE\"]",
    "[엄마 says, 다정하고 따뜻하게: \"...\"]",
    "[아이 says, 수줍게 속삭이며: \"...\"]",
  ],
  naturalKoreanExpressions: {
    good: ["생일 축하해!", "소원 빌어", "감사합니다~"],
    avoid: ["번역투 표현", "격식체 과용"],
  },
};

// =============================================================================
// BEAT TIMING PATTERNS (KLING 전용)
// =============================================================================

export const BEAT_TIMING = {
  avoidExpressions: ["immediately", "right away", "instantly", "suddenly"],
  recommendedFormat: [
    "0.0-0.5s: Boy inhales, chest rises, lips form 'O' shape.",
    "0.5-1.0s: Holds inhaled pose, eyes locked on candles.",
    "1.0-1.5s: Gentle exhale begins, candles flicker.",
    "1.5-2.0s: Candles extinguish, smoke wisps rise.",
  ],
  creativityGuide: {
    "0.3-0.4": "얼굴 보존 최우선, 최소 변형",
    "0.4-0.6": "안정적 모션, 권장값",
    "0.6-0.8": "자연스러운 동작, 약간의 변형 허용",
    "0.8+": "창의적 모션, 변형 많음",
  },
};

// =============================================================================
// ERA-SPECIFIC NEGATIVE PROMPTS (시대별 금지 요소)
// =============================================================================

export const ERA_NEGATIVES = {
  "1990s": {
    english: "western features, caucasian skin, blonde, blue eyes, smartphones, LED lights, modern furniture, sharp digital look, IKEA style, cold lighting",
    korean: "서양인 특징, 백인 피부, 금발, 파란 눈, 스마트폰, LED 조명, 현대 가구, 샤프한 디지털 느낌, 이케아 스타일, 차가운 조명",
  },
  "2020s": {
    english: "warm lighting, candles, tungsten, genuine happiness, film grain, retro furniture, nostalgic warmth, Kodak film look",
    korean: "따뜻한 조명, 촛불, 텅스텐, 진심 어린 행복, 필름 그레인, 레트로 가구, 노스탤직한 따뜻함, 코닥 필름 느낌",
  },
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Get step configuration by step number
 */
export function getTikitakaStep(step: number): TikitakaStepConfig | undefined {
  return TIKITAKA_STEPS[step];
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
  template?: ToolSpecificTemplate;
}

/**
 * Tool configurations with parameter guides
 */
export const TOOL_CONFIGS: Record<string, ToolConfig> = {
  nanobanana: {
    id: "nanobanana",
    name: "NanoBanana Pro",
    url: "https://nanobanana.ai",
    format: "korean",
    icon: "NB",
    template: NANOBANANA_TEMPLATE,
    parameterGuide: NANOBANANA_TEMPLATE.parameterGuide,
    commonIssues: NANOBANANA_TEMPLATE.commonIssues,
  },
  midjourney: {
    id: "midjourney",
    name: "MJ V7",
    url: "https://discord.com/channels/@me",
    format: "english_with_params",
    icon: "MJ",
    template: MIDJOURNEY_TEMPLATE,
    parameterGuide: MIDJOURNEY_TEMPLATE.parameterGuide,
    commonIssues: MIDJOURNEY_TEMPLATE.commonIssues,
  },
  kling: {
    id: "kling",
    name: "Kling 2.6",
    url: "https://klingai.com",
    format: "english",
    icon: "KL",
    template: KLING_TEMPLATE,
    parameterGuide: KLING_TEMPLATE.parameterGuide,
    commonIssues: KLING_TEMPLATE.commonIssues,
  },
  veo: {
    id: "veo",
    name: "Veo 3.1",
    url: "https://labs.google/fx/tools/veo",
    format: "english",
    icon: "VE",
    template: VEO_TEMPLATE,
    parameterGuide: VEO_TEMPLATE.parameterGuide,
    commonIssues: VEO_TEMPLATE.commonIssues,
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

/**
 * Get negative prompts for era
 */
export function getEraNegatives(era: "1990s" | "2020s", language: "korean" | "english"): string {
  return ERA_NEGATIVES[era][language];
}

/**
 * Get tool template by ID
 */
export function getToolTemplate(toolId: ToolId): ToolSpecificTemplate | undefined {
  return TOOL_CONFIGS[toolId]?.template;
}

/**
 * Generate formatted tool prompt from template
 */
export function generateToolPrompt(
  toolId: ToolId,
  variables: Record<string, string>,
  isMultiRef: boolean = false
): string {
  const template = getToolTemplate(toolId);
  if (!template) return "";

  let promptTemplate = isMultiRef ? template.multiRefTemplate : template.singleRefTemplate;

  // Replace variables
  for (const [key, value] of Object.entries(variables)) {
    const placeholder = `{{${key}}}`;
    promptTemplate = promptTemplate.replace(new RegExp(placeholder, "g"), value);
  }

  return promptTemplate;
}

// =============================================================================
// CRITIQUE DIMENSIONS (5차원 23항목)
// =============================================================================

export interface CritiqueDimension {
  id: string;
  name: string;
  nameKo: string;
  weight: number;
  items: CritiqueItem[];
}

export interface CritiqueItem {
  id: string;
  label: string;
  description: string;
  suggestion: string;  // 실패 시 규칙 기반 제안 문구
  weight: number;      // 항목별 가중치 (점수)
}

export const CRITIQUE_DIMENSIONS: CritiqueDimension[] = [
  {
    id: "prompt_adherence",
    name: "Prompt Adherence",
    nameKo: "프롬프트 준수",
    weight: 25,
    items: [
      { id: "subject", label: "주제 정확성", description: "주제(Subject)가 정확히 표현됨", suggestion: "주제를 더 구체적으로 명시 (예: 'Korean boy, 7 years old')", weight: 5 },
      { id: "background", label: "배경/환경", description: "배경과 환경이 의도대로 생성됨", suggestion: "배경 설명 추가 (예: '1990s Korean living room, wooden furniture')", weight: 4 },
      { id: "lighting", label: "조명/색감", description: "조명과 색감이 지시와 일치", suggestion: "K값 명시 (예: '3200K tungsten lighting' 또는 '6500K LED')", weight: 5 },
      { id: "style", label: "스타일", description: "요청한 스타일과 일치", suggestion: "시대별 스타일 명시 (예: 'Kodak Portra 400 film look' 또는 '--style raw')", weight: 4 },
      { id: "no_missing", label: "누락 없음", description: "누락된 요소가 없음", suggestion: "원본 키프레임 다시 확인하고 누락된 요소 추가", weight: 4 },
      { id: "no_extra", label: "추가 없음", description: "불필요한 추가 요소가 없음", suggestion: "--no 파라미터로 불필요한 요소 제거 (예: '--no modern furniture, smartphones')", weight: 3 },
    ],
  },
  {
    id: "aesthetic",
    name: "Aesthetic Quality",
    nameKo: "미적 품질",
    weight: 20,
    items: [
      { id: "composition", label: "구도", description: "구도가 균형잡히고 시선 유도가 적절함", suggestion: "--iw 2.0~2.5로 레퍼런스 영향력 높이기", weight: 5 },
      { id: "color_harmony", label: "색감 조화", description: "팔레트가 일관성 있음", suggestion: "color palette HEX 코드 명시 (예: '#F5DEB3 warm beige tones')", weight: 5 },
      { id: "lighting_natural", label: "조명", description: "조명이 자연스럽고 분위기에 맞음", suggestion: "조명 방향/소스 명시 (예: 'soft key light from left, candle fill')", weight: 5 },
      { id: "impact", label: "시각적 임팩트", description: "전체적으로 시각적으로 매력적임", suggestion: "--stylize 100-250 조정으로 예술적 해석 조절", weight: 5 },
    ],
  },
  {
    id: "technical",
    name: "Technical Quality",
    nameKo: "기술적 완성도",
    weight: 15,
    items: [
      { id: "resolution", label: "해상도/선명도", description: "충분한 디테일이 있음", suggestion: "해상도 명시 (예: '4K resolution, sharp details')", weight: 4 },
      { id: "texture", label: "텍스처", description: "텍스처가 자연스러움", suggestion: "텍스처 스타일 명시 (예: 'subtle film grain, natural skin texture')", weight: 4 },
      { id: "noise", label: "노이즈/그레인", description: "의도적이거나 없음", suggestion: "1990s면 'film grain' 추가, 2020s면 '--no film grain'", weight: 3 },
      { id: "artifacts", label: "아티팩트", description: "글리치나 왜곡이 없음", suggestion: "--no artifacts, glitches, distortion 추가", weight: 4 },
    ],
  },
  {
    id: "consistency",
    name: "Character Consistency",
    nameKo: "캐릭터 일관성",
    weight: 25, // 가장 중요
    items: [
      { id: "face", label: "얼굴", description: "ANCHOR와 얼굴이 일치함", suggestion: "--oref [ANCHOR URL] --cw 80-100 으로 얼굴 고정", weight: 8 },
      { id: "hair", label: "헤어스타일", description: "헤어스타일이 일치함", suggestion: "헤어스타일 구체적 명시 (예: 'bowl cut, black straight hair')", weight: 4 },
      { id: "ethnicity", label: "민족/피부톤", description: "한국인으로 정확히 표현됨", suggestion: "Korean::2 + --no western features, caucasian skin, blonde, blue eyes", weight: 8 },
      { id: "clothing", label: "의상", description: "색상과 스타일이 일치함", suggestion: "의상 색상 정확히 명시 (예: 'red striped t-shirt, same as Image 1')", weight: 3 },
      { id: "age", label: "나이", description: "나이가 적절하게 표현됨", suggestion: "나이 구체적 명시 (예: '7 years old Korean boy')", weight: 2 },
    ],
  },
  {
    id: "anatomy",
    name: "Anatomy/Physics",
    nameKo: "해부학/물리",
    weight: 15,
    items: [
      { id: "hands", label: "손", description: "자연스러운 포즈, 손가락 수 정확", suggestion: "--no 6 fingers, extra fingers, deformed hands 또는 'hands hidden behind back'", weight: 5 },
      { id: "face_features", label: "얼굴 특징", description: "눈/코/입 배치가 정상", suggestion: "--no distorted face, asymmetric features, crossed eyes", weight: 4 },
      { id: "body_proportion", label: "신체 비율", description: "신체 비율이 자연스러움", suggestion: "--no elongated limbs, disproportionate body", weight: 3 },
      { id: "physics", label: "물리적 논리", description: "중력, 그림자 등이 적절함", suggestion: "그림자 방향 명시 (예: 'shadows consistent with candle light source')", weight: 3 },
    ],
  },
];

/**
 * Calculate total score from dimension scores (legacy)
 */
export function calculateTotalScore(dimensionScores: Record<string, number>): number {
  let totalScore = 0;
  let totalWeight = 0;

  for (const dimension of CRITIQUE_DIMENSIONS) {
    const score = dimensionScores[dimension.id] ?? 0;
    totalScore += score * dimension.weight;
    totalWeight += dimension.weight;
  }

  return Math.round(totalScore / totalWeight);
}

/**
 * Checked item result with pass/fail
 */
export interface CritiqueItemResult {
  dimensionId: string;
  dimensionName: string;
  itemId: string;
  label: string;
  passed: boolean;
  weight: number;
  suggestion: string;
}

/**
 * Calculate total score from individual item checks (5D×23)
 */
export function calculateItemScore(
  checkedItems: Record<string, Record<string, boolean>> // {dimension_id: {item_id: passed}}
): { score: number; passedItems: CritiqueItemResult[]; failedItems: CritiqueItemResult[] } {
  let earnedPoints = 0;
  let totalPoints = 0;
  const passedItems: CritiqueItemResult[] = [];
  const failedItems: CritiqueItemResult[] = [];

  for (const dimension of CRITIQUE_DIMENSIONS) {
    const dimChecks = checkedItems[dimension.id] || {};

    for (const item of dimension.items) {
      totalPoints += item.weight;
      const passed = dimChecks[item.id] === true;

      const result: CritiqueItemResult = {
        dimensionId: dimension.id,
        dimensionName: dimension.nameKo,
        itemId: item.id,
        label: item.label,
        passed,
        weight: item.weight,
        suggestion: item.suggestion,
      };

      if (passed) {
        earnedPoints += item.weight;
        passedItems.push(result);
      } else {
        failedItems.push(result);
      }
    }
  }

  // Normalize to 0-100 scale
  const score = totalPoints > 0 ? Math.round((earnedPoints / totalPoints) * 100) : 0;
  return { score, passedItems, failedItems };
}

/**
 * Generate Markdown critique output for copy-paste
 */
export function generateCritiqueMarkdown(
  sceneName: string,
  score: number,
  verdict: "PASS" | "REVISE" | "REJECT",
  passedItems: CritiqueItemResult[],
  failedItems: CritiqueItemResult[],
  improvedPrompt?: string
): string {
  const verdictEmoji = verdict === "PASS" ? "✅" : verdict === "REVISE" ? "🔄" : "❌";

  let md = `## 🎯 Critique 결과 (${sceneName})

### 점수: ${score}/100 → ${verdictEmoji} ${verdict}

`;

  if (passedItems.length > 0) {
    md += `### ✅ 통과 항목
`;
    for (const item of passedItems) {
      md += `- [${item.dimensionName}] ${item.label} (+${item.weight})
`;
    }
    md += `
`;
  }

  if (failedItems.length > 0) {
    md += `### ❌ 실패 항목
`;
    for (const item of failedItems) {
      md += `- [${item.dimensionName}] ${item.label} (-${item.weight})
  → 제안: ${item.suggestion}
`;
    }
    md += `
`;
  }

  if (improvedPrompt) {
    md += `### 💡 개선된 프롬프트
\`\`\`
${improvedPrompt}
\`\`\`
`;
  }

  return md;
}

/**
 * Generate improved prompt by appending suggestions from failed items
 */
export function generateImprovedPrompt(
  originalPrompt: string,
  failedItems: CritiqueItemResult[]
): string {
  const suggestions: string[] = [];
  const noParams: string[] = [];

  for (const item of failedItems) {
    // Extract --no parameters from suggestions
    const noMatch = item.suggestion.match(/--no\s+([^,]+(?:,\s*[^,]+)*)/);
    if (noMatch) {
      noParams.push(noMatch[1].trim());
    }

    // Collect other suggestions
    if (!item.suggestion.startsWith("--no")) {
      suggestions.push(`// ${item.dimensionName}: ${item.suggestion}`);
    }
  }

  let improved = originalPrompt;

  // Append --no parameters if any
  if (noParams.length > 0) {
    const existingNo = originalPrompt.match(/--no\s+([^\n]+)/);
    if (existingNo) {
      // Append to existing --no
      improved = improved.replace(
        /--no\s+([^\n]+)/,
        `--no ${existingNo[1]}, ${noParams.join(", ")}`
      );
    } else {
      // Add new --no line
      improved += `\n\n--no ${noParams.join(", ")}`;
    }
  }

  // Add suggestions as comments at the end
  if (suggestions.length > 0) {
    improved += `\n\n/* 개선 제안:\n${suggestions.join("\n")}\n*/`;
  }

  return improved;
}
