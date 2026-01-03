"use client";

import AppShell from "@/components/AppShell";
import StoryboardPanel from "@/components/teaching/StoryboardPanel";
import { useLanguage } from "@/contexts/LanguageContext";

export default function TeachingStoryboardPage() {
    const { t } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <StoryboardPanel />
            </div>
        </AppShell>
    );
}
