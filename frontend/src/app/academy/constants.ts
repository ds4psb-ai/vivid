// Tool Links
export const TOOL_LINKS = {
  builder: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221aReu3uy_0Ayxo6KhjC1OS-EJUmOmSLVA%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  vibe: "https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221wKUuefdolzOVFp7YAxSfcO13prtAWvgu%22%5D,%22action%22:%22open%22,%22userId%22:%22109914641793744493802%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing",
  antigravity: "https://antigravity.google",
};

export const FREE_TRIAL_URL = "https://console.cloud.google.com/freetrial/signup/tos?facet_url=https:%2F%2Fcloud.google.com%2Ffree&facet_utm_source=google&facet_utm_campaign=17100102-GCP-DR-APAC-KR-ko-Google-BKWS-MIX-GenericCloud&facet_utm_medium=cpc";

export type TabKey = "home" | "setup" | "credit" | "upload" | "prompt" | "parse" | "tools" | "vibe" | "homework" | "admin";

export interface NavItem {
  key: TabKey;
  label: string;
  icon: string;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: "Dashboard",
    items: [
      { key: "home", label: "홈 대시보드", icon: "dashboard" },
      { key: "setup", label: "환경 설정", icon: "settings" },
      { key: "credit", label: "$300 무료 크레딧", icon: "redeem" },
    ],
  },
  {
    title: "Workflow",
    items: [
      { key: "upload", label: "영상 업로드", icon: "cloud_upload" },
      { key: "prompt", label: "프롬프터", icon: "auto_awesome" },
      { key: "parse", label: "파싱 + 복사", icon: "content_copy" },
      { key: "tools", label: "외부 툴", icon: "build" },
    ],
  },
  {
    title: "기타",
    items: [
      { key: "vibe", label: "철학관", icon: "psychology" },
      { key: "homework", label: "과제", icon: "assignment_turned_in" },
    ],
  },
];

// Admin 전용 섹션 (is_admin일 때만 표시)
export const ADMIN_SECTION: NavSection = {
  title: "ADMIN",
  items: [
    { key: "admin", label: "수강생 관리", icon: "admin_panel_settings" },
  ],
};
