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
 *
 * Note: DimensionChainProvider is now at root layout for cross-MegaApp sharing.
 */

import { TeachingSettingsProvider } from "@/contexts/DimensionSettingsContext";
import AppShell from "@/components/AppShell";

interface DimensionProvidersProps {
  children: React.ReactNode;
}

export default function DimensionProviders({
  children,
}: DimensionProvidersProps) {
  return (
    <AppShell navVariant="academy" showChokki={false}>
      <TeachingSettingsProvider>
        <div className="h-screen">{children}</div>
      </TeachingSettingsProvider>
    </AppShell>
  );
}
