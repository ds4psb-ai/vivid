"use client";

import type { DNACard, MasterDNAMetadata } from "@/types/dna-card";
import { DNA_CARD_CONFIG } from "../constants";
import { MasterMetadata } from "../shared";

interface MasterContentProps {
  card: DNACard & { metadata: MasterDNAMetadata };
}

export function MasterContent({ card }: MasterContentProps) {
  const { metadata } = card;
  const config = DNA_CARD_CONFIG[card.type];
  const cardHue = card.hue ?? config.hue;

  return (
    <div className="space-y-6">
      {/* Thumbnail */}
      <div className="relative aspect-video rounded-xl overflow-hidden bg-black/20">
        {card.thumbnailUrl ? (
          <img
            src={card.thumbnailUrl}
            alt={card.name}
            className="w-full h-full object-cover"
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
      <MasterMetadata metadata={metadata} hue={cardHue} variant="full" />
    </div>
  );
}
