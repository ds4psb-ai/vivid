"use client";

/**
 * Academy Admin Page (Integrated)
 *
 * 통합 수강생 관리 페이지:
 * - 수강 신청 (CrebitApplication)
 * - 접근 요청 (AccessRequest)
 * - 빠른 활성화
 */

import { useState, useCallback } from "react";
import {
    GraduationCap,
    RefreshCw,
    Users,
    Clock,
    UserCheck,
    Link2Off,
} from "lucide-react";

import AppShell from "@/components/AppShell";
import { StatCard } from "@/components/shared";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

import { ApplicationsTab } from "./components/ApplicationsTab";
import { AccessRequestsTab } from "./components/AccessRequestsTab";
import { QuickActivateTab } from "./components/QuickActivateTab";

// =============================================================================
// Main Page
// =============================================================================

export default function AdminAcademyPage() {
    const [activeTab, setActiveTab] = useState("applications");
    const [refreshKey, setRefreshKey] = useState(0);

    // Stats from child components
    const [stats, setStats] = useState({
        paidStudents: 0,
        pendingRequests: 0,
        unlinkedAccounts: 0,
        totalActive: 0,
    });

    const handleRefresh = useCallback(() => {
        setRefreshKey((k) => k + 1);
    }, []);

    const handleApplicationsData = useCallback((data: { paid: number; unlinked: number; total: number }) => {
        setStats((s) => ({
            ...s,
            paidStudents: data.paid,
            unlinkedAccounts: data.unlinked,
            totalActive: data.paid,
        }));
    }, []);

    const handleAccessRequestsData = useCallback((data: { pending: number; total: number }) => {
        setStats((s) => ({
            ...s,
            pendingRequests: data.pending,
        }));
    }, []);

    return (
        <AppShell>
            <div className="min-h-screen px-4 py-6 sm:px-6 sm:py-8">
                <div className="mx-auto max-w-6xl">
                    {/* Header */}
                    <div className="mb-6 sm:mb-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-xl font-bold text-[var(--fg-0)] sm:text-2xl flex items-center gap-2">
                                    <GraduationCap className="w-6 h-6 text-purple-400" />
                                    Academy 수강생 관리
                                </h1>
                                <p className="mt-1 text-sm text-[var(--fg-muted)] sm:text-base">
                                    수강 신청, 접근 요청, 빠른 활성화를 한 곳에서 관리
                                </p>
                            </div>
                            <button
                                onClick={handleRefresh}
                                className="p-2 text-[var(--fg-muted)] hover:text-[var(--fg-0)] hover:bg-white/5 rounded-lg transition-colors"
                                title="새로고침"
                            >
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Stats Overview */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                        <StatCard
                            title="결제완료 수강생"
                            value={stats.paidStudents}
                            icon={Users}
                            color="green"
                            subtitle="명"
                        />
                        <StatCard
                            title="대기 중 요청"
                            value={stats.pendingRequests}
                            icon={Clock}
                            color="yellow"
                            subtitle="건"
                        />
                        <StatCard
                            title="미연결 계정"
                            value={stats.unlinkedAccounts}
                            icon={Link2Off}
                            color="orange"
                            subtitle="건"
                        />
                        <StatCard
                            title="전체 활성"
                            value={stats.totalActive}
                            icon={UserCheck}
                            color="purple"
                            subtitle="명"
                        />
                    </div>

                    {/* Tabs */}
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                        <TabsList className="w-full justify-start bg-[var(--surface-1)]/70 border border-white/5 rounded-xl p-1 mb-6">
                            <TabsTrigger
                                value="applications"
                                className="flex-1 sm:flex-none data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300 rounded-lg px-4 py-2"
                            >
                                <span className="flex items-center gap-2">
                                    <Users className="w-4 h-4" />
                                    <span className="hidden sm:inline">수강 신청</span>
                                    <span className="sm:hidden">신청</span>
                                </span>
                            </TabsTrigger>
                            <TabsTrigger
                                value="access-requests"
                                className="flex-1 sm:flex-none data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300 rounded-lg px-4 py-2"
                            >
                                <span className="flex items-center gap-2">
                                    <UserCheck className="w-4 h-4" />
                                    <span className="hidden sm:inline">접근 요청</span>
                                    <span className="sm:hidden">요청</span>
                                    {stats.pendingRequests > 0 && (
                                        <span className="px-1.5 py-0.5 text-xs bg-amber-500/20 text-amber-300 rounded-full">
                                            {stats.pendingRequests}
                                        </span>
                                    )}
                                </span>
                            </TabsTrigger>
                            <TabsTrigger
                                value="quick-activate"
                                className="flex-1 sm:flex-none data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300 rounded-lg px-4 py-2"
                            >
                                <span className="flex items-center gap-2">
                                    <span className="material-symbols-outlined text-lg">bolt</span>
                                    <span className="hidden sm:inline">빠른 활성화</span>
                                    <span className="sm:hidden">활성화</span>
                                </span>
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="applications" className="mt-0">
                            <ApplicationsTab
                                key={`applications-${refreshKey}`}
                                onDataUpdate={handleApplicationsData}
                            />
                        </TabsContent>

                        <TabsContent value="access-requests" className="mt-0">
                            <AccessRequestsTab
                                key={`access-requests-${refreshKey}`}
                                onDataUpdate={handleAccessRequestsData}
                            />
                        </TabsContent>

                        <TabsContent value="quick-activate" className="mt-0">
                            <QuickActivateTab
                                key={`quick-activate-${refreshKey}`}
                                onActivated={handleRefresh}
                            />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </AppShell>
    );
}
