import { type Language } from "@/lib/translations";

export type ConfidenceLevel = "high" | "medium" | "low";

const REASON_CODE_LABELS: Record<Language, Record<string, string>> = {
  ko: {
    // Genre
    "genre:romance": "로맨스 장르",
    "genre:horror": "호러 장르",
    "genre:action": "액션 장르",
    "genre:drama": "드라마 장르",
    "genre:comedy": "코미디 장르",
    "genre:thriller": "스릴러 장르",
    "genre:fantasy": "판타지 장르",
    "genre:sci-fi": "SF 장르",
    "genre:documentary": "다큐 장르",
    "genre:animation": "애니메이션 장르",

    // Auteur
    "auteur:bong": "봉준호 스타일",
    "auteur:nolan": "놀란 스타일",
    "auteur:kubrick": "큐브릭 스타일",
    "auteur:tarantino": "타란티노 스타일",
    "auteur:ghibli": "지브리 스타일",
    "auteur:villeneuve": "빌뇌브 스타일",
    "auteur:fincher": "핀처 스타일",
    "auteur:wes_anderson": "웨스 앤더슨 스타일",
    "auteur:spielberg": "스필버그 스타일",
    "auteur:scorsese": "스콜세지 스타일",

    // Dimension
    "dimension:1D": "1D 프롬프트",
    "dimension:2D": "2D 스토리보드",
    "dimension:3D": "3D 비주얼",
    "dimension:4D": "4D 레퍼런스",
    "dimension:AD": "미학디렉터",
    "dimension:QC": "퀄리티 체크",
    "dimension:VEO": "비디오 생성",
    "dimension:STORY": "스토리 아키텍트",
    "dimension:SOUND": "사운드 크래프터",
    "dimension:AI": "AI 페르소나",

    // Shot / Scene
    "shot:closeup": "클로즈업 샷",
    "shot:wide": "와이드 샷",
    "shot:establishing": "설정 샷",
    "shot:pov": "시점 샷",
    "shot:tracking": "트래킹 샷",
    "shot:aerial": "항공 샷",
    "shot:handheld": "핸드헬드",
    "shot:static": "고정 샷",
    "shot:dolly": "돌리 샷",
    "shot:crane": "크레인 샷",
    "shot:action": "액션 씬",
    "shot:dialogue": "대화 씬",
    "shot:montage": "몽타주",

    // Context
    "context:worldbuilding": "세계관 맥락",
    "context:character": "캐릭터 중심",
    "context:setting": "배경 중심",
    "context:theme": "테마 매칭",
    "context:mood": "분위기 매칭",
    "context:narrative": "서사 맥락",
    "context:visual_style": "비주얼 스타일",
    "context:color_palette": "컬러 팔레트",
    "context:pacing": "리듬/페이싱",
    "context:workflow_preset": "워크플로우 매칭",

    // History
    "history:frequently_used": "자주 사용됨",
    "history:recently_used": "최근 사용됨",
    "history:workflow_pattern": "워크플로우 패턴",
    "history:similar_project": "유사 프로젝트",
  },
  en: {
    // Genre
    "genre:romance": "Romance Genre",
    "genre:horror": "Horror Genre",
    "genre:action": "Action Genre",
    "genre:drama": "Drama Genre",
    "genre:comedy": "Comedy Genre",
    "genre:thriller": "Thriller Genre",
    "genre:fantasy": "Fantasy Genre",
    "genre:sci-fi": "Sci-Fi Genre",
    "genre:documentary": "Documentary",
    "genre:animation": "Animation Genre",

    // Auteur
    "auteur:bong": "Bong Joon-ho Style",
    "auteur:nolan": "Christopher Nolan Style",
    "auteur:kubrick": "Stanley Kubrick Style",
    "auteur:tarantino": "Quentin Tarantino Style",
    "auteur:ghibli": "Studio Ghibli Style",
    "auteur:villeneuve": "Denis Villeneuve Style",
    "auteur:fincher": "David Fincher Style",
    "auteur:wes_anderson": "Wes Anderson Style",
    "auteur:spielberg": "Steven Spielberg Style",
    "auteur:scorsese": "Martin Scorsese Style",

    // Dimension
    "dimension:1D": "1D Prompt",
    "dimension:2D": "2D Storyboard",
    "dimension:3D": "3D Visual",
    "dimension:4D": "4D Reference",
    "dimension:AD": "Aesthetic Director",
    "dimension:QC": "Quality Check",
    "dimension:VEO": "Video Generation",
    "dimension:STORY": "Story Architect",
    "dimension:SOUND": "Sound Crafter",
    "dimension:AI": "AI Persona",

    // Shot / Scene
    "shot:closeup": "Close-up Shot",
    "shot:wide": "Wide Shot",
    "shot:establishing": "Establishing Shot",
    "shot:pov": "POV Shot",
    "shot:tracking": "Tracking Shot",
    "shot:aerial": "Aerial Shot",
    "shot:handheld": "Handheld Shot",
    "shot:static": "Static Shot",
    "shot:dolly": "Dolly Shot",
    "shot:crane": "Crane Shot",
    "shot:action": "Action Scene",
    "shot:dialogue": "Dialogue Scene",
    "shot:montage": "Montage",

    // Context
    "context:worldbuilding": "Worldbuilding Context",
    "context:character": "Character Focus",
    "context:setting": "Setting Focus",
    "context:theme": "Theme Match",
    "context:mood": "Mood Match",
    "context:narrative": "Narrative Context",
    "context:visual_style": "Visual Style",
    "context:color_palette": "Color Palette",
    "context:pacing": "Pacing",
    "context:workflow_preset": "Workflow Match",

    // History
    "history:frequently_used": "Frequently Used",
    "history:recently_used": "Recently Used",
    "history:workflow_pattern": "Workflow Pattern",
    "history:similar_project": "Similar Project",
  },
};

export function getReasonCodeLabel(code: string, language: Language): string {
  return REASON_CODE_LABELS[language]?.[code] || code;
}

export function scoreToConfidenceLevel(score?: number): ConfidenceLevel {
  const value = score ?? 0;
  if (value >= 0.75) return "high";
  if (value >= 0.5) return "medium";
  return "low";
}

export function getConfidenceLabel(level: ConfidenceLevel, language: Language): string {
  if (language === "ko") {
    return level === "high" ? "높음" : level === "medium" ? "보통" : "낮음";
  }
  return level.toUpperCase();
}
