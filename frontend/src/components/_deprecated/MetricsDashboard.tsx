'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Eye, Heart,
    BarChart3, PieChart, Zap, Lightbulb,
    RefreshCw, Calendar,
    Award, Target, Flame, ArrowUpRight, ArrowDownRight,
    Activity, Sparkles
} from 'lucide-react';
import { api } from '@/lib/api';

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
    data: Record<string, unknown>;
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

type DashboardTab = 'overview' | 'ab-tests' | 'insights';

// =============================================================================
// Mock Data (fallback when API unavailable)
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
        title: '역설형 훅: 바이럴 점수 최고 기록',
        description: '지난 30일간 역설형(paradox) 훅이 평균 78점으로 가장 높은 바이럴 점수를 기록했습니다.',
        data: { style: 'paradox', score: 78, improvement: '+12%' },
        recommendation: '익숙함과 낯선 요소의 조합을 더 적극적으로 활용하여 시청자의 예상을 깨뜨리세요.',
    },
    {
        insight_type: 'engagement_leader',
        title: '감정형 훅: 참여율 1위 달성',
        description: '감정형(emotion) 훅이 11.5%의 높은 참여율로 전체 스타일 중 1위를 차지했습니다.',
        data: { style: 'emotion', rate: 11.5, benchmark: 7.2 },
        recommendation: '시청자의 공감을 이끌어내는 감정적 스토리텔링을 도입부에 배치하세요.',
    },
    {
        insight_type: 'growth_trend',
        title: '충격형 콘텐츠 제작 증가',
        description: '이번 달 충격형 훅 사용이 지난달 대비 40% 증가하며 트렌드를 주도하고 있습니다.',
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
    <div className="group bg-white/5 backdrop-blur-md rounded-2xl border border-white/5 p-5 hover:bg-white/10 hover:border-white/10 transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">{label}</span>
            <div className={`p-2 rounded-xl bg-white/5 text-${color}-400 group-hover:scale-110 transition-transform duration-300`}>
                {icon}
            </div>
        </div>
        <div className="flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white tracking-tight">{value}</span>
        </div>
        {change !== undefined && (
            <div className="mt-2 flex items-center gap-2">
                <span className={`text-xs font-semibold px-1.5 py-0.5 rounded flex items-center gap-0.5 ${change >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                    }`}>
                    {change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {Math.abs(change)}%
                </span>
                <span className="text-[10px] text-gray-500">지난달 대비</span>
            </div>
        )}
    </div>
);

// Using explicit colors for safety
const STYLE_BAR_COLORS: Record<string, string> = {
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
    const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
    const [isLoading, setIsLoading] = useState(false);
    const [aggregates, setAggregates] = useState<AggregateData[]>(MOCK_AGGREGATES);
    const [insights, setInsights] = useState<ViralInsight[]>(MOCK_INSIGHTS);
    const [abTests, setAbTests] = useState<ABTestResult[]>(MOCK_AB_TESTS);
    const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;

        try {
            // Fetch aggregate metrics
            const aggregateRes = await api.getAggregateMetrics({ group_by: 'hook_style', days });
            if (aggregateRes.data && aggregateRes.data.length > 0) {
                setAggregates(aggregateRes.data);
            }
        } catch {
            // Fall back to mock data
            setAggregates(MOCK_AGGREGATES);
        }

        try {
            // Fetch viral insights
            const insightsRes = await api.getViralInsights({ days });
            if (insightsRes.insights && insightsRes.insights.length > 0) {
                setInsights(insightsRes.insights as ViralInsight[]);
            }
        } catch {
            setInsights(MOCK_INSIGHTS);
        }

        try {
            // Fetch A/B tests
            const abRes = await api.listABTests();
            if (abRes && abRes.length > 0) {
                setAbTests(abRes as ABTestResult[]);
            }
        } catch {
            setAbTests(MOCK_AB_TESTS);
        }

        setIsLoading(false);
        onRefresh?.();
    }, [period, onRefresh]);

    // Load data on mount and period change
    useEffect(() => {
        const timeout = setTimeout(() => {
            void fetchData();
        }, 0);
        return () => clearTimeout(timeout);
    }, [fetchData]);

    const handleRefresh = useCallback(() => {
        fetchData();
    }, [fetchData]);

    const tabs: Array<{ id: DashboardTab; label: string; icon: React.ElementType }> = [
        { id: 'overview', label: '개요', icon: PieChart },
        { id: 'ab-tests', label: 'A/B 테스트', icon: Target },
        { id: 'insights', label: '인사이트', icon: Lightbulb },
    ];

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
        <div className={`bg-[#0A0A0C] min-h-screen text-white font-sans ${className}`}>
            {/* Header */}
            <div className="sticky top-0 z-20 border-b border-white/5 bg-[#0A0A0C]/80 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/20 shadow-[0_0_15px_-3px_rgba(168,85,247,0.2)]">
                                <Activity className="w-6 h-6 text-purple-400" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold tracking-tight text-white">Metrics Dashboard</h1>
                                <p className="text-sm text-gray-500">실시간 바이럴 성과 및 테스트 분석</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3">
                            {/* Period Selector */}
                            <div className="flex bg-white/5 rounded-lg p-1 border border-white/5">
                                {(['7d', '30d', '90d'] as const).map(p => (
                                    <button
                                        key={p}
                                        onClick={() => setPeriod(p)}
                                        className={`
                                            px-3 py-1.5 text-xs font-medium rounded-md transition-all
                                            ${period === p
                                                ? 'bg-purple-600/20 text-purple-300 shadow-sm'
                                                : 'text-gray-500 hover:text-gray-300'
                                            }
                                        `}
                                    >
                                        {p === '7d' ? '7일' : p === '30d' ? '30일' : '90일'}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={handleRefresh}
                                disabled={isLoading}
                                className="p-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 hover:text-white transition-all text-gray-400"
                            >
                                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-6 mt-6 border-b border-white/0">
                        {tabs.map(tab => {
                            const isActive = activeTab === tab.id;
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`
                                        group flex items-center gap-2 pb-3 text-sm font-medium transition-all relative
                                        ${isActive ? 'text-white' : 'text-gray-500 hover:text-gray-300'}
                                    `}
                                >
                                    <Icon size={16} className={isActive ? 'text-purple-400' : 'group-hover:text-gray-400'} />
                                    {tab.label}
                                    {isActive && (
                                        <motion.div
                                            layoutId="metricTabIndicator"
                                            className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 to-pink-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]"
                                        />
                                    )}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-6 py-8">
                <AnimatePresence mode="wait">
                    {/* OVERVIEW TAB */}
                    {activeTab === 'overview' && (
                        <motion.div
                            key="overview"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                            className="space-y-6"
                        >
                            {/* Stat Cards */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                <StatCard
                                    label="총 조회수"
                                    value={`${(totals.views / 1000000).toFixed(1)}M`}
                                    change={12}
                                    icon={<Eye size={20} />}
                                    color="emerald"
                                />
                                <StatCard
                                    label="총 콘텐츠"
                                    value={totals.content}
                                    change={8}
                                    icon={<BarChart3 size={20} />}
                                    color="purple"
                                />
                                <StatCard
                                    label="평균 참여율"
                                    value={`${avgEngagement}%`}
                                    change={5}
                                    icon={<Heart size={20} />}
                                    color="pink"
                                />
                                <StatCard
                                    label="평균 바이럴 점수"
                                    value={avgViral}
                                    change={-2}
                                    icon={<Flame size={20} />}
                                    color="orange"
                                />
                            </div>

                            {/* Hook Style Comparison Chart */}
                            <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/5 p-7">
                                <h2 className="text-base font-bold text-white mb-6 flex items-center gap-2">
                                    <div className="p-1.5 bg-yellow-500/10 rounded-lg">
                                        <Zap size={16} className="text-yellow-400" />
                                    </div>
                                    훅 스타일별 성과 분석
                                </h2>

                                <div className="space-y-4">
                                    {aggregates.map((item, idx) => {
                                        const maxViral = Math.max(...aggregates.map(a => a.avg_viral_score));
                                        const percentage = (item.avg_viral_score / maxViral) * 100;

                                        return (
                                            <div key={item.group_key} className="group">
                                                <div className="flex items-center justify-between text-xs mb-2">
                                                    <div className="flex items-center gap-2.5">
                                                        <div className={`w-2.5 h-2.5 rounded-full ${STYLE_BAR_COLORS[item.group_key] || 'bg-gray-500'} shadow-[0_0_8px_rgba(0,0,0,0.5)]`} />
                                                        <span className="text-gray-300 font-medium text-sm">
                                                            {STYLE_LABELS[item.group_key] || item.group_key}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-6 text-gray-500 font-light">
                                                        <span>콘텐츠 {item.total_content}개</span>
                                                        <span className="w-20 text-right">{(item.total_views / 1000).toFixed(0)}K views</span>
                                                        <span className="w-12 text-right text-yellow-500 font-bold">{item.avg_viral_score}점</span>
                                                    </div>
                                                </div>
                                                <div className="relative h-2.5 bg-white/5 rounded-full overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${percentage}%` }}
                                                        transition={{ duration: 0.8, delay: idx * 0.1, ease: "easeOut" }}
                                                        className={`absolute left-0 top-0 h-full rounded-full ${STYLE_BAR_COLORS[item.group_key] || 'bg-gray-500'} shadow-[0_0_10px_rgba(255,255,255,0.2)]`}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* A/B TESTS TAB */}
                    {activeTab === 'ab-tests' && (
                        <motion.div
                            key="ab-tests"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                            className="space-y-4"
                        >
                            {abTests.map(test => (
                                <div key={test.test_id} className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/5 p-6 hover:border-white/10 transition-colors">
                                    <div className="flex items-center justify-between mb-5">
                                        <div>
                                            <h3 className="font-bold text-white text-lg flex items-center gap-3">
                                                {test.test_name}
                                                <span className={`px-2.5 py-1 text-[10px] font-bold rounded-full uppercase tracking-wide ${test.status === 'completed'
                                                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                                    : test.status === 'running'
                                                        ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse'
                                                        : 'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                                                    }`}>
                                                    {test.status === 'completed' ? 'COMPLETED' : test.status === 'running' ? 'RUNNING' : 'CANCELLED'}
                                                </span>
                                            </h3>
                                            <p className="text-xs text-gray-500 mt-1.5 flex items-center gap-2">
                                                <Calendar size={12} />
                                                {new Date(test.started_at).toLocaleDateString('ko-KR')} 시작
                                                {test.ended_at && ` · ${new Date(test.ended_at).toLocaleDateString('ko-KR')} 종료`}
                                            </p>
                                        </div>
                                        {test.confidence_level && (
                                            <div className="text-right">
                                                <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Confidence</span>
                                                <div className="text-2xl font-bold text-emerald-400 flex items-center justify-end gap-1">
                                                    {test.confidence_level}%
                                                    <Award size={18} />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {test.variants.map(variant => (
                                            <div
                                                key={variant.variant_id}
                                                className={`p-5 rounded-xl border transition-all duration-300 relative overflow-hidden ${variant.is_winner
                                                    ? 'bg-emerald-500/10 border-emerald-500/30 ring-1 ring-emerald-500/30'
                                                    : 'bg-white/5 border-white/5'
                                                    }`}
                                            >
                                                {variant.is_winner && (
                                                    <div className="absolute top-0 right-0 p-2 bg-emerald-500/20 rounded-bl-xl">
                                                        <Award size={16} className="text-emerald-400" />
                                                    </div>
                                                )}

                                                <div className="flex items-center justify-between mb-3">
                                                    <span className={`text-base font-bold ${variant.is_winner ? 'text-emerald-400' : 'text-gray-300'}`}>
                                                        {STYLE_LABELS[variant.style] || variant.style}
                                                    </span>
                                                </div>

                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center p-2 rounded-lg bg-black/20">
                                                        <span className="text-xs text-gray-500">조회수</span>
                                                        <span className="text-sm font-medium text-white">{(variant.views / 1000).toFixed(1)}K</span>
                                                    </div>
                                                    <div className="flex justify-between items-center p-2 rounded-lg bg-black/20">
                                                        <span className="text-xs text-gray-500">참여율</span>
                                                        <span className="text-sm font-medium text-white">{variant.engagement_rate}%</span>
                                                    </div>
                                                    <div className="flex justify-between items-center p-2 rounded-lg bg-black/20">
                                                        <span className="text-xs text-gray-500">바이럴 점수</span>
                                                        <span className={`text-sm font-bold ${variant.is_winner ? 'text-emerald-400' : 'text-white'}`}>
                                                            {variant.viral_score}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </motion.div>
                    )}

                    {/* INSIGHTS TAB */}
                    {activeTab === 'insights' && (
                        <motion.div
                            key="insights"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                            className="grid grid-cols-1 md:grid-cols-2 gap-5"
                        >
                            {insights.map((insight, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className="group bg-white/5 backdrop-blur-md rounded-2xl border border-white/5 p-6 hover:bg-white/10 hover:border-purple-500/30 hover:shadow-[0_0_20px_-5px_rgba(168,85,247,0.2)] transition-all duration-300"
                                >
                                    <div className="flex items-start gap-4">
                                        <div className="p-3 rounded-xl bg-purple-500/10 group-hover:bg-purple-500/20 transition-colors">
                                            <Lightbulb size={24} className="text-purple-400" />
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="font-bold text-white text-base mb-1">{insight.title}</h3>
                                            <p className="text-sm text-gray-400 leading-relaxed mb-4">{insight.description}</p>

                                            {insight.recommendation && (
                                                <div className="p-3 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl border border-purple-500/20 mb-4">
                                                    <p className="text-xs text-purple-200 font-medium flex items-center gap-2">
                                                        <Sparkles size={12} className="text-purple-400" />
                                                        Action Item
                                                    </p>
                                                    <p className="text-sm text-purple-100 mt-1">
                                                        {insight.recommendation}
                                                    </p>
                                                </div>
                                            )}

                                            <div className="flex flex-wrap gap-2">
                                                {Object.entries(insight.data).map(([key, value]) => (
                                                    <span
                                                        key={key}
                                                        className="px-2.5 py-1 text-[11px] font-medium bg-black/30 rounded-full text-gray-400 border border-white/5"
                                                    >
                                                        {key.toUpperCase()}: <span className="text-white ml-1">{value}</span>
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default MetricsDashboard;
