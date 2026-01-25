"use client";

import { useMemo } from "react";

interface Sparkle {
  id: number;
  x: number;
  y: number;
  size: number;
  delay: number;
  duration: number;
}

interface SparkleParticlesProps {
  count?: number;
  className?: string;
}

export function SparkleParticles({ count = 15, className = "" }: SparkleParticlesProps) {
  const sparkles = useMemo<Sparkle[]>(() => {
    const seededRandom = (seed: number) => {
      let t = seed + 0x6D2B79F5;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };

    return Array.from({ length: count }, (_, i) => {
      const base = (count + 1) * (i + 1);
      const r1 = seededRandom(base);
      const r2 = seededRandom(base + 1);
      const r3 = seededRandom(base + 2);
      const r4 = seededRandom(base + 3);
      const r5 = seededRandom(base + 4);

      return {
        id: i,
        x: r1 * 100,
        y: r2 * 100,
        size: r3 * 3 + 1,
        delay: r4 * 3,
        duration: r5 * 2 + 2,
      };
    });
  }, [count]);

  return (
    <div className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {sparkles.map((s) => (
        <div
          key={s.id}
          className="absolute rounded-full bg-white animate-sparkle"
          style={{
            left: `${s.x}%`,
            top: `${s.y}%`,
            width: s.size,
            height: s.size,
            animationDelay: `${s.delay}s`,
            animationDuration: `${s.duration}s`,
          }}
        />
      ))}
    </div>
  );
}
