"use client";

import type { DNACard } from "@/types/dna-card";
import { isMasterCard, isMasterpieceCard, isCharacterCard } from "@/types/dna-card";
import { MasterContent } from "./MasterContent";
import { MasterpieceContent } from "./MasterpieceContent";
import { CharacterContent } from "./CharacterContent";

interface SidePanelContentProps {
  card: DNACard;
}

export function SidePanelContent({ card }: SidePanelContentProps) {
  if (isMasterCard(card)) {
    return <MasterContent card={card} />;
  }

  if (isMasterpieceCard(card)) {
    return <MasterpieceContent card={card} />;
  }

  if (isCharacterCard(card)) {
    return <CharacterContent card={card} />;
  }

  // Fallback for unknown card types
  return (
    <div className="text-center py-8 text-[var(--fg-muted)]">
      Unknown card type
    </div>
  );
}
