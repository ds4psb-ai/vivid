"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

type GlowColor = "red" | "violet" | "emerald" | "amber" | "cyan";

interface GlowButtonProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: GlowColor;
  size?: "sm" | "md" | "lg";
  variant?: "solid" | "outline";
  disabled?: boolean;
  onClick?: () => void;
  type?: "button" | "submit" | "reset";
}

const glowColorMap: Record<GlowColor, { gradient: string; glow: string }> = {
  red: {
    gradient: "from-red-600 to-red-500 hover:from-red-500 hover:to-rose-500",
    glow: "from-red-400/50 to-rose-400/50",
  },
  violet: {
    gradient: "from-violet-600 to-violet-500 hover:from-violet-500 hover:to-fuchsia-500",
    glow: "from-violet-400/50 to-fuchsia-400/50",
  },
  emerald: {
    gradient: "from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-teal-500",
    glow: "from-emerald-400/50 to-teal-400/50",
  },
  amber: {
    gradient: "from-amber-600 to-amber-500 hover:from-amber-500 hover:to-orange-500",
    glow: "from-amber-400/50 to-orange-400/50",
  },
  cyan: {
    gradient: "from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-blue-500",
    glow: "from-cyan-400/50 to-blue-400/50",
  },
};

const sizeMap = {
  sm: "px-4 py-2 text-sm",
  md: "px-6 py-3 text-base",
  lg: "px-8 py-4 text-lg",
};

export function GlowButton({
  children,
  className,
  glowColor = "red",
  size = "md",
  variant = "solid",
  disabled,
  onClick,
  type = "button",
}: GlowButtonProps) {
  const colors = glowColorMap[glowColor];

  return (
    <motion.button
      type={type}
      className={cn(
        "relative rounded-full font-semibold text-white overflow-hidden group",
        "transition-all duration-300 ease-out",
        variant === "solid" && `bg-gradient-to-r ${colors.gradient}`,
        variant === "outline" && "border-2 border-white/20 hover:border-white/40 bg-transparent",
        sizeMap[size],
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      disabled={disabled}
      onClick={onClick}
    >
      {/* Glow effect layer */}
      {variant === "solid" && (
        <div
          className={cn(
            "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300",
            `bg-gradient-to-r ${colors.glow} blur-xl`
          )}
        />
      )}

      {/* Content */}
      <span className="relative z-10 flex items-center justify-center gap-2">
        {children}
      </span>

      {/* Shine sweep effect */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out" />
      </div>
    </motion.button>
  );
}
