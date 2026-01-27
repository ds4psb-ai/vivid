"use client";

import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";

function StoryArchitectLoading() {
    return (
        <div className="h-screen flex items-center justify-center bg-black">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-white/60" />
                <p className="text-sm text-white/40">Loading Story Architect...</p>
            </div>
        </div>
    );
}

export default function StoryArchitectPage() {
    return (
        <AppShell showTopBar={false}>
            <Suspense fallback={<StoryArchitectLoading />}>
                <div className="h-screen">
                    <StoryArchitectPanel />
                </div>
            </Suspense>
        </AppShell>
    );
}
