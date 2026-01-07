"use client";

import AppShell from "@/components/AppShell";
import QualityDirectorPanel from "@/components/dimension/QualityDirectorPanel";

export default function QualityCheckPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <QualityDirectorPanel />
            </div>
        </AppShell>
    );
}
