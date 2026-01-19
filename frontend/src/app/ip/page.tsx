import type { Metadata } from "next";
import { Suspense } from "react";
import IPCatalogClient from "./_components/IPCatalogClient";

export const metadata: Metadata = {
  title: "IP Gallery | Crebit",
  description: "Browse IP catalog and create AI fan-fiction videos",
};

function IPCatalogFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-0)]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
    </div>
  );
}

export default function IPCatalogPage() {
  return (
    <Suspense fallback={<IPCatalogFallback />}>
      <IPCatalogClient />
    </Suspense>
  );
}
