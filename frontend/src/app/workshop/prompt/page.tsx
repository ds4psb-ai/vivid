"use client";

import AppShell from "@/components/AppShell";
import PromptGeneratorPanel from "@/components/teaching/PromptGeneratorPanel";
import { useLanguage } from "@/contexts/LanguageContext";

export default function TeachingPromptPage() {
    const { t } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            <div className="h-screen bg-[#131313]">
                <PromptGeneratorPanel />
            </div>
        </AppShell>
    );
}
