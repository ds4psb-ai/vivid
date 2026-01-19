"use client";

import AppShell from "@/components/AppShell";
import StoryboardPanel from "@/components/dimension/StoryboardPanel";

export default function TeachingStoryboardPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <StoryboardPanel />
            </div>
        </AppShell>
    );
}
