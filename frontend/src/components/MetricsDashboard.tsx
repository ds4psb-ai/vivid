'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    TrendingUp, TrendingDown, Eye, Heart, MessageCircle,
    Share2, BarChart3, PieChart, Zap, Lightbulb,
    RefreshCw, Download, Calendar, Filter, ChevronDown,
    Award, Target, Flame, ArrowUpRight, ArrowDownRight
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export interface ContentMetrics {
    content_id: string;
    platform: string;
    hook_style?: string;
    hook_variant_id?: string;
    views: number;
    likes: number;
    comments: number;
    shares: number;
    watch_time_avg_sec: number;
    retention_rate: number;
    engagement_rate: number;
    viral_score: number;
    collected_at: string;
}

export interface ABTestVariantResult {
    variant_id: string;
    style: string;
    views: number;
    engagement_rate: number;
    viral_score: number;
    is_winner: boolean;
}

export interface ABTestResult {
    test_id: string;
    test_name: string;
    started_at: string;
    ended_at?: string;
    status: 'running' | 'completed' | 'cancelled';
    variants: ABTestVariantResult[];
    winner_variant_id?: string;
    confidence_level?: number;
}

export interface ViralInsight {
    insight_type: string;
    title: string;
    description: string;
    data: Record<string, any>;
    recommendation?: string;
}

export interface AggregateData {
    group_key: string;
    total_content: number;
    avg_views: number;
    avg_engagement_rate: number;
    avg_viral_score: number;
    total_views: number;
}

export interface MetricsDashboardProps {
    className?: string;
    onRefresh?: () => void;
}

// =============================================================================
// Mock Data (will be replaced with API calls)
// =============================================================================

const MOCK_AGGREGATES: AggregateData[] = [
    { group_key: 'shock', total_content: 24, avg_views: 45000, avg_engagement_rate: 8.5, avg_viral_score: 72, total_views: 1080000 },
    { group_key: 'curiosity', total_content: 18, avg_views: 38000, avg_engagement_rate: 7.2, avg_viral_score: 65, total_views: 684000 },
    { group_key: 'paradox', total_content: 15, avg_views: 52000, avg_engagement_rate: 9.1, avg_viral_score: 78, total_views: 780000 },
    { group_key: 'emotion', total_content: 12, avg_views: 32000, avg_engagement_rate: 11.5, avg_viral_score: 68, total_views: 384000 },
    { group_key: 'tease', total_content: 10, avg_views: 41000, avg_engagement_rate: 6.8, avg_viral_score: 62, total_views: 410000 },
];

const MOCK_INSIGHTS: ViralInsight[] = [
    {
        insight_type: 'top_performer',
        title: '역설형 훅 가장 높은 바이럴 점수',
        description: '지난 30일간 역설형(paradox) 훅이 평균 78점으로 가장 높은 바이럴 점수를 기록했습니다.',
        data: { style: 'paradox', score: 78, improvement: '+12%' },
        recommendation: '익숙함+낯섦 조합을 더 적극적으로 활용하세요.',
    },
    {
        insight_type: 'engagement_leader',
        title: '감정형 훅 최고 참여율',
        description: '감정형(emotion) 훅이 11.5%의 참여율로 전체 스타일 중 1위를 차지했습니다.',
        data: { style: 'emotion', rate: 11.5, benchmark: 7.2 },
        recommendation: '공감할 수 있는 감정적 시작점을 더 활용해보세요.',
    },
    {
        insight_type: 'growth_trend',
        title: '충격형 콘텐츠 수 증가',
        description: '이번 달 충격형 훅 사용이 지난달 대비 40% 증가했습니다.',
        data: { style: 'shock', growth: '+40%', count: 24 },
    },
];

