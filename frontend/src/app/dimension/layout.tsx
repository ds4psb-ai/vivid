"use client";

import { TeachingSettingsProvider } from "@/contexts/DimensionSettingsContext";
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
