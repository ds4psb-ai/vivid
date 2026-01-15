/**
 * Dimension Hub Page - Server Component
 * ======================================
 *
 * 2026 RSC Best Practice:
 * - Page component is a Server Component
 * - Static metadata export
 * - Dynamic content in client island
 *
 * Benefits:
 * - SEO-friendly metadata at build time
 * - Reduced client-side JavaScript
 * - Faster Time to First Byte (TTFB)
 */

import type { Metadata } from "next";
import DimensionHubClient from "./_components/DimensionHubClient";

export const metadata: Metadata = {
  title: "Dimension Studio | Crebit",
  description:
    "AI 비디오 제작 도구 - 기획부터 완성까지 10개의 전문 도구로 창작하세요",
  keywords: [
    "AI video",
    "creative tools",
    "video production",
    "storyboard",
    "prompt engineering",
  ],
  openGraph: {
    title: "Dimension Studio | Crebit",
    description:
      "AI 비디오 제작 도구 - 기획부터 완성까지 10개의 전문 도구로 창작하세요",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Dimension Studio | Crebit",
    description:
      "AI 비디오 제작 도구 - 기획부터 완성까지 10개의 전문 도구로 창작하세요",
  },
};

export default function DimensionHubPage() {
  // This is a Server Component - no "use client" directive
  // All interactive logic is in DimensionHubClient
  return <DimensionHubClient />;
}
