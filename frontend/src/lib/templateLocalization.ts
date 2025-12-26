import type { Template } from "@/lib/api";

type TemplateOverride = {
  title: string;
  description: string;
  tags: string[];
};

const KO_OVERRIDES: Record<string, TemplateOverride> = {
  "tmpl-auteur-bong": {
    title: "구조적 긴장",
    description: "정교한 동선과 장르 전환의 긴장감을 설계합니다.",
    tags: ["스릴러", "풍자", "다이내믹"],
  },
  "tmpl-auteur-park": {
    title: "대칭 누아르",
    description: "강박적 대칭과 강한 대비로 복수 서사를 강화합니다.",
    tags: ["누아르", "강렬", "스타일리시"],
  },
  "tmpl-auteur-shinkai": {
    title: "빛의 하늘",
    description: "현실적인 빛과 구름, 감정의 여운을 살립니다.",
    tags: ["애니메이션", "로맨스", "풍경"],
  },
  "tmpl-auteur-leejunho": {
    title: "무대 리듬",
    description: "음악 싱크 컷과 퍼포먼스 에너지로 리듬을 잡습니다.",
    tags: ["음악", "퍼포먼스", "리듬"],
  },
  "tmpl-auteur-na": {
    title: "거친 추격",
    description: "거친 핸드헬드와 긴박한 추격 서사를 강화합니다.",
    tags: ["액션", "추격", "리얼"],
  },
  "tmpl-auteur-hong": {
    title: "정적 대화",
    description: "롱테이크, 어색한 침묵, 돌연한 줌으로 리듬을 만듭니다.",
    tags: ["드라마", "미니멀", "대화"],
  },
  "tmpl-production-stage": {
    title: "프로덕션: 무대 리허설",
    description: "샷 리스트 → 프롬프트 → 생성 워크플로를 점검합니다.",
    tags: ["프로덕션", "샷", "스튜디오"],
  },
};

const hasHangul = (value?: string | null) => Boolean(value && /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/.test(value));

const shouldOverride = (value?: string | null) => !value || !hasHangul(value);

export const localizeTemplate = (template: Template, language: string): Template => {
  if (language !== "ko") return template;
  const override = KO_OVERRIDES[template.slug];
  if (!override) return template;
  return {
    ...template,
    title: shouldOverride(template.title) ? override.title : template.title,
    description: shouldOverride(template.description) ? override.description : template.description,
    tags:
      !template.tags?.length || template.tags.every((tag) => !hasHangul(tag))
        ? override.tags
        : template.tags,
  };
};
