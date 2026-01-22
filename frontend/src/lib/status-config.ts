/**
 * Centralized Status Configuration
 *
 * Single source of truth for status colors, icons, and labels
 * across HumanCloud and other status-based components.
 */

import { LucideIcon, Clock, CheckCircle, Play, Send, FileCheck, AlertTriangle } from "lucide-react";

// =============================================================================
// Request Status Configuration
// =============================================================================

export interface RequestStatusConfig {
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
  labelKo: string;
}

export const REQUEST_STATUS_CONFIG: Record<string, RequestStatusConfig> = {
  draft: {
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
    borderColor: "border-slate-500/30",
    label: "Draft",
    labelKo: "초안",
  },
  open: {
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    label: "Open",
    labelKo: "공개",
  },
  assigned: {
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    label: "Assigned",
    labelKo: "배정됨",
  },
  in_progress: {
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    label: "In Progress",
    labelKo: "진행중",
  },
  review: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    label: "Review",
    labelKo: "검토중",
  },
  delivered: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    label: "Delivered",
    labelKo: "납품됨",
  },
  completed: {
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    label: "Completed",
    labelKo: "완료",
  },
  cancelled: {
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    label: "Cancelled",
    labelKo: "취소됨",
  },
};

// =============================================================================
// Assignment Status Configuration
// =============================================================================

export interface AssignmentStatusConfig {
  color: string;
  bgColor: string;
  borderColor: string;
  icon: LucideIcon;
  label: string;
  labelKo: string;
}

export const ASSIGNMENT_STATUS_CONFIG: Record<string, AssignmentStatusConfig> = {
  pending: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/30",
    icon: Clock,
    label: "Pending",
    labelKo: "대기중",
  },
  accepted: {
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    icon: CheckCircle,
    label: "Accepted",
    labelKo: "수락됨",
  },
  in_progress: {
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    icon: Play,
    label: "In Progress",
    labelKo: "진행중",
  },
  delivered: {
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    icon: Send,
    label: "Delivered",
    labelKo: "납품됨",
  },
  completed: {
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    icon: FileCheck,
    label: "Completed",
    labelKo: "완료",
  },
  rejected: {
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    icon: AlertTriangle,
    label: "Rejected",
    labelKo: "거절됨",
  },
};

// =============================================================================
// Filter Options
// =============================================================================

export interface StatusFilterOption {
  value: string;
  label: string;
  labelKo: string;
}

export const REQUEST_CATEGORY_FILTERS: StatusFilterOption[] = [
  { value: "", label: "All", labelKo: "전체" },
  { value: "video_creative", label: "Video", labelKo: "영상" },
  { value: "image_design", label: "Image", labelKo: "이미지" },
  { value: "motion_graphics", label: "Motion", labelKo: "모션" },
  { value: "short_form", label: "Short-form", labelKo: "숏폼" },
  { value: "brand_content", label: "Brand", labelKo: "브랜드" },
];

export const ASSIGNMENT_STATUS_FILTERS: StatusFilterOption[] = [
  { value: "", label: "All", labelKo: "전체" },
  { value: "pending", label: "Pending", labelKo: "대기중" },
  { value: "accepted", label: "Accepted", labelKo: "수락됨" },
  { value: "in_progress", label: "In Progress", labelKo: "진행중" },
  { value: "delivered", label: "Delivered", labelKo: "납품됨" },
  { value: "completed", label: "Completed", labelKo: "완료" },
];

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get request status configuration with fallback
 */
export function getRequestStatus(status: string): RequestStatusConfig {
  return REQUEST_STATUS_CONFIG[status] || REQUEST_STATUS_CONFIG.draft;
}

/**
 * Get assignment status configuration with fallback
 */
export function getAssignmentStatus(status: string): AssignmentStatusConfig {
  return ASSIGNMENT_STATUS_CONFIG[status] || ASSIGNMENT_STATUS_CONFIG.pending;
}

/**
 * Get localized label for a status
 */
export function getStatusLabel(
  config: RequestStatusConfig | AssignmentStatusConfig,
  language: string
): string {
  return language === "ko" ? config.labelKo : config.label;
}
