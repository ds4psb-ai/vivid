/**
 * Critique Prompt Generator
 *
 * Generates copy-paste prompts for AI critique workflow.
 * No API calls - designed for manual copy-paste to external AI tools.
 */

export interface CritiqueContext {
  sceneId: string;
  sceneName: string;
  isAnchor: boolean;
  imagePath?: string;
  anchorImagePath?: string;
  originalKeyframePath?: string;
  critiqueType: "image" | "video";
}

export interface CritiqueDimension {
  id: string;
  name: string;
  nameKo: string;
  description: string;
  weight: number;
}

/**
 * 5D Critique Dimensions for Image
 */
export const IMAGE_CRITIQUE_DIMENSIONS: CritiqueDimension[] = [
  {
    id: "identity_accuracy",
    name: "Identity Accuracy",
    nameKo: "인물 정확도",
    description: "모든 인물이 한국인으로 생성되었는가? 피부톤, 눈 모양, 헤어스타일이 원본과 일치하는가?",
    weight: 25,
  },
  {
    id: "composition_match",
    name: "Composition Match",
    nameKo: "구도 일치",
    description: "원본 키프레임의 구도, 인물 배치, 앵글이 정확히 재현되었는가?",
    weight: 20,
  },
  {
    id: "color_consistency",
    name: "Color Consistency",
    nameKo: "색감 일관성",
    description: "조명 색온도, 의상 색깔, 배경 색감이 원본 및 ANCHOR와 일관적인가?",
    weight: 20,
  },
  {
    id: "era_authenticity",
    name: "Era Authenticity",
    nameKo: "시대 재현",
    description: "1990s/2020s 등 설정된 시대의 분위기가 정확히 표현되었는가?",
    weight: 15,
  },
  {
    id: "anchor_similarity",
    name: "ANCHOR Similarity",
    nameKo: "ANCHOR 유사도",
    description: "ANCHOR 이미지의 캐릭터와 스타일이 일관되게 유지되는가?",
    weight: 20,
  },
];

/**
 * 5D Critique Dimensions for Video
 */
export const VIDEO_CRITIQUE_DIMENSIONS: CritiqueDimension[] = [
  {
    id: "motion_naturalness",
    name: "Motion Naturalness",
    nameKo: "모션 자연스러움",
    description: "움직임이 자연스럽고 어색하지 않은가? 관절 왜곡이 없는가?",
    weight: 25,
  },
  {
    id: "face_consistency",
    name: "Face Consistency",
    nameKo: "얼굴 일관성",
    description: "영상 전체에서 인물 얼굴이 일관되게 유지되는가? 깜빡임이나 변형이 없는가?",
    weight: 25,
  },
  {
    id: "artifact_free",
    name: "Artifact-Free",
    nameKo: "아티팩트 없음",
    description: "워핑, 깜빡임, 글리치 등의 AI 아티팩트가 없는가?",
    weight: 20,
  },
  {
    id: "timing_accuracy",
    name: "Timing Accuracy",
    nameKo: "타이밍 정확도",
    description: "원본 영상의 타이밍과 리듬이 잘 재현되었는가?",
    weight: 15,
  },
  {
    id: "source_fidelity",
    name: "Source Fidelity",
    nameKo: "원본 충실도",
    description: "소스 이미지의 디테일이 영상에서 잘 보존되었는가?",
    weight: 15,
  },
];

/**
 * Generate critique prompt for copy-paste
 */
export function generateCritiquePrompt(context: CritiqueContext): string {
  const dimensions =
    context.critiqueType === "image"
      ? IMAGE_CRITIQUE_DIMENSIONS
      : VIDEO_CRITIQUE_DIMENSIONS;

  const typeLabel = context.critiqueType === "image" ? "이미지" : "영상";
  const typeEmoji = context.critiqueType === "image" ? "🖼️" : "🎬";

  let prompt = `${typeEmoji} ${context.sceneName} ${typeLabel} Critique 요청

`;

  if (context.imagePath) {
    prompt += `**평가 대상**: ${context.imagePath}
`;
  }

  if (context.anchorImagePath && !context.isAnchor) {
    prompt += `**ANCHOR 참조**: ${context.anchorImagePath}
`;
  }

  if (context.originalKeyframePath) {
    prompt += `**원본 키프레임**: ${context.originalKeyframePath}
`;
  }

  prompt += `
## 평가 요청

아래 5가지 기준으로 이 ${typeLabel}를 평가해주세요.
각 항목별 0-100점 점수와 구체적인 피드백을 제공해주세요.

`;

  dimensions.forEach((dim, i) => {
    prompt += `### ${i + 1}. ${dim.nameKo} (${dim.name}) - 가중치 ${dim.weight}%
${dim.description}

**점수**: /100
**피드백**:

`;
  });

  prompt += `---

## 최종 판정

총점: /100 (가중 평균)

**Verdict**:
- ✅ **PASS** (85점 이상): 다음 단계 진행
- 🔄 **REVISE** (60-84점): 아래 수정사항 반영 후 재생성
- ❌ **REJECT** (60점 미만): 프롬프트 재검토 필요

**주요 문제점**:
1.
2.

**개선 제안**:
1.
2.

---

## JSON 출력 (파싱용)

\`\`\`json
{
  "scene_id": "${context.sceneId}",
  "critique_type": "${context.critiqueType}",
  "scores": {
${dimensions.map((d) => `    "${d.id}": 0`).join(",\n")}
  },
  "total_score": 0,
  "verdict": "PASS|REVISE|REJECT",
  "issues": [],
  "suggestions": []
}
\`\`\`
`;

  return prompt;
}

/**
 * Generate batch critique prompt for multiple scenes
 */
export function generateBatchCritiquePrompt(
  contexts: CritiqueContext[],
  anchorImagePath?: string
): string {
  const firstContext = contexts[0];
  const critiqueType = firstContext?.critiqueType || "image";
  const typeLabel = critiqueType === "image" ? "이미지" : "영상";

  let prompt = `📋 Batch ${typeLabel} Critique 요청

`;

  if (anchorImagePath) {
    prompt += `**ANCHOR 참조**: ${anchorImagePath}

`;
  }

  prompt += `## 평가 대상 (${contexts.length}개)

`;

  contexts.forEach((ctx, i) => {
    prompt += `${i + 1}. **${ctx.sceneName}**${ctx.isAnchor ? " (ANCHOR)" : ""}
   - 경로: ${ctx.imagePath || "(없음)"}

`;
  });

  prompt += `---

## 평가 기준

`;

  const dimensions =
    critiqueType === "image"
      ? IMAGE_CRITIQUE_DIMENSIONS
      : VIDEO_CRITIQUE_DIMENSIONS;

  dimensions.forEach((dim, i) => {
    prompt += `${i + 1}. **${dim.nameKo}** (${dim.weight}%): ${dim.description}
`;
  });

  prompt += `
---

## 요청

각 ${typeLabel}에 대해:
1. 5가지 기준별 점수 (0-100)
2. 총점 (가중 평균)
3. Verdict (PASS/REVISE/REJECT)
4. 주요 문제점과 개선 제안

JSON 배열로 출력해주세요.

\`\`\`json
[
  {
    "scene_id": "scene1",
    "scores": {...},
    "total_score": 0,
    "verdict": "PASS",
    "issues": [],
    "suggestions": []
  }
]
\`\`\`
`;

  return prompt;
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand("copy");
      return true;
    } catch {
      return false;
    } finally {
      document.body.removeChild(textarea);
    }
  }
}
