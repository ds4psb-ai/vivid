"use client";

/**
 * Dimension Providers - Client Component Boundary
 * ================================================
 *
 * This client component wraps the context providers that
 * require client-side state management. The parent layout
 * can remain a Server Component.
 *
 * 2026 RSC Pattern: "Provider Islands" for client-side state.
 */

import { TeachingSettingsProvider } from "@/contexts/DimensionSettingsContext";
import { CreditProvider } from "@/contexts/CreditContext";
import { DimensionChainProvider } from "@/contexts/DimensionChainContext";

interface DimensionProvidersProps {
  children: React.ReactNode;
}

export default function DimensionProviders({
  children,
}: DimensionProvidersProps) {
  return (
    <CreditProvider>
      <TeachingSettingsProvider>
        <DimensionChainProvider>{children}</DimensionChainProvider>
      </TeachingSettingsProvider>
    </CreditProvider>
  );
}
