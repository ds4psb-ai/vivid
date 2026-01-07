"use client";

import AppShell from "@/components/AppShell";
import QualityCheckerPanel from "@/components/dimension/QualityCheckerPanel";

export default function QualityCheckPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <QualityCheckerPanel />
            </div>
        </AppShell>
    );
}
