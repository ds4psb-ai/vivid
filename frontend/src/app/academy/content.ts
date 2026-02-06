export const HOMEWORK_DATA = {
  "1강": {
    date: "2026년 1월 30일 (목)",
    tasks: [
      {
        title: "1. Crebit AI Studio 회원가입",
        items: ["prompty.co.kr 접속", "Google 계정 로그인"],
      },
      {
        title: "2. 디스코드 가입",
        items: ["초대 링크로 서버 입장", "닉네임 설정 (실명 권장)"],
      },
    ],
    submission: {
      channel: "디스코드 #과제제출 채널에 '완료' 댓글",
      items: [] as string[],
    },
  },
  "2강": {
    date: "2026년 2월 6일 (목)",
    tasks: [
      {
        title: "1. 이미지 프롬프트 생성기 완료",
        items: ["바이럴 영상 분석", "결과물(.md) 저장"],
      },
      {
        title: "2. 철학관 세션",
        items: ["최소 50% 깊이 도달", "프로필(.json) 다운로드"],
      },
      {
        title: "3. Google 계정 준비",
        items: ["최소 3개 계정 생성", "하나의 전화번호로 최대 5개 생성 가능"],
        highlight: "3개",
      },
    ],
    submission: {
      channel: "디스코드 #과제제출 채널에 업로드",
      items: ["이미지 프롬프트 생성기 결과물 (.md)"],
      note: "철학관 프로필은 개인정보이므로 제출하지 않습니다.",
    },
  },
  "3강": {
    date: "2026년 2월 13일 (목)",
    tasks: [
      {
        title: "1. 비디오 프롬프트 생성 완료",
        items: ["이미지 프롬프트 기반 비디오 프롬프트 생성", "결과물(.md) 저장"],
      },
      {
        title: "2. Veo3 영상 생성 (1개 이상)",
        items: ["생성된 프롬프트로 Veo3 실행", "결과 영상 저장"],
      },
    ],
    submission: {
      channel: "디스코드 #과제제출 채널에 업로드",
      items: ["비디오 프롬프트 결과물 (.md)", "Veo3 생성 영상 (1개 이상)"],
    },
  },
} as const;

export type LectureKey = keyof typeof HOMEWORK_DATA;

export const VIDEO_DOWNLOAD_SOURCES = [
  {
    platform: "YouTube",
    icon: "play_circle",
    colorClass:
      "from-red-500/10 to-red-600/5 border-red-500/20 text-red-400",
    links: [
      { label: "savefrom.net", href: "https://savefrom.net" },
      {
        label: "publer.com",
        href: "https://publer.com/tools/youtube-short-downloader",
      },
    ],
  },
  {
    platform: "TikTok",
    icon: "music_note",
    colorClass:
      "from-pink-500/10 to-pink-600/5 border-pink-500/20 text-pink-400",
    links: [
      { label: "snaptik.app", href: "https://snaptik.app" },
      { label: "ssstik.io", href: "https://ssstik.io" },
    ],
  },
  {
    platform: "Instagram",
    icon: "photo_camera",
    colorClass:
      "from-purple-500/10 to-fuchsia-600/5 border-purple-500/20 text-purple-400",
    links: [
      { label: "snapinsta.to", href: "https://snapinsta.to" },
      {
        label: "sssinstagram.com",
        href: "https://sssinstagram.com/reels-downloader",
      },
    ],
  },
] as const;
