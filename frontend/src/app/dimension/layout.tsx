"use client";

import { TeachingSettingsProvider } from "@/contexts/DimensionSettingsContext";
import { CreditProvider } from "@/contexts/CreditContext";
import { DimensionChainProvider } from "@/contexts/DimensionChainContext";

export default function TeachingLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <CreditProvider>
            <TeachingSettingsProvider>
                <DimensionChainProvider>
                    {children}
                </DimensionChainProvider>
            </TeachingSettingsProvider>
        </CreditProvider>
    );
}
