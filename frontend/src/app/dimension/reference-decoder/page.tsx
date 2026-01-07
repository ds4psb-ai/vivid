"use client";

import AppShell from "@/components/AppShell";
import ReferenceCapturePanel from "@/components/dimension/ReferenceCapturePanel";

export default function ReferenceDecoderPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <ReferenceCapturePanel />
            </div>
        </AppShell>
    );
}
