"use client";

import type { MegaAppHeaderProps } from "./types";
import { getTheme } from "./constants";

/**
 * MegaAppHeader - Glass morphism header with theme glow
 *
 * Features:
 * - Glass morphism background (backdrop-blur)
 * - Theme-colored glow effect on icon
 * - Optional headerRight slot for stats/actions
 */
export function MegaAppHeader({
  appId,
  title,
  subtitle,
  icon: Icon,
  headerRight,
}: MegaAppHeaderProps) {
  const theme = getTheme(appId);

  return (
    <div className="flex-shrink-0 border-b bg-stitch-surface backdrop-blur-xl border-white/5">
      <div className="container py-4">
        <div className="flex items-center gap-3">
          {/* Icon with theme glow */}
          <div
            className="p-2 rounded-lg bg-white/5"
            style={{
              boxShadow: `0 0 20px ${theme.glowColor}`,
            }}
          >
            <Icon
              className="w-6 h-6"
              style={{ color: `oklch(0.74 0.18 ${theme.hue})` }}
            />
          </div>

          {/* Title & Subtitle */}
          <div>
            <h1 className="text-xl font-bold text-white">{title}</h1>
            <p className="text-sm text-white/60">{subtitle}</p>
          </div>

          {/* Optional Right Slot */}
          {headerRight && <div className="ml-auto">{headerRight}</div>}
        </div>
      </div>
    </div>
  );
}
