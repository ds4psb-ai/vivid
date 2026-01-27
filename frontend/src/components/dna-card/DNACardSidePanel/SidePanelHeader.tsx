"use client";

import { X } from "lucide-react";
import type { DNACard } from "@/types/dna-card";
import { DNA_CARD_CONFIG } from "../constants";

interface SidePanelHeaderProps {
  card: DNACard;
  onClose: () => void;
}

export function SidePanelHeader({ card, onClose }: SidePanelHeaderProps) {
  const config = DNA_CARD_CONFIG[card.type];
  const Icon = config.icon;

  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-muted)]">
      <div className="flex items-center gap-3">
        {/* Type Icon */}
        <div
          className="p-2 rounded-lg"
          style={{
            backgroundColor: `oklch(0.25 0.05 ${card.hue ?? config.hue})`,
          }}
        >
          <Icon
            className="w-5 h-5"
            style={{ color: `oklch(0.75 0.15 ${card.hue ?? config.hue})` }}
          />
        </div>

        {/* Name and Type */}
        <div>
          <h2 className="font-bold text-[var(--fg-default)] text-lg">
            {card.name}
          </h2>
          <span className="text-xs text-[var(--fg-muted)]">{config.label}</span>
        </div>
      </div>

      {/* Close Button */}
      <button
        onClick={onClose}
        className="p-2 rounded-lg hover:bg-[var(--surface-2)] text-[var(--fg-muted)] hover:text-[var(--fg-default)] transition-colors"
        aria-label="Close"
      >
        <X className="w-5 h-5" />
      </button>
    </div>
  );
}
