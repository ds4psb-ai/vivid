"use client";

import AppShell from "@/components/AppShell";
import ImageToolPanel from "@/components/dimension/ImageToolPanel";

export default function VisualRealizerPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <ImageToolPanel />
            </div>
        </AppShell>
    );
}
