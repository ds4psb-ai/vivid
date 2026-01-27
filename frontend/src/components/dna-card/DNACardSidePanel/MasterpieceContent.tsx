"use client";

import Image from "next/image";
import type { DNACard, MasterpieceDNAMetadata } from "@/types/dna-card";
import { DNA_CARD_CONFIG } from "../constants";
import { MasterpieceMetadata } from "../shared";

interface MasterpieceContentProps {
  card: DNACard & { metadata: MasterpieceDNAMetadata };
}

export function MasterpieceContent({ card }: MasterpieceContentProps) {
  const { metadata } = card;
  const config = DNA_CARD_CONFIG[card.type];

  return (
    <div className="space-y-6">
      {/* Thumbnail */}
      <div className="relative aspect-video rounded-xl overflow-hidden bg-black/20">
        {card.thumbnailUrl ? (
          <Image
            src={card.thumbnailUrl}
            alt={card.name}
            fill
            className="object-cover"
            sizes="400px"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900">
            <config.icon className="w-16 h-16 text-white/20" />
          </div>
        )}
      </div>

      {/* Description */}
      <p className="text-sm text-[var(--fg-muted)] leading-relaxed">
        {card.description}
      </p>

      {/* Metadata (using shared component) */}
      <MasterpieceMetadata metadata={metadata} variant="full" />
    </div>
  );
}
