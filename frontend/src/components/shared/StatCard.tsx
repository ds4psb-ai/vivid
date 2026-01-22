/**
 * Stat Card Component
 *
 * Unified stat card supporting multiple variants:
 * - default: Simple stat with icon and value
 * - dashboard: With helper text and BETA badge (Creator pages)
 * - stripe: With colored top stripe (Creator Hub page)
 * - lusion: Lusion-style with glow effect (HumanCloud page)
 */

import { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// Semantic tone colors (for dashboard/stripe variants)
export type StatTone = "success" | "warning" | "neutral" | "info";

// Direct colors (for default variant)
export type StatColor = "purple" | "blue" | "green" | "yellow" | "red" | "gray" | "orange" | "emerald" | "violet" | "slate" | "amber";

export type StatVariant = "default" | "dashboard" | "stripe" | "lusion";

interface BaseStatCardProps {
  icon: LucideIcon;
  value: string | number;
  loading?: boolean;
}

interface DefaultVariantProps extends BaseStatCardProps {
  variant?: "default";
  title: string;
  color?: StatColor;
  subtitle?: string;
  trend?: {
    value: number;
    direction: "up" | "down";
  };
}

interface DashboardVariantProps extends BaseStatCardProps {
  variant: "dashboard";
  title: string;
  helper: string;
  tone?: StatTone;
  badge?: string;
}

interface StripeVariantProps extends BaseStatCardProps {
  variant: "stripe";
  label: string;
  helper: string;
  tone?: StatTone;
  badge?: string;
}

interface LusionVariantProps extends BaseStatCardProps {
  variant: "lusion";
  label: string;
  color?: StatColor;
}

export type StatCardProps =
  | DefaultVariantProps
  | DashboardVariantProps
  | StripeVariantProps
  | LusionVariantProps;

// Color mappings for direct colors
const COLOR_MAP: Record<StatColor, { icon: string; bg: string; stripe: string; glow: string }> = {
  purple: { icon: "text-purple-400", bg: "bg-purple-500/10", stripe: "bg-purple-500/60", glow: "bg-purple-500" },
  blue: { icon: "text-blue-400", bg: "bg-blue-500/10", stripe: "bg-blue-500/60", glow: "bg-blue-500" },
  green: { icon: "text-green-400", bg: "bg-green-500/10", stripe: "bg-green-500/60", glow: "bg-green-500" },
  yellow: { icon: "text-yellow-400", bg: "bg-yellow-500/10", stripe: "bg-yellow-500/60", glow: "bg-yellow-500" },
  red: { icon: "text-red-400", bg: "bg-red-500/10", stripe: "bg-red-500/60", glow: "bg-red-500" },
  gray: { icon: "text-slate-300", bg: "bg-slate-500/10", stripe: "bg-slate-500/40", glow: "bg-slate-500" },
  orange: { icon: "text-orange-400", bg: "bg-orange-500/10", stripe: "bg-orange-500/60", glow: "bg-orange-500" },
  emerald: { icon: "text-emerald-400", bg: "bg-emerald-500/10", stripe: "bg-emerald-500/60", glow: "bg-emerald-500" },
  violet: { icon: "text-violet-400", bg: "bg-violet-500/10", stripe: "bg-violet-500/60", glow: "bg-violet-500" },
  slate: { icon: "text-slate-300", bg: "bg-slate-500/10", stripe: "bg-slate-500/40", glow: "bg-slate-500" },
  amber: { icon: "text-amber-400", bg: "bg-amber-500/10", stripe: "bg-amber-500/60", glow: "bg-amber-500" },
};

// Tone to color mapping for semantic tones
const TONE_MAP: Record<StatTone, { icon: string; bg: string; stripe: string }> = {
  success: { icon: "text-emerald-400", bg: "bg-emerald-500/10", stripe: "bg-emerald-500/60" },
  warning: { icon: "text-amber-400", bg: "bg-amber-500/10", stripe: "bg-amber-500/60" },
  neutral: { icon: "text-slate-300", bg: "bg-slate-500/10", stripe: "bg-slate-500/40" },
  info: { icon: "text-violet-400", bg: "bg-violet-500/10", stripe: "bg-violet-500/60" },
};

// Default variant (existing API)
function DefaultStatCard({
  title,
  value,
  icon: Icon,
  color = "purple",
  subtitle,
  loading = false,
  trend,
}: DefaultVariantProps) {
  const colors = COLOR_MAP[color];

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70 transition-colors hover:border-white/10">
      <CardContent className="p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-[var(--fg-muted)]">{title}</span>
          <div className={cn("p-2 rounded-lg", colors.bg)}>
            <Icon className={cn("w-4 h-4", colors.icon)} />
          </div>
        </div>

        {loading ? (
          <div className="h-8 bg-white/10 rounded animate-pulse w-20" />
        ) : (
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-[var(--fg-0)]">{value}</span>
            {trend && (
              <span className={cn("text-sm", trend.direction === "up" ? "text-green-400" : "text-red-400")}>
                {trend.direction === "up" ? "↑" : "↓"} {trend.value}%
              </span>
            )}
          </div>
        )}

        {subtitle && <p className="text-xs text-[var(--fg-subtle)] mt-1">{subtitle}</p>}
      </CardContent>
    </Card>
  );
}

