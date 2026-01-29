import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/**
 * Mega App Identifiers
 * Each mega app has a unique ID for theming and routing
 */
export type MegaAppId = "dna-lab" | "story-engine" | "production";

/**
 * Tab Configuration for Mega Apps
 */
export interface MegaAppTab {
  value: string;
  label: string;
  labelEn: string;
  icon: ReactNode;
  description: string;
  isNew?: boolean;
  isDisabled?: boolean;
  badge?: string;
}

/**
 * Theme Configuration for Mega Apps
 * Uses Oklch color space for perceptual uniformity
 */
export interface MegaAppTheme {
  id: MegaAppId;
  hue: number;
  cssVar: string;
  glowColor: string;
}

/**
 * Workflow Step for Progress Component
 */
export interface WorkflowStep {
  id: MegaAppId;
  label: string;
  labelEn: string;
  href: string;
  description: string;
}

/**
 * Header Props
 */
export interface MegaAppHeaderProps {
  appId: MegaAppId;
  title: string;
  subtitle: string;
  icon: LucideIcon;
  headerRight?: ReactNode;
}

/**
 * Workflow Progress Props
 */
export interface WorkflowProgressProps {
  currentAppId: MegaAppId;
}

/**
 * Aurora Background Props
 */
export interface MegaAppAuroraProps {
  appId: MegaAppId;
  opacity?: number;
}
