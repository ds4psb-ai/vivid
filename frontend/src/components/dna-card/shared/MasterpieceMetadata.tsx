"use client";

import type { MasterpieceDNAMetadata } from "@/types/dna-card";
import { MetadataSection } from "./MetadataSection";

interface MasterpieceMetadataProps {
  metadata: MasterpieceDNAMetadata;
  variant: "compact" | "full";
}

/**
 * MasterpieceMetadata - 작품 DNA 메타데이터 표시 컴포넌트
 *
 * 공통 컴포넌트로 DNACardPreview와 SidePanel에서 재사용
 *
 * @param metadata - 작품 DNA 메타데이터
 * @param variant - compact: 프리뷰용, full: 사이드패널용
 */
export function MasterpieceMetadata({
  metadata,
  variant,
}: MasterpieceMetadataProps) {
  const isCompact = variant === "compact";

  return (
    <div className={isCompact ? "space-y-3" : "space-y-6"}>
      {/* Genres */}
      {metadata.genres.length > 0 && (
        <MetadataSection title="Genres" isCompact={isCompact}>
          <div className="flex flex-wrap gap-1">
            {metadata.genres.map((genre, i) => (
              <span
                key={i}
                className={`px-2 py-0.5 rounded-full ${
                  isCompact
                    ? "text-[10px] bg-white/5 text-white/70"
                    : "text-xs bg-[var(--surface-2)] text-[var(--fg-default)] border border-[var(--border-muted)]"
                }`}
              >
                {genre}
              </span>
            ))}
          </div>
        </MetadataSection>
      )}

      {/* Logic Vector Summary */}
      {metadata.logicVectorSummary && (
        <div className={isCompact ? "space-y-1" : "space-y-3"}>
          {!isCompact && (
            <h3 className="text-xs font-semibold text-[var(--fg-muted)] uppercase tracking-wider">
              Logic Vector
            </h3>
          )}

          {isCompact ? (
            <div className="text-xs text-white/60 space-y-1">
              <p>
                <span className="text-white/40">Composition:</span>{" "}
                {metadata.logicVectorSummary.compositionStyle}
              </p>
              <p>
                <span className="text-white/40">Lighting:</span>{" "}
                {metadata.logicVectorSummary.lightingPattern}
              </p>
              <p>
                <span className="text-white/40">Pacing:</span>{" "}
                {metadata.logicVectorSummary.pacingSignature}
              </p>
            </div>
          ) : (
            <div className="grid gap-3">
              <LogicVectorCard
                label="Composition"
                value={metadata.logicVectorSummary.compositionStyle}
              />
              <LogicVectorCard
                label="Lighting"
                value={metadata.logicVectorSummary.lightingPattern}
              />
              <LogicVectorCard
                label="Pacing"
                value={metadata.logicVectorSummary.pacingSignature}
              />
            </div>
          )}
        </div>
      )}

      {/* IP ID (full variant only) */}
      {!isCompact && (
        <div className="pt-2 border-t border-[var(--border-muted)]">
          <div className="text-[10px] font-medium text-[var(--fg-muted)] uppercase tracking-wider">
            IP ID
          </div>
          <div className="text-xs font-mono text-[var(--fg-muted)]">
            {metadata.ipId}
          </div>
        </div>
      )}
    </div>
  );
}

function LogicVectorCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border-muted)]">
      <div className="text-[10px] font-medium text-[var(--fg-muted)] uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className="text-sm text-[var(--fg-default)]">{value}</div>
    </div>
  );
}
