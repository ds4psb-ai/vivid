"use client";

import AppShell from "@/components/AppShell";
import AbyssMirrorPanel from "@/components/dimension/AbyssMirrorPanel";

export default function AbyssPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <AbyssMirrorPanel />
            </div>
        </AppShell>
    );
}
