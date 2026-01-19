"use client";

import React from "react";
import { Shield, AlertTriangle, Ban } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface LicenseStatusBadgeProps {
  status: "allowed" | "restricted" | "prohibited";
  size?: "small" | "medium" | "large";
  showLabel?: boolean;
}

const statusConfig = {
  allowed: {
    labelKo: "허용",
    labelEn: "Allowed",
    icon: Shield,
    bgClass: "bg-green-500/90",
    textClass: "text-white",
    description: {
      ko: "이 IP로 팬 창작물을 만들 수 있습니다",
      en: "You can create fan content with this IP",
    },
  },
  restricted: {
    labelKo: "제한",
    labelEn: "Restricted",
    icon: AlertTriangle,
    bgClass: "bg-yellow-500/90",
    textClass: "text-black",
    description: {
      ko: "일부 제한이 있습니다. 생성 전 확인이 필요합니다",
      en: "Some restrictions apply. Confirmation required before generating",
    },
  },
  prohibited: {
    labelKo: "불가",
    labelEn: "Prohibited",
    icon: Ban,
    bgClass: "bg-red-500/90",
    textClass: "text-white",
    description: {
      ko: "현재 이 IP로 생성이 불가능합니다",
      en: "Generation is not available for this IP",
    },
  },
};

export default function LicenseStatusBadge({
  status,
  size = "small",
  showLabel = true,
}: LicenseStatusBadgeProps) {
  const { language } = useLanguage();
  const config = statusConfig[status];
  const Icon = config.icon;
  const label = language === "ko" ? config.labelKo : config.labelEn;

  const sizeClasses = {
    small: {
      container: "text-xs px-2 py-1",
      icon: "w-3 h-3",
    },
    medium: {
      container: "text-sm px-2.5 py-1.5",
      icon: "w-4 h-4",
    },
    large: {
      container: "text-base px-3 py-2",
      icon: "w-5 h-5",
    },
  };

  // Don't show badge for allowed status (clean UI)
  if (status === "allowed") {
    return null;
  }

  return (
    <span
      className={
        "inline-flex items-center gap-1 rounded-full font-medium " +
        config.bgClass + " " +
        config.textClass + " " +
        sizeClasses[size].container
      }
      title={config.description[language]}
    >
      <Icon className={sizeClasses[size].icon} />
      {showLabel && <span>{label}</span>}
    </span>
  );
}

// Export for use in modals and dialogs
export function LicenseStatusInfo({
  status,
}: {
  status: "allowed" | "restricted" | "prohibited";
}) {
  const { language } = useLanguage();
  const config = statusConfig[status];
  const Icon = config.icon;
  const label = language === "ko" ? config.labelKo : config.labelEn;
  const description = config.description[language];

  return (
    <div className="flex items-start gap-3 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50">
      <div className={"p-2 rounded-full " + config.bgClass}>
        <Icon className={"w-5 h-5 " + config.textClass} />
      </div>
      <div>
        <h4 className="font-medium text-slate-900 dark:text-white">{label}</h4>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          {description}
        </p>
      </div>
    </div>
  );
}
