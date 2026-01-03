"use client";

import AppShell from "@/components/AppShell";
import ImageToolPanel from "@/components/teaching/ImageToolPanel";
import { useLanguage } from "@/contexts/LanguageContext";

export default function TeachingImageToolPage() {
    const { t } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <ImageToolPanel />
            </div>
        </AppShell>
    );
}
