"use client";

import AppShell from "@/components/AppShell";
import VeoVideoPanel from "@/components/dimension/VeoVideoPanel";

export default function VideoMakerPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <VeoVideoPanel />
            </div>
        </AppShell>
    );
}
