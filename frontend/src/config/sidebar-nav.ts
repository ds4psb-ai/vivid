import type { LucideIcon } from "lucide-react";
import {
  Layers,
  PenTool,
  Users,
  Wrench,
  Cloud,
  Sparkles,
  GraduationCap,
  GitBranch,
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
  { id: "dimension", icon: Layers, label: "만들기", href: "/dimension" },
  { id: "studio", icon: PenTool, label: "스튜디오", href: "/studio" },
  { id: "characters", icon: Users, label: "캐릭터", href: "/characters" },
  {
    id: "tools",
    icon: Wrench,
    label: "도구",
    href: "/tools",
    dividerBefore: true,
  },
  { id: "humancloud", icon: Cloud, label: "휴먼클라우드", href: "/humancloud" },
  {
    id: "singularity",
    icon: Sparkles,
    label: "싱귤래리티",
    href: "/singularity",
  },
  {
    id: "academy",
    icon: GraduationCap,
    label: "아카데미",
    href: "/",
    dividerBefore: true,
  },
  { id: "flow", icon: GitBranch, label: "워크플로우", href: "/flow" },
  {
    id: "admin",
    icon: Shield,
    label: "관리자",
    href: "/admin",
    dividerBefore: true,
    adminOnly: true,
  },
];
