"use client";

import AppShell from "@/components/AppShell";
import SoundCrafterPanel from "@/components/dimension/SoundCrafterPanel";

export default function SoundCrafterPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <SoundCrafterPanel />
            </div>
        </AppShell>
    );
}
