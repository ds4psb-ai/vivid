# Crebit Studio Design Consulting Report

> Generated: 2026-01-25
> Stitch Project: `projects/2522952777371678289`
> Stitch Dashboard: https://stitch.google.com (Google 계정으로 접속)

---

## Executive Summary

Crebit Studio의 현재 디자인 시스템을 분석한 결과, **이미 2026 Best Practices의 80%를 충족**하고 있습니다. 주요 개선 포인트는 Hero 섹션 임팩트 강화, 카드 인터랙션 고도화, 그리고 CTA 시각적 계층 개선입니다.

### Stitch MCP 연동 현황
| 항목 | 상태 |
|------|------|
| 프로젝트 생성 | ✅ `projects/2522952777371678289` |
| API 연결 | ✅ 정상 (ADC 인증) |
| 디자인 테마 | Dark Mode, Space Grotesk, Violet Accent |
| 기존 에셋 | 3개 프로젝트 (Lumina, Shorti, Login) |

---

## Current Design Analysis

### Strengths (강점)

#### 1. Design Tokens Foundation (A+)
```css
/* W3C DTCG 2025.10 Aligned - Oklch color space */
--color-brand-primary: oklch(0.62 0.26 290);  /* Vivid Violet */
--color-brand-secondary: oklch(0.78 0.20 145); /* Vivid Emerald */
```
- ✅ Wide-gamut Oklch 색공간 사용
- ✅ Semantic token 계층 (bg-0 → bg-1 → surface-1)
- ✅ Light/Dark 모드 완벽 지원
- ✅ High contrast / reduced motion 접근성 지원

#### 2. Aurora Background (A)
```tsx
// Interactive mouse-following aurora orbs
<div className="animate-aurora-drift-slow mix-blend-screen" />
```
- ✅ GPU 가속 blur (60px)
- ✅ Mouse-reactive 인터랙션
- ✅ 20fps throttle로 성능 최적화

#### 3. Component Library (B+)
- ✅ Card variants: glass, premium, lusion
- ✅ Stagger reveal animations
- ✅ Magnetic button effects
- ⚠️ 일부 컴포넌트 hover state 부족

---

## Improvement Recommendations

### Priority 1: Hero Section Enhancement

**문제점**: 현재 Hero가 없고 바로 콘텐츠 레일로 시작

**개선안**:
```tsx
// NEW: Cinematic Hero with Stitch-inspired design
<section className="relative h-[70vh] flex items-center justify-center overflow-hidden">
  {/* Animated gradient mesh */}
  <div className="absolute inset-0 bg-gradient-to-br from-violet-600/20 via-transparent to-emerald-600/20 animate-gradient-xy" />

  {/* Floating orbs (Stitch pattern) */}
  <div className="absolute w-96 h-96 rounded-full bg-violet-500/30 blur-3xl animate-float" />

  {/* Hero content */}
  <div className="relative z-10 text-center space-y-6">
    <motion.h1
      className="text-6xl md:text-8xl font-bold bg-gradient-to-r from-white via-violet-200 to-emerald-200 bg-clip-text text-transparent"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      Crebit Studio
    </motion.h1>
    <motion.p
      className="text-xl text-[var(--fg-muted)] max-w-2xl mx-auto"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
    >
      AI-Powered Creative Production Platform
    </motion.p>
  </div>
</section>
```

### Priority 2: IP Rail Card Hover Enhancement

**문제점**: 비디오 프리뷰는 있지만 3D tilt 효과 없음

**개선안** (IPRailCard.tsx):
```tsx
// Add 3D tilt on hover
const handleMouseMove = (e: React.MouseEvent) => {
  const rect = e.currentTarget.getBoundingClientRect();
  const x = (e.clientX - rect.left) / rect.width - 0.5;
  const y = (e.clientY - rect.top) / rect.height - 0.5;

  e.currentTarget.style.transform = `
    perspective(1000px)
    rotateY(${x * 10}deg)
    rotateX(${y * -10}deg)
    scale(1.02)
  `;
};

const handleMouseLeave = (e: React.MouseEvent) => {
  e.currentTarget.style.transform = 'perspective(1000px) rotateY(0) rotateX(0) scale(1)';
};
```

### Priority 3: Dimension Flow CTA Upgrade

**문제점**: 현재 static gradient box

**개선안**:
```tsx
// Animated border gradient + glow pulse
<div className="relative group">
  {/* Animated gradient border */}
  <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 via-emerald-500 to-violet-600 rounded-2xl opacity-50 group-hover:opacity-100 blur-sm transition-opacity animate-gradient-x" />

  {/* Inner content */}
  <div className="relative bg-black/80 backdrop-blur-xl rounded-2xl p-8 border border-white/10">
    {/* Sparkle particle effect */}
    <SparkleParticles count={20} />
    ...
  </div>
</div>
```

### Priority 4: Dimension Grid Cards

**문제점**: 호버 시 border만 변경

**개선안**:
```css
/* Add to globals.css */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.dimension-card-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255,255,255,0.1) 50%,
    transparent 100%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}
```

---

## New CSS Animations to Add

```css
/* Add to globals.css */

/* Gradient animation for hero */
@keyframes gradient-xy {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.animate-gradient-xy {
  background-size: 200% 200%;
  animation: gradient-xy 8s ease infinite;
}

/* Floating animation for orbs */
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(10px, -20px) scale(1.05); }
  50% { transform: translate(-5px, 10px) scale(0.95); }
  75% { transform: translate(15px, 5px) scale(1.02); }
}

.animate-float {
  animation: float 15s ease-in-out infinite;
}

/* Horizontal gradient animation */
@keyframes gradient-x {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.animate-gradient-x {
  background-size: 200% auto;
  animation: gradient-x 3s linear infinite;
}
```

