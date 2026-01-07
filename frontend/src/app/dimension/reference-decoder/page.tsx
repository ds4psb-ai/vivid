"use client";

import AppShell from "@/components/AppShell";
import ReferenceDecoderPanel from "@/components/dimension/ReferenceDecoderPanel";

export default function ReferenceDecoderPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <ReferenceDecoderPanel />
            </div>
        </AppShell>
    );
}
