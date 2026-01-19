"use client";

import React from "react";
import Link from "next/link";
import { useLanguage } from "@/contexts/LanguageContext";
import LicenseStatusBadge from "./LicenseStatusBadge";

interface IPCardProps {
  id: string;
  slug: string;
  nameKo: string;
  nameEn: string;
  thumbnailUrl?: string | null;
  genre?: string[];
  tags?: string[];
  presetCount: number;
  generationCount: number;
  licenseStatus: "allowed" | "restricted" | "prohibited";
  isFeatured?: boolean;
  size?: "small" | "medium" | "large";
}

export default function IPCard({
  id,
  slug,
  nameKo,
  nameEn,
  thumbnailUrl,
  genre = [],
  tags = [],
  presetCount,
  generationCount,
  licenseStatus,
  isFeatured = false,
  size = "medium",
}: IPCardProps) {
  const { language } = useLanguage();
  const name = language === "ko" ? nameKo : nameEn;

  const sizeClasses = {
    small: "w-40",
    medium: "w-48",
    large: "w-56",
  };

  const heightClasses = {
    small: "h-52",
    medium: "h-64",
    large: "h-72",
  };

  return (
    <Link
      href={"/ip/" + slug}
      className={"group block " + sizeClasses[size] + " focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 rounded-xl"}
    >
      {/* Thumbnail */}
      <div className={"relative " + sizeClasses[size] + " " + heightClasses[size] + " rounded-xl overflow-hidden bg-slate-100 dark:bg-slate-800 mb-2"}>
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-violet-500/20 to-pink-500/20">
            🎬
          </div>
        )}

        {/* Featured badge */}
        {isFeatured && (
          <div className="absolute top-2 left-2">
            <span className="text-xs px-2 py-1 rounded-full bg-violet-500/90 text-white font-medium">
              Featured
            </span>
          </div>
        )}

        {/* License status badge */}
        <div className="absolute top-2 right-2">
          <LicenseStatusBadge status={licenseStatus} size="small" />
        </div>

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute bottom-3 left-3 right-3">
            <div className="flex items-center gap-2 text-white text-xs">
              <span>{presetCount} presets</span>
              <span className="w-1 h-1 rounded-full bg-white/50" />
              <span>{generationCount.toLocaleString()} created</span>
            </div>
          </div>
        </div>
      </div>

      {/* Title */}
      <h3 className="text-sm font-medium text-slate-900 dark:text-white truncate group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
        {name}
      </h3>

      {/* Genre tags */}
      {genre.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {genre.slice(0, 2).map((g) => (
            <span
              key={g}
              className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            >
              {g}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
