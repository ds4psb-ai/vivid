"use client";

import AppShell from "@/components/AppShell";
import AestheticDirectorPanel from "@/components/dimension/AestheticDirectorPanel";

export default function AestheticPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <AestheticDirectorPanel />
            </div>
        </AppShell>
    );
}
