"use client";

import AppShell from "@/components/AppShell";
import ReferenceCapturePanel from "@/components/teaching/ReferenceCapturePanel";
import { useLanguage } from "@/contexts/LanguageContext";

export default function TeachingShotCatchPage() {
    const { t } = useLanguage();

    return (
        <AppShell showTopBar={false}>
            <div className="h-screen">
                <ReferenceCapturePanel />
            </div>
        </AppShell>
    );
}
