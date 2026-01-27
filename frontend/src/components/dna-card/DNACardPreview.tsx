"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type {
  DNACard,
  MasterDNAMetadata,
  MasterpieceDNAMetadata,
  CharacterDNAMetadata,
} from "@/types/dna-card";
import { DNA_CARD_CONFIG } from "./constants";

interface DNACardPreviewProps {
  card: DNACard;
  anchorRect?: DOMRect | null;
}

type PreviewPosition = "right" | "left" | "bottom";

export function DNACardPreview({ card, anchorRect }: DNACardPreviewProps) {
  const config = DNA_CARD_CONFIG[card.type];

  // P0: 동적 위치 계산 (useMemo로 동기적 계산)
  const position = useMemo<PreviewPosition>(() => {
    if (!anchorRect || typeof window === "undefined") return "right";

    const spaceRight = window.innerWidth - anchorRect.right;
    const spaceLeft = anchorRect.left;

    // 모바일: 항상 바텀시트
    if (window.innerWidth < 768) {
      return "bottom";
    } else if (spaceRight < 320 && spaceLeft > 320) {
      return "left";
    } else {
      return "right";
    }
  }, [anchorRect]);

  // 위치별 클래스 (P0 + P1 개선)
  const positionClasses: Record<PreviewPosition, string> = {
    right: "left-full ml-4 top-0",
    left: "right-full mr-4 top-0",
    bottom: "fixed inset-x-4 bottom-4 w-auto z-[100]", // 모바일 바텀시트
  };

  const cardHue = card.hue ?? config.hue;

  return (
    <motion.div
      initial={{ opacity: 0, y: position === "bottom" ? 20 : 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: position === "bottom" ? 20 : 10, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "absolute w-72 z-50",
        positionClasses[position],
        position === "bottom" && "max-w-md mx-auto"
      )}
    >
      {/* P1: 글래스모피즘 + Glow 스타일 */}
      <div
        className={cn(
          "relative rounded-2xl p-5 space-y-4",
          "bg-black/80 backdrop-blur-xl",
          "border border-white/10",
          "shadow-[0_8px_32px_rgba(0,0,0,0.4)]"
        )}
        style={
          {
            "--card-hue": cardHue,
          } as React.CSSProperties
        }
      >
        {/* Glow 효과 */}
        <div
          className="absolute inset-0 rounded-2xl -z-10 blur-xl opacity-30"
          style={{
            background: `linear-gradient(135deg, oklch(0.6 0.15 ${cardHue}) 0%, transparent 60%)`,
          }}
        />

        {/* 헤더 */}
        <div className="flex items-start gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `oklch(0.3 0.15 ${cardHue})` }}
          >
            <config.icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h4 className="font-bold text-white">{card.name}</h4>
            <p className="text-xs text-white/60">{config.labelEn}</p>
          </div>
        </div>

        {/* 타입별 상세 정보 */}
        {card.type === "master" && (
          <MasterPreviewContent metadata={card.metadata as MasterDNAMetadata} />
        )}
        {card.type === "masterpiece" && (
          <MasterpiecePreviewContent
            metadata={card.metadata as MasterpieceDNAMetadata}
          />
        )}
        {card.type === "character" && (
          <CharacterPreviewContent
            metadata={card.metadata as CharacterDNAMetadata}
          />
        )}

        {/* 액션 버튼들 */}
        <div className="flex gap-2 pt-3 border-t border-white/10">
          <button
            className="flex-1 px-3 py-2 text-xs font-medium rounded-lg text-white transition-all"
            style={{ backgroundColor: `oklch(0.5 0.15 ${cardHue})` }}
          >
            DNA Lab에서 분석
          </button>
          <button className="flex-1 px-3 py-2 text-xs font-medium rounded-lg bg-white/10 text-white/80 hover:bg-white/20 transition-colors">
            스토리에 적용
          </button>
        </div>
      </div>
    </motion.div>
  );
}

// 거장 프리뷰
function MasterPreviewContent({ metadata }: { metadata: MasterDNAMetadata }) {
  return (
    <div className="space-y-3">
      {/* 시그니처 기법 */}
      <div>
        <h5 className="text-[10px] font-medium text-white/50 uppercase mb-1">
          Signature Techniques
        </h5>
        <div className="flex flex-wrap gap-1">
          {metadata.signatureTechniques.slice(0, 3).map((tech, i) => (
            <span
              key={i}
              className="px-2 py-0.5 text-[10px] rounded-full bg-white/5 text-white/70"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* 컬러 팔레트 */}
      {metadata.colorPalettes?.[0] && (
        <div>
          <h5 className="text-[10px] font-medium text-white/50 uppercase mb-1">
            Color Palette
          </h5>
          <div className="flex gap-1">
            {metadata.colorPalettes[0].slice(0, 5).map((color, i) => (
              <div
                key={i}
                className="w-6 h-6 rounded-md border border-white/10"
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>
      )}

      {/* 필모그래피 */}
      {metadata.films && (
        <div>
          <h5 className="text-[10px] font-medium text-white/50 uppercase mb-1">
            Filmography
          </h5>
          <p className="text-xs text-white/60">
            {metadata.films.slice(0, 3).join(", ")}
            {metadata.films.length > 3 && ` 외 ${metadata.films.length - 3}편`}
          </p>
        </div>
      )}
    </div>
  );
}

// 작품 프리뷰
function MasterpiecePreviewContent({
  metadata,
}: {
  metadata: MasterpieceDNAMetadata;
}) {
  return (
    <div className="space-y-3">
      {/* 장르 */}
      <div>
        <h5 className="text-[10px] font-medium text-white/50 uppercase mb-1">
          Genres
        </h5>
        <div className="flex flex-wrap gap-1">
          {metadata.genres.map((genre, i) => (
            <span
              key={i}
              className="px-2 py-0.5 text-[10px] rounded-full bg-white/5 text-white/70"
            >
              {genre}
            </span>
          ))}
        </div>
      </div>

      {/* Logic Vector 요약 */}
      {metadata.logicVectorSummary && (
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
      )}
    </div>
  );
}

// 캐릭터 프리뷰
function CharacterPreviewContent({
  metadata,
}: {
  metadata: CharacterDNAMetadata;
}) {
  return (
    <div className="space-y-3">
      {/* 태그 */}
      <div className="flex flex-wrap gap-1">
        {metadata.tags.slice(0, 4).map((tag, i) => (
          <span
            key={i}
            className="px-2 py-0.5 text-[10px] rounded-full bg-white/5 text-white/70"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* 메모리 키프레임 */}
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

      {/* 캐릭터 프리뷰 이미지 */}
      {metadata.primaryImageUrl && (
        <div className="rounded-lg overflow-hidden h-20">
          <img
            src={metadata.primaryImageUrl}
            alt="Character preview"
            className="w-full h-full object-cover"
          />
        </div>
      )}
    </div>
  );
}
