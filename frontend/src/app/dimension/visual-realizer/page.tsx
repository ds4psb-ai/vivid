"use client";

import AppShell from "@/components/AppShell";
import VisualRealizerPanel from "@/components/dimension/VisualRealizerPanel";

export default function VisualRealizerPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <VisualRealizerPanel />
            </div>
        </AppShell>
    );
}
