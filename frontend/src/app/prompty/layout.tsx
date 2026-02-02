"use client";

import { Suspense } from "react";
import { PromptyNavbar } from "@/components/prompty/PromptyNavbar";

export default function PromptyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <PromptyNavbar />
      <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
        {children}
      </Suspense>
    </div>
  );
}
