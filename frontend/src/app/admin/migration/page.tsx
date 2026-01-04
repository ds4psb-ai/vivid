/**
 * Admin Migration Page
 * 
 * 내부 직원 전용 앱 마이그레이션 도구
 */
"use client";

import { AppMigrationConsole } from "@/components/admin/AppMigrationConsole";
import AppShell from "@/components/AppShell";

export default function AdminMigrationPage() {
    const handleDeploy = async (manifest: { name: string; version: string }, appId: string) => {
        // In production: call backend API
        console.log(`Deployed: ${manifest.name} v${manifest.version} as ${appId}`);
    };

    return (
        <AppShell>
            <AppMigrationConsole onDeploy={handleDeploy} />
        </AppShell>
    );
}
