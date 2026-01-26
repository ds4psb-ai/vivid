"use client";

import { getTheme } from "./constants";
import type { MegaAppAuroraProps } from "./types";

/**
 * MegaAppAurora - Theme-tinted aurora background
 *
 * Features:
 * - Subtle radial gradient overlay
 * - Theme-colored tint
 * - Customizable opacity
 * - Non-interactive (pointer-events-none)
 */
export function MegaAppAurora({ appId, opacity = 0.15 }: MegaAppAuroraProps) {
  const theme = getTheme(appId);

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      aria-hidden="true"
    >
      {/* Top-right glow */}
      <div
        className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
        style={{
          background: `radial-gradient(circle, oklch(0.64 0.18 ${theme.hue} / ${opacity}) 0%, transparent 70%)`,
        }}
      />

      {/* Bottom-left subtle glow */}
      <div
        className="absolute -bottom-1/4 -left-1/4 w-1/3 h-1/3 rounded-full blur-3xl"
        style={{
          background: `radial-gradient(circle, oklch(0.64 0.18 ${theme.hue} / ${opacity * 0.5}) 0%, transparent 70%)`,
        }}
      />
    </div>
  );
}