const MOCK_AB_TESTS: ABTestResult[] = [
    {
        test_id: 'ab_001',
        test_name: '치킨집 사장 - 훅 스타일 테스트',
        started_at: '2024-12-25T10:00:00Z',
        ended_at: '2024-12-28T10:00:00Z',
        status: 'completed',
        variants: [
            { variant_id: 'shock_1', style: 'shock', views: 15000, engagement_rate: 8.2, viral_score: 71, is_winner: false },
            { variant_id: 'paradox_1', style: 'paradox', views: 18500, engagement_rate: 9.8, viral_score: 82, is_winner: true },
            { variant_id: 'tease_1', style: 'tease', views: 12000, engagement_rate: 7.1, viral_score: 58, is_winner: false },
        ],
        winner_variant_id: 'paradox_1',
        confidence_level: 95,
    },
    {
        test_id: 'ab_002',
        test_name: 'NBA 스타 광고 - 강도 테스트',
        started_at: '2024-12-28T14:00:00Z',
        status: 'running',
        variants: [
            { variant_id: 'shock_soft', style: 'shock', views: 8200, engagement_rate: 6.5, viral_score: 55, is_winner: false },
            { variant_id: 'shock_explosive', style: 'shock', views: 9800, engagement_rate: 8.9, viral_score: 68, is_winner: false },
        ],
    },
];

// =============================================================================
// Helper Components
// =============================================================================

