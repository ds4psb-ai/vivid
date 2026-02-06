import type { TabKey } from "@/app/academy/constants";

export function extractAcademyTabFromHref(href: string): TabKey {
  try {
    const url = new URL(href, "http://local");
    const tab = url.searchParams.get("tab");
    return (tab as TabKey) || "home";
  } catch {
    return "home";
  }
}

export function isAcademyTabActive(currentTab: TabKey, href: string): boolean {
  return currentTab === extractAcademyTabFromHref(href);
}
