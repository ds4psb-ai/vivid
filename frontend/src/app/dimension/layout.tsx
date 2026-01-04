"use client";

import { TeachingSettingsProvider } from "@/contexts/TeachingSettingsContext";
import { CreditProvider } from "@/contexts/CreditContext";

export default function TeachingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <CreditProvider>
            <TeachingSettingsProvider>
                {children}
            </TeachingSettingsProvider>
        </CreditProvider>
    );
}
