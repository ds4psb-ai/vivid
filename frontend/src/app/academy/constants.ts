// Tool Links
export const TOOL_LINKS = {
  builder: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221aReu3uy_0Ayxo6KhjC1OS-EJUmOmSLVA%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  vibe: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221wKUuefdolzOVFp7YAxSfcO13prtAWvgu%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  antigravity: "https://antigravity.google",
};

export const FREE_TRIAL_URL = "https://console.cloud.google.com/freetrial/signup/tos?facet_url=https:%2F%2Fcloud.google.com%2Ffree&facet_utm_source=google&facet_utm_campaign=17100102-GCP-DR-APAC-KR-ko-Google-BKWS-MIX-GenericCloud&facet_utm_medium=cpc";

export type TabKey = "home" | "setup" | "credit" | "upload" | "prompt" | "parse" | "tools" | "vibe" | "homework";

export const NAV_SECTIONS = [
  {
    title: "Dashboard",
    items: [
      { key: "home" as TabKey, label: "홈 대시보드", icon: "dashboard" },
      { key: "setup" as TabKey, label: "환경 설정", icon: "settings" },
      { key: "credit" as TabKey, label: "$300 무료 크레딧", icon: "redeem" },
    ],
  },
  {
    title: "Workflow",
    items: [
      { key: "upload" as TabKey, label: "영상 업로드", icon: "cloud_upload" },
      { key: "prompt" as TabKey, label: "프롬프트 생성", icon: "auto_awesome" },
      { key: "parse" as TabKey, label: "파싱 + 복사", icon: "content_copy" },
      { key: "tools" as TabKey, label: "외부 툴", icon: "build" },
    ],
  },
  {
    title: "기타",
    items: [
      { key: "vibe" as TabKey, label: "바이브 철학관", icon: "psychology" },
      { key: "homework" as TabKey, label: "과제", icon: "assignment_turned_in" },
    ],
  },
];
