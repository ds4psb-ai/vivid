/**
 * Dimension Layout - Server Component
 * ====================================
 *
 * 2026 RSC Best Practice:
 * - Layout is a Server Component (no "use client")
 * - Metadata generated on server
 * - Client providers wrapped in separate component
 *
 * Benefits:
 * - Smaller JavaScript bundle
 * - Faster initial page load (SSR)
 * - Static metadata at build time
 */

import type { Metadata } from "next";
import DimensionProviders from "./providers";

export const metadata: Metadata = {
  title: "Dimension Studio | Crebit",
  description:
    "Creative AI tools for video production - from concept to final output",
  openGraph: {
    title: "Dimension Studio | Crebit",
    description:
      "Creative AI tools for video production - from concept to final output",
    type: "website",
  },
};

interface DimensionLayoutProps {
  children: React.ReactNode;
}

export default function DimensionLayout({ children }: DimensionLayoutProps) {
  return <DimensionProviders>{children}</DimensionProviders>;
}
