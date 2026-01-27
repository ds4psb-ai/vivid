"use client";

import type { MasterDNAMetadata } from "@/types/dna-card";

interface MasterMetadataProps {
  metadata: MasterDNAMetadata;
  hue: number;
  variant: "compact" | "full";
}

/**
 * MasterMetadata - 거장 DNA 메타데이터 표시 컴포넌트
 *
 * 공통 컴포넌트로 DNACardPreview와 SidePanel에서 재사용
 *
 * @param metadata - 거장 DNA 메타데이터
 * @param hue - OKLCH 색상 hue 값
 * @param variant - compact: 프리뷰용, full: 사이드패널용
 */
export function MasterMetadata({ metadata, hue, variant }: MasterMetadataProps) {
  const isCompact = variant === "compact";

  return (
    <div className={isCompact ? "space-y-3" : "space-y-6"}>
      {/* Signature Techniques */}
      {metadata.signatureTechniques.length > 0 && (
        <MetadataSection
          title="Signature Techniques"
          isCompact={isCompact}
        >
          <div className="flex flex-wrap gap-1">
            {metadata.signatureTechniques
              .slice(0, isCompact ? 3 : undefined)
              .map((tech, i) => (
                <span
                  key={i}
                  className={`px-2 py-0.5 rounded-full ${
                    isCompact
                      ? "text-[10px] bg-white/5 text-white/70"
                      : "text-xs bg-[var(--surface-2)] text-[var(--fg-default)] border border-[var(--border-muted)]"
                  }`}
                >
                  {tech}
                </span>
              ))}
          </div>
        </MetadataSection>
      )}

      {/* Signature Moods (full variant only) */}
      {!isCompact && metadata.signatureMoods.length > 0 && (
        <MetadataSection title="Signature Moods" isCompact={false}>
          <div className="flex flex-wrap gap-2">
            {metadata.signatureMoods.map((mood, i) => (
              <span
                key={i}
                className="px-3 py-1 text-xs rounded-full"
                style={{
                  backgroundColor: `oklch(0.25 0.05 ${hue})`,
                  color: `oklch(0.8 0.12 ${hue})`,
                }}
              >
                {mood}
              </span>
            ))}
          </div>
        </MetadataSection>
      )}

      {/* Color Palette */}
      {metadata.colorPalettes?.[0] && (
        <MetadataSection title="Color Palette" isCompact={isCompact}>
          <div className="flex gap-1">
            {metadata.colorPalettes[0]
              .slice(0, isCompact ? 5 : undefined)
              .map((color, i) => (
                <div
                  key={i}
                  className={`rounded-md border border-white/10 ${
                    isCompact ? "w-6 h-6" : "w-10 h-10 shadow-sm"
                  }`}
                  style={{ backgroundColor: color }}
                  title={isCompact ? undefined : color}
                />
              ))}
          </div>
        </MetadataSection>
      )}

      {/* Filmography */}
      {metadata.films && metadata.films.length > 0 && (
        <MetadataSection title="Filmography" isCompact={isCompact}>
          {isCompact ? (
            <p className="text-xs text-white/60">
              {metadata.films.slice(0, 3).join(", ")}
              {metadata.films.length > 3 && ` 외 ${metadata.films.length - 3}편`}
            </p>
          ) : (
            <ul className="space-y-1">
              {metadata.films.map((film, i) => (
                <li
                  key={i}
                  className="text-sm text-[var(--fg-default)] flex items-center gap-2"
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: `oklch(0.7 0.15 ${hue})` }}
                  />
                  {film}
                </li>
              ))}
            </ul>
          )}
        </MetadataSection>
      )}
    </div>
  );
}

function MetadataSection({
  title,
  isCompact,
  children,
}: {
  title: string;
  isCompact: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={isCompact ? "" : "space-y-2"}>
      <h5
        className={`font-medium uppercase tracking-wider ${
          isCompact
            ? "text-[10px] text-white/50 mb-1"
            : "text-xs text-[var(--fg-muted)]"
        }`}
      >
        {title}
      </h5>
      {children}
    </div>
  );
}
