"use client";

import Image from "next/image";
import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";

type LicenseStatus = "allowed" | "restricted" | "prohibited";

interface IPRailCardProps {
  title: string;
  subtitle?: string;
  thumbnailUrl?: string;
  genres?: string[];
  licenseStatus?: LicenseStatus;
}

const STATUS_STYLES: Record<LicenseStatus, { label: string; icon: typeof ShieldCheck; className: string }> = {
  allowed: {
    label: "허용",
    icon: ShieldCheck,
    className: "text-emerald-400 border-emerald-400/30 bg-emerald-500/10",
  },
  restricted: {
    label: "제한",
    icon: ShieldAlert,
    className: "text-amber-400 border-amber-400/30 bg-amber-500/10",
  },
  prohibited: {
    label: "금지",
    icon: ShieldX,
    className: "text-rose-400 border-rose-400/30 bg-rose-500/10",
  },
};

export function IPRailCard({
  title,
  subtitle,
  thumbnailUrl,
  genres,
  licenseStatus = "allowed",
}: IPRailCardProps) {
  const status = STATUS_STYLES[licenseStatus];
  const StatusIcon = status.icon;

  return (
    <div className="group h-full overflow-hidden rounded-2xl border border-[var(--border-muted)] bg-[var(--surface-1)] hover:border-[var(--border-strong)] transition-all">
      <div className="relative h-32 w-full bg-black/10">
        {thumbnailUrl ? (
          <Image
            src={thumbnailUrl}
            alt={title}
            fill
            sizes="(max-width: 1024px) 220px, 220px"
            className="object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xs text-[var(--fg-muted)]">
            No Image
          </div>
        )}
      </div>
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-sm font-semibold text-[var(--fg-0)] line-clamp-1">{title}</p>
            {subtitle && (
              <p className="text-xs text-[var(--fg-muted)] line-clamp-1">{subtitle}</p>
            )}
          </div>
          <span
            className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${status.className}`}
          >
            <StatusIcon className="h-3 w-3" />
            {status.label}
          </span>
        </div>
        {genres && genres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {genres.slice(0, 3).map((genre) => (
              <span
                key={genre}
                className="rounded-full bg-[var(--surface-2)] px-2 py-0.5 text-[10px] text-[var(--fg-muted)]"
              >
                {genre}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
