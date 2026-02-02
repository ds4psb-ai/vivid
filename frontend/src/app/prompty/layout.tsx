"use client";

import { Suspense } from "react";

export default function PromptyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
        {children}
      </Suspense>
    </div>
  );
}
