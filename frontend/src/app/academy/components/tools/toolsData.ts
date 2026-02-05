export const IMAGE_TOOLS = [
  {
    id: "nanobanana",
    title: "NanoBanana Pro",
    color: "orange",
    url: "https://gemini.google.com",
    badge: "한글 OK",
  },
  {
    id: "midjourney",
    title: "Midjourney V7",
    color: "violet",
    url: "https://www.midjourney.com",
    badge: "--cref",
  },
];

export const VIDEO_TOOLS = [
  {
    id: "kling",
    title: "Kling 3.0",
    color: "cyan",
    url: "https://klingai.com",
    badge: "4K",
  },
  {
    id: "veo",
    title: "Veo 3.1",
    color: "red",
    url: "https://labs.google/fx/tools/flow",
    badge: "오디오 포함",
  },
];

export const FAQ_ITEMS = [
  {
    id: "anchor",
    question: "앵커 이미지란?",
    answer: "첫 번째 씬(보통 Scene 1)에서 생성한 캐릭터 기준 이미지입니다. 이 이미지를 --oref로 참조하면 나머지 씬에서도 같은 캐릭터를 유지할 수 있습니다.",
  },
  {
    id: "cref",
    question: "--oref URL은 어디서 복사하나요?",
    answer: "Midjourney 웹사이트: 생성된 이미지 우클릭 → '이미지 주소 복사'\nDiscord: 이미지 클릭 → '브라우저에서 열기' → 주소창 URL 복사\n\n복사한 URL을 프롬프트의 [ANCHOR_URL] 부분에 직접 붙여넣으세요.",
  },
  {
    id: "klingvsveo",
    question: "Kling vs Veo, 언제 뭘 쓰나요?",
    answer: "• Kling: 캐릭터 일관성 중요할 때, 4K 고화질 필요할 때, 카메라 움직임 세밀 제어\n• Veo: 대사나 효과음이 필요한 씬, 빠른 프로토타입, Google 크레딧 있을 때\n\n💡 보통 Kling으로 영상 만들고, CapCut에서 오디오 추가하는 게 품질이 좋습니다.",
  },
  {
    id: "audio",
    question: "오디오는 어떻게 적용하나요?",
    answer: "1. Veo: 자동으로 대사/효과음 생성됨\n2. Kling: 무음 → CapCut/Premiere에서 오디오 추가\n\n오디오 소스: ElevenLabs(TTS), Suno(음악), 또는 직접 녹음",
  },
  {
    id: "merge",
    question: "영상은 어떻게 합치나요?",
    answer: "1. CapCut (무료, 추천): 모바일/PC 모두 지원, 자동 자막\n2. Premiere Pro: 전문가용\n3. DaVinci Resolve: 무료, 컬러그레이딩 강력\n\n씬별로 생성한 클립들을 타임라인에 순서대로 배치하면 됩니다.",
  },
];

export const MIDJOURNEY_PARAMS = [
  { param: "--ar 9:16", desc: "세로 비율 (숏폼)" },
  { param: "--ar 16:9", desc: "가로 비율" },
  { param: "--v 7", desc: "버전 7" },
  { param: "--style raw", desc: "실사 느낌" },
  { param: "--stylize 250", desc: "스타일 강도 (0~1000)" },
  { param: "--cref [URL]", desc: "캐릭터 참조 URL" },
  { param: "--cw 30~100", desc: "참조 강도 (얼굴30, 전체100)" },
  { param: "--no [키워드]", desc: "제외 요소" },
];

export const KLING_CAMERA_OPTIONS = [
  { option: "Static", desc: "고정 (클로즈업에 적합)" },
  { option: "Dolly In/Out", desc: "줌인/줌아웃" },
  { option: "Pan Left/Right", desc: "좌우 패닝" },
  { option: "Tilt Up/Down", desc: "상하 틸트" },
];

export const KLING_MOTION_SCORES = [
  { score: "1-2", usage: "정적 (배경, 클로즈업)" },
  { score: "3-4", usage: "약간 움직임 (대화, 표정)" },
  { score: "5", usage: "활발한 움직임 (걷기, 액션)" },
];