// Dashboard variant (Creator experiments/approvals/feedback pages)
function DashboardStatCard({
  title,
  value,
  helper,
  icon: Icon,
  tone = "neutral",
  badge = "BETA",
  loading = false,
}: DashboardVariantProps) {
  const toneStyles = TONE_MAP[tone];

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70">
      <CardContent className="pt-6">
        {loading ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-white/10 animate-pulse" />
              <div className="space-y-2">
                <div className="h-3 w-16 bg-white/10 rounded animate-pulse" />
                <div className="h-5 w-12 bg-white/10 rounded animate-pulse" />
              </div>
            </div>
            <div className="h-3 w-24 bg-white/5 rounded animate-pulse" />
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center", toneStyles.bg)}>
                  <Icon className={cn("h-5 w-5", toneStyles.icon)} />
                </div>
                <div>
                  <p className="text-xs text-[var(--fg-muted)]">{title}</p>
                  <p className="text-xl font-semibold text-[var(--fg-0)]">{value}</p>
                </div>
              </div>
              {badge && (
                <Badge variant="outline" className="text-xs">
                  {badge}
                </Badge>
              )}
            </div>
            <p className="mt-3 text-xs text-[var(--fg-subtle)]">{helper}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// Stripe variant (Creator Hub page - with colored top stripe)
function StripeStatCard({
  label,
  value,
  helper,
  icon: Icon,
  tone = "neutral",
  badge = "BETA",
  loading = false,
}: StripeVariantProps) {
  const toneStyles = TONE_MAP[tone];

  return (
    <Card className="border border-white/5 bg-[var(--surface-1)]/70 overflow-hidden">
      <div className={cn("h-1 w-full", toneStyles.stripe)} />
      <CardContent className="pt-5">
        {loading ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-white/10 animate-pulse" />
              <div className="space-y-2">
                <div className="h-3 w-16 bg-white/10 rounded animate-pulse" />
                <div className="h-5 w-12 bg-white/10 rounded animate-pulse" />
              </div>
            </div>
            <div className="h-3 w-24 bg-white/5 rounded animate-pulse" />
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center", toneStyles.bg)}>
                  <Icon className={cn("h-5 w-5", toneStyles.icon)} />
                </div>
                <div>
                  <p className="text-xs text-[var(--fg-muted)]">{label}</p>
                  <p className="text-xl font-semibold text-[var(--fg-0)]">{value}</p>
                </div>
              </div>
              {badge && (
                <Badge variant="outline" className="text-xs">
                  {badge}
                </Badge>
              )}
            </div>
            <p className="mt-3 text-xs text-[var(--fg-subtle)]">{helper}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// Lusion variant (HumanCloud page - with glow effect)
function LusionStatCard({
  label,
  value,
  icon: Icon,
  color = "violet",
  loading = false,
}: LusionVariantProps) {
  const colors = COLOR_MAP[color];

  return (
    <div className="card-glass p-5 relative overflow-hidden">
      {/* Subtle glow */}
      <div className={cn("absolute -right-8 -top-8 h-32 w-32 rounded-full opacity-10 blur-[50px]", colors.glow)} />

      <div className="relative flex items-center justify-between">
        {loading ? (
          <>
            <div className="space-y-2">
              <div className="h-8 w-16 bg-white/10 rounded animate-pulse" />
              <div className="h-4 w-20 bg-white/5 rounded animate-pulse" />
            </div>
            <div className="h-11 w-11 bg-white/5 rounded-xl animate-pulse" />
          </>
        ) : (
          <>
            <div>
              <div className="text-3xl font-bold text-white mb-1">
                {typeof value === "number" ? value.toLocaleString() : value}
              </div>
              <div className="text-sm text-[var(--fg-muted)]">{label}</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10">
              <Icon className={cn("w-5 h-5", colors.icon)} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Main component with variant dispatch
export function StatCard(props: StatCardProps) {
  const variant = props.variant ?? "default";

  switch (variant) {
    case "dashboard":
      return <DashboardStatCard {...(props as DashboardVariantProps)} />;
    case "stripe":
      return <StripeStatCard {...(props as StripeVariantProps)} />;
    case "lusion":
      return <LusionStatCard {...(props as LusionVariantProps)} />;
    default:
      return <DefaultStatCard {...(props as DefaultVariantProps)} />;
  }
}

export default StatCard;