const StatCard: React.FC<{
    label: string;
    value: string | number;
    change?: number;
    icon: React.ReactNode;
    color?: string;
}> = ({ label, value, change, icon, color = 'emerald' }) => (
    <div className="bg-slate-900/50 rounded-xl border border-white/10 p-4 hover:border-white/20 transition-colors">
        <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-500 uppercase tracking-wider">{label}</span>
            <div className={`p-1.5 rounded-lg bg-${color}-500/20`}>
                {icon}
            </div>
        </div>
        <div className="flex items-end justify-between">
            <span className="text-2xl font-bold text-white">{value}</span>
            {change !== undefined && (
                <span className={`text-xs flex items-center gap-0.5 ${change >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {Math.abs(change)}%
                </span>
            )}
        </div>
    </div>
);

const STYLE_COLORS: Record<string, string> = {
    shock: 'bg-red-500',
    curiosity: 'bg-purple-500',
    emotion: 'bg-pink-500',
    paradox: 'bg-yellow-500',
    tease: 'bg-cyan-500',
    action: 'bg-orange-500',
    question: 'bg-blue-500',
    calm: 'bg-emerald-500',
};

const STYLE_LABELS: Record<string, string> = {
    shock: '충격형',
    curiosity: '호기심형',
    emotion: '감정형',
    paradox: '역설형',
    tease: '티저형',
    action: '액션형',
    question: '의문형',
    calm: '차분형',
};

// =============================================================================
// Main Component
// =============================================================================

export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({
    className = '',
    onRefresh,
}) => {
    const [activeTab, setActiveTab] = useState<'overview' | 'ab-tests' | 'insights'>('overview');
    const [isLoading, setIsLoading] = useState(false);
    const [aggregates, setAggregates] = useState<AggregateData[]>(MOCK_AGGREGATES);
    const [insights, setInsights] = useState<ViralInsight[]>(MOCK_INSIGHTS);
    const [abTests, setAbTests] = useState<ABTestResult[]>(MOCK_AB_TESTS);
    const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

    const handleRefresh = useCallback(async () => {
        setIsLoading(true);
        // TODO: Replace with actual API calls
        // const response = await api.getAggregateMetrics({ days: period === '7d' ? 7 : period === '30d' ? 30 : 90 });
        await new Promise(resolve => setTimeout(resolve, 500));
        setIsLoading(false);
        onRefresh?.();
    }, [period, onRefresh]);

    // Calculate totals
    const totals = aggregates.reduce((acc, item) => ({
        views: acc.views + item.total_views,
        content: acc.content + item.total_content,
        avgEngagement: acc.avgEngagement + item.avg_engagement_rate,
        avgViral: acc.avgViral + item.avg_viral_score,
    }), { views: 0, content: 0, avgEngagement: 0, avgViral: 0 });

    const avgEngagement = aggregates.length > 0 ? (totals.avgEngagement / aggregates.length).toFixed(1) : 0;
    const avgViral = aggregates.length > 0 ? Math.round(totals.avgViral / aggregates.length) : 0;

    return (
        <div className={`bg-[#0A0A0C] min-h-screen text-white ${className}`}>
            {/* Header */}
            <div className="border-b border-white/10 bg-white/[0.02]">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-white/10">
                                <BarChart3 className="w-6 h-6 text-purple-400" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold tracking-tight">Metrics Dashboard</h1>
                                <p className="text-sm text-slate-500">바이럴 성과 및 A/B 테스트 결과</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            {/* Period Selector */}
                            <div className="flex bg-black/30 rounded-lg p-1 border border-white/5">
                                {(['7d', '30d', '90d'] as const).map(p => (
                                    <button
                                        key={p}
                                        onClick={() => setPeriod(p)}
                                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${period === p
                                                ? 'bg-purple-600 text-white'
                                                : 'text-slate-400 hover:text-white'
                                            }`}
                                    >
                                        {p === '7d' ? '7일' : p === '30d' ? '30일' : '90일'}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={handleRefresh}
                                disabled={isLoading}
                                className="p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                            >
                                <RefreshCw className={`w-4 h-4 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-1 mt-4">
                        {[
                            { id: 'overview', label: '개요', icon: PieChart },
                            { id: 'ab-tests', label: 'A/B 테스트', icon: Target },
                            { id: 'insights', label: '인사이트', icon: Lightbulb },
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${activeTab === tab.id
                                        ? 'bg-white/5 text-white border-b-2 border-purple-500'
                                        : 'text-slate-500 hover:text-slate-300'
                                    }`}
                            >
                                <tab.icon size={16} />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-6">
                {/* OVERVIEW TAB */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* Stat Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <StatCard
                                label="총 조회수"
                                value={`${(totals.views / 1000000).toFixed(1)}M`}
                                change={12}
                                icon={<Eye size={16} className="text-emerald-400" />}
                            />
                            <StatCard
                                label="총 콘텐츠"
                                value={totals.content}
                                change={8}
                                icon={<BarChart3 size={16} className="text-purple-400" />}
                                color="purple"
                            />
                            <StatCard
                                label="평균 참여율"
                                value={`${avgEngagement}%`}
                                change={5}
                                icon={<Heart size={16} className="text-pink-400" />}
                                color="pink"
                            />
                            <StatCard
                                label="평균 바이럴 점수"
                                value={avgViral}
                                change={-2}
                                icon={<Flame size={16} className="text-orange-400" />}
                                color="orange"
                            />
                        </div>

                        {/* Hook Style Comparison Chart */}
                        <div className="bg-slate-900/50 rounded-xl border border-white/10 p-6">
                            <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                                <Zap size={16} className="text-yellow-400" />
                                훅 스타일별 성과 비교
                            </h2>

                            <div className="space-y-3">
                                {aggregates.map((item, idx) => {
                                    const maxViral = Math.max(...aggregates.map(a => a.avg_viral_score));
                                    const percentage = (item.avg_viral_score / maxViral) * 100;

                                    return (
                                        <div key={item.group_key} className="space-y-1">
                                            <div className="flex items-center justify-between text-xs">
                                                <div className="flex items-center gap-2">
                                                    <div className={`w-2 h-2 rounded-full ${STYLE_COLORS[item.group_key] || 'bg-slate-500'}`} />
                                                    <span className="text-slate-300">
                                                        {STYLE_LABELS[item.group_key] || item.group_key}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-4 text-slate-500">
                                                    <span>{item.total_content}개</span>
                                                    <span>{(item.total_views / 1000).toFixed(0)}K views</span>
                                                    <span className="text-yellow-400 font-medium">{item.avg_viral_score}점</span>
                                                </div>
                                            </div>
                                            <div className="relative h-2 bg-slate-800 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${percentage}%` }}
                                                    transition={{ duration: 0.5, delay: idx * 0.1 }}
                                                    className={`absolute left-0 top-0 h-full rounded-full ${STYLE_COLORS[item.group_key] || 'bg-slate-500'}`}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* A/B TESTS TAB */}
                {activeTab === 'ab-tests' && (
                    <div className="space-y-4">
                        {abTests.map(test => (
                            <div key={test.test_id} className="bg-slate-900/50 rounded-xl border border-white/10 p-5">
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <h3 className="font-semibold text-white flex items-center gap-2">
                                            {test.test_name}
                                            <span className={`px-2 py-0.5 text-[10px] rounded-full ${test.status === 'completed'
                                                    ? 'bg-emerald-500/20 text-emerald-400'
                                                    : test.status === 'running'
                                                        ? 'bg-yellow-500/20 text-yellow-400'
                                                        : 'bg-slate-500/20 text-slate-400'
                                                }`}>
                                                {test.status === 'completed' ? '완료' : test.status === 'running' ? '진행중' : '취소'}
                                            </span>
                                        </h3>
                                        <p className="text-xs text-slate-500 mt-1">
                                            시작: {new Date(test.started_at).toLocaleDateString('ko-KR')}
                                            {test.ended_at && ` → 종료: ${new Date(test.ended_at).toLocaleDateString('ko-KR')}`}
                                        </p>
                                    </div>
                                    {test.confidence_level && (
                                        <div className="text-right">
                                            <span className="text-xs text-slate-500">신뢰도</span>
                                            <p className="text-lg font-bold text-emerald-400">{test.confidence_level}%</p>
                                        </div>
                                    )}
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    {test.variants.map(variant => (
                                        <div
                                            key={variant.variant_id}
                                            className={`p-4 rounded-lg border transition-colors ${variant.is_winner
                                                    ? 'bg-emerald-500/10 border-emerald-500/50'
                                                    : 'bg-slate-800/50 border-white/5'
                                                }`}
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <span className={`text-sm font-medium ${variant.is_winner ? 'text-emerald-400' : 'text-slate-300'
                                                    }`}>
                                                    {STYLE_LABELS[variant.style] || variant.style}
                                                </span>
                                                {variant.is_winner && (
                                                    <Award size={16} className="text-emerald-400" />
                                                )}
                                            </div>
                                            <div className="space-y-1 text-xs text-slate-500">
                                                <div className="flex justify-between">
                                                    <span>조회수</span>
                                                    <span className="text-slate-300">{(variant.views / 1000).toFixed(1)}K</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span>참여율</span>
                                                    <span className="text-slate-300">{variant.engagement_rate}%</span>
                                                </div>
                                                <div className="flex justify-between">
                                                    <span>바이럴 점수</span>
                                                    <span className={variant.is_winner ? 'text-emerald-400 font-medium' : 'text-slate-300'}>
                                                        {variant.viral_score}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}

                        {abTests.length === 0 && (
                            <div className="text-center py-20">
                                <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <h3 className="text-slate-300 font-medium">A/B 테스트 없음</h3>
                                <p className="text-slate-500 text-sm mt-1">
                                    훅 셀렉터에서 A/B 테스트를 시작하세요.
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* INSIGHTS TAB */}
                {activeTab === 'insights' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {insights.map((insight, idx) => (
                            <motion.div
                                key={idx}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                className="bg-slate-900/50 rounded-xl border border-white/10 p-5 hover:border-purple-500/30 transition-colors"
                            >
                                <div className="flex items-start gap-3">
                                    <div className="p-2 rounded-lg bg-purple-500/20">
                                        <Lightbulb size={18} className="text-purple-400" />
                                    </div>
                                    <div className="flex-1">
                                        <h3 className="font-semibold text-white text-sm">{insight.title}</h3>
                                        <p className="text-xs text-slate-400 mt-1">{insight.description}</p>

                                        {insight.recommendation && (
                                            <div className="mt-3 p-2.5 bg-purple-500/10 rounded-lg border border-purple-500/20">
                                                <p className="text-xs text-purple-300">
                                                    💡 {insight.recommendation}
                                                </p>
                                            </div>
                                        )}

                                        {/* Data Badges */}
                                        <div className="flex flex-wrap gap-2 mt-3">
                                            {Object.entries(insight.data).map(([key, value]) => (
                                                <span
                                                    key={key}
                                                    className="px-2 py-1 text-[10px] bg-white/5 rounded-full text-slate-400"
                                                >
                                                    {key}: <span className="text-white">{value}</span>
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        ))}

                        {insights.length === 0 && (
                            <div className="col-span-2 text-center py-20">
                                <Lightbulb className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                                <h3 className="text-slate-300 font-medium">인사이트 없음</h3>
                                <p className="text-slate-500 text-sm mt-1">
                                    더 많은 데이터가 수집되면 인사이트가 생성됩니다.
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default MetricsDashboard;
