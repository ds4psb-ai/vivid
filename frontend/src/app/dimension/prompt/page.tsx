"use client";

import AppShell from "@/components/AppShell";
import PromptGeneratorPanel from "@/components/dimension/PromptGeneratorPanel";

export default function TeachingPromptPage() {
    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <PromptGeneratorPanel />
            </div>
        </AppShell>
    );
}
