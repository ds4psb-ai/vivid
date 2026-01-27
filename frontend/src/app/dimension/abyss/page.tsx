"use client";

import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import AppShell from "@/components/AppShell";
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";

function AbyssLoading() {
    return (
        <div className="h-screen flex items-center justify-center bg-black">
            <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-8 h-8 animate-spin text-white/60" />
                <p className="text-sm text-white/40">Loading Abyss Mirror...</p>
            </div>
        </div>
    );
}

export default function AbyssPage() {
    return (
        <AppShell showTopBar={false}>
            <Suspense fallback={<AbyssLoading />}>
                <div className="h-screen">
                    <AbyssMirrorPanel />
                </div>
            </Suspense>
        </AppShell>
    );
}
