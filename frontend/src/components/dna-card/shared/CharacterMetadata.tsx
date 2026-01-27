"use client";

import Image from "next/image";
import type { CharacterDNAMetadata } from "@/types/dna-card";

interface CharacterMetadataProps {
  metadata: CharacterDNAMetadata;
  hue: number;
  variant: "compact" | "full";
}

/**
 * CharacterMetadata - 캐릭터 DNA 메타데이터 표시 컴포넌트
 *
 * 공통 컴포넌트로 DNACardPreview와 SidePanel에서 재사용
 *
 * @param metadata - 캐릭터 DNA 메타데이터
 * @param hue - OKLCH 색상 hue 값
 * @param variant - compact: 프리뷰용, full: 사이드패널용
 */
export function CharacterMetadata({
  metadata,
  hue,
  variant,
}: CharacterMetadataProps) {
  const isCompact = variant === "compact";

  return (
    <div className={isCompact ? "space-y-3" : "space-y-6"}>
      {/* Tags */}
      {metadata.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {metadata.tags.slice(0, isCompact ? 4 : undefined).map((tag, i) => (
            <span
              key={i}
              className={`px-2 py-0.5 rounded-full ${
                isCompact ? "text-[10px] bg-white/5 text-white/70" : "text-xs"
              }`}
              style={
                !isCompact
                  ? {
                      backgroundColor: `oklch(0.25 0.05 ${hue})`,
                      color: `oklch(0.8 0.12 ${hue})`,
                    }
                  : undefined
              }
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Stats */}
      {isCompact ? (
        <div className="text-xs text-white/60 space-y-1">
          <p>
            <span className="text-white/40">Memory Keyframes:</span>{" "}
            {metadata.memoryKeyframeCount}개
          </p>
          {metadata.consistencyScore !== undefined && (
            <p>
              <span className="text-white/40">Consistency:</span>{" "}
              {Math.round(metadata.consistencyScore * 100)}%
            </p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            label="Memory Keyframes"
            value={metadata.memoryKeyframeCount.toString()}
          />
          {metadata.consistencyScore !== undefined && (
            <StatCard
              label="Consistency"
              value={`${Math.round(metadata.consistencyScore * 100)}%`}
            />
          )}
        </div>
      )}

      {/* Character Image (compact variant only) */}
      {isCompact && metadata.primaryImageUrl && (
        <div className="relative rounded-lg overflow-hidden h-20">
          <Image
            src={metadata.primaryImageUrl}
            alt="Character preview"
            fill
            className="object-cover"
            sizes="200px"
          />
        </div>
      )}

      {/* Character ID (full variant only) */}
      {!isCompact && (
        <div className="pt-2 border-t border-[var(--border-muted)]">
          <div className="text-[10px] font-medium text-[var(--fg-muted)] uppercase tracking-wider">
            Character ID
          </div>
          <div className="text-xs font-mono text-[var(--fg-muted)]">
            {metadata.characterId}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4 rounded-lg bg-[var(--surface-2)] border border-[var(--border-muted)]">
      <div className="text-[10px] font-medium text-[var(--fg-muted)] uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className="text-2xl font-bold text-[var(--fg-default)]">{value}</div>
    </div>
  );
}
