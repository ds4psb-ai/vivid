"use client";

import AppShell from "@/components/AppShell";
import AbyssInterpreterPanel from "@/components/dimension/AbyssInterpreterPanel";

export default function AbyssPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <AbyssInterpreterPanel />
            </div>
        </AppShell>
    );
}
