/**
 * IP Detail Loading Fallback
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * Displayed while the IP detail page is loading or generating on the server.
 * Used as the Suspense fallback in the page component.
 */

export function IPDetailFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-0)]">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
        <p className="text-sm text-[var(--fg-muted)]">Loading IP details...</p>
      </div>
    </div>
  );
}
