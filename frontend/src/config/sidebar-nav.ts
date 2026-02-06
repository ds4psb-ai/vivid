import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Settings,
  Gift,
  Upload,
  Sparkles,
  ClipboardCopy,
  Wrench,
  Brain,
  ClipboardCheck,
  Shield,
} from "lucide-react";

export interface SidebarNavItem {
  id: string;
  icon: LucideIcon;
  label: string;
  href: string;
  dividerBefore?: boolean;
  adminOnly?: boolean;
}

export const SIDEBAR_NAV_ITEMS: SidebarNavItem[] = [
  { id: "home", icon: LayoutDashboard, label: "홈", href: "/" },
  { id: "setup", icon: Settings, label: "시작", href: "/?tab=setup" },
  { id: "credit", icon: Gift, label: "크레딧", href: "/?tab=credit" },
  { id: "upload", icon: Upload, label: "업로드", href: "/?tab=upload", dividerBefore: true },
  { id: "prompt", icon: Sparkles, label: "빌더", href: "/?tab=prompt" },
  { id: "parse", icon: ClipboardCopy, label: "파싱", href: "/?tab=parse" },
  { id: "tools", icon: Wrench, label: "툴", href: "/?tab=tools" },
  { id: "vibe", icon: Brain, label: "바이브", href: "/?tab=vibe", dividerBefore: true },
  { id: "homework", icon: ClipboardCheck, label: "과제", href: "/?tab=homework" },
  { id: "admin", icon: Shield, label: "관리", href: "/?tab=admin", dividerBefore: true, adminOnly: true },
];
