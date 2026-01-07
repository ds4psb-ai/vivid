"use client";

import AppShell from "@/components/AppShell";
import StoryArchitectPanel from "@/components/dimension/StoryArchitectPanel";

export default function StoryArchitectPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <StoryArchitectPanel />
            </div>
        </AppShell>
    );
}
