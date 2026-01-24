"use client";

import { useEffect, useState, useMemo } from "react";

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
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const sparkles = useMemo<Sparkle[]>(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      delay: Math.random() * 3,
      duration: Math.random() * 2 + 2,
    }));
  }, [count]);

  if (!mounted) return null;

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
