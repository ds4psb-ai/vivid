"use client";

import AppShell from "@/components/AppShell";
import CreativeEditorPanel from "@/components/dimension/CreativeEditorPanel";

export default function QualityCheckPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <CreativeEditorPanel />
            </div>
        </AppShell>
    );
}