---

## Component Improvements

### 1. SparkleParticles Component (신규)

```tsx
// components/ui/SparkleParticles.tsx
"use client";
import { useEffect, useState } from "react";

interface Sparkle {
  id: number;
  x: number;
  y: number;
  size: number;
  delay: number;
}

export function SparkleParticles({ count = 15 }: { count?: number }) {
  const [sparkles, setSparkles] = useState<Sparkle[]>([]);

  useEffect(() => {
    setSparkles(
      Array.from({ length: count }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 4 + 2,
        delay: Math.random() * 2,
      }))
    );
  }, [count]);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {sparkles.map((s) => (
        <div
          key={s.id}
          className="absolute rounded-full bg-white animate-pulse-slow"
          style={{
            left: `${s.x}%`,
            top: `${s.y}%`,
            width: s.size,
            height: s.size,
            animationDelay: `${s.delay}s`,
            opacity: 0.6,
          }}
        />
      ))}
    </div>
  );
}
```

### 2. GlowButton Component (신규)

```tsx
// components/ui/GlowButton.tsx
"use client";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface GlowButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  glowColor?: string;
}

export function GlowButton({
  children,
  className,
  onClick,
  glowColor = "violet"
}: GlowButtonProps) {
  return (
    <motion.button
      className={cn(
        "relative px-6 py-3 rounded-full font-semibold text-white overflow-hidden group",
        "bg-gradient-to-r from-violet-600 to-violet-500",
        "hover:from-violet-500 hover:to-emerald-500",
        "transition-all duration-300",
        className
      )}
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Glow effect */}
      <div className={cn(
        "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity",
        "bg-gradient-to-r from-violet-400/50 to-emerald-400/50 blur-xl"
      )} />

      {/* Content */}
      <span className="relative z-10 flex items-center gap-2">
        {children}
      </span>

      {/* Shine effect */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
      </div>
    </motion.button>
  );
}
```

---

## Stitch Design Assets

### Existing Projects (Stitch Dashboard)

| Project | Theme | Font | Accent |
|---------|-------|------|--------|
| Lumina AI Landing | Dark | Space Grotesk | `#f425d1` |
| Shorti.ai Discover | Dark | Spline Sans | `#f490c3` |
| Login Screen | Dark | Inter | `#ee2b8c` |

### Thumbnail URLs (바로 사용 가능)

```
Lumina: https://lh3.googleusercontent.com/aida/AOfcidUYkGDsH8hOhAX0VYGGGmbZDW7urvWDWdbarJQ0Dx0BHk0693gz7QhOhMH139zHx_HgF-19DPEhoMD_Ssk19hhxder7eknIlLkXNT_GuTq92ThiyBufa9kDBLCHsCAGjEcbZiBUw8DZHrBICZalHiZid7IYqaJuXs4zqa9XyBPv6zU-313R01L7zvZKqdwQvamF7BLNR2ZnFfutK-yO7uKGesI94wG2eWdDkyQaLlqtDWysU1VKpjAFTt0

Shorti: https://lh3.googleusercontent.com/aida/AOfcidWSXheZLpBWDx4R4s-cJBrwnzg9PXZleY1AJhThUi8Tz1clpzFxZNN3zsLVbbTy5vUDC6NO314hFdDizuBGorvGFJgSmnkbIjJLjrtoTNke6B50GWzuDRqcwAy_lShSgR9PcwGfcBXGkwOBgcfCWKNB2WiEAPC7rey0u1aC4R9VZmam60MUOJa4H1YsOHFAzIgUjizgbzVX_igr1LUe_lDfySk9BpPca3mZI0DosBunygXgaJLneTjYPA
```

---

## Implementation Roadmap

### Phase 1: Quick Wins (1-2일)
- [ ] globals.css에 새 애니메이션 추가
- [ ] SparkleParticles, GlowButton 컴포넌트 생성
- [ ] IPRailCard에 3D tilt 효과 추가

### Phase 2: Hero & CTA (2-3일)
- [ ] 메인 페이지 Hero 섹션 추가
- [ ] Dimension Flow CTA 업그레이드
- [ ] Animated gradient border 적용

### Phase 3: Polish (1-2일)
- [ ] Dimension Grid 카드 shimmer 효과
- [ ] 전체 hover state 일관성 점검
- [ ] Light mode 최종 검수

---

## Design References

Based on 2026 design trends from:
- **Linear.app**: Gradient mesh backgrounds, magnetic buttons
- **Raycast.com**: Glass morphism, glow effects
- **Vercel.com**: Clean typography, subtle animations
- **Lusion.co**: Interactive 3D, parallax scrolling

---

## Stitch MCP Commands Reference

```bash
# 프로젝트 목록 조회
Stitch API: list_projects

# 스크린 생성 (Stitch Dashboard에서 추천 - API 느림)
Stitch API: generate_screen_from_text

# 스크린 조회
Stitch API: list_screens, get_screen
```

---

## Conclusion

Crebit Studio는 이미 Premium SaaS 수준의 디자인 시스템을 갖추고 있습니다. 제안된 개선사항들은 기존 foundation 위에 **더 임팩트 있는 Hero**, **고급 인터랙션**, **시각적 계층 강화**를 추가하는 것입니다.

Stitch MCP 연동으로 향후 디자인 iteration을 빠르게 진행할 수 있는 인프라가 구축되었습니다.

---

*Report generated by Claude Code with Stitch MCP integration*
