'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertTriangle, XCircle, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

export interface RuleResult {
    rule_id: string;
    rule_name: string;
    priority: 'critical' | 'high' | 'medium' | 'low';
    level: 'compliant' | 'partial' | 'violation' | 'unknown';
    confidence: number;
    message: string;
    expected?: string | number | null;
    actual?: string | number | null;
}

export interface ShotComplianceReport {
    shot_id: string;
    badge?: string;
    overall_level: 'compliant' | 'partial' | 'violation' | 'unknown';
    overall_confidence: number;
    rule_results: RuleResult[];
    critical_violations: number;
    high_violations: number;
    suggestions: string[];
}

export interface BatchComplianceReport {
    total_shots: number;
    compliant_shots: number;
    partial_shots: number;
    violation_shots: number;
    overall_compliance_rate: number;
    summary: string;
    shot_reports: ShotComplianceReport[];
}

export interface DNAComplianceViewerProps {
    report: BatchComplianceReport;
    className?: string;
    compact?: boolean;
}

// =============================================================================
// Helper Components
// =============================================================================

const LevelBadge: React.FC<{ level: string; size?: 'sm' | 'md' }> = ({ level, size = 'sm' }) => {
    const config = {
        compliant: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
        partial: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
        violation: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20' },
        unknown: { icon: HelpCircle, color: 'text-gray-400', bg: 'bg-gray-500/20' },
    }[level] || { icon: HelpCircle, color: 'text-gray-400', bg: 'bg-gray-500/20' };

    const Icon = config.icon;
    const iconSize = size === 'sm' ? 14 : 18;

    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${config.bg} ${config.color}`}>
            <Icon size={iconSize} />
            <span className={size === 'sm' ? 'text-xs' : 'text-sm'}>{level}</span>
        </span>
    );
};

const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
    const colors = {
        critical: 'bg-red-500/20 text-red-400 border-red-500/30',
        high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
        medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        low: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    }[priority] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';

    return (
        <span className={`px-1.5 py-0.5 text-xs rounded border ${colors}`}>
            {priority}
        </span>
    );
};

const ProgressBar: React.FC<{ value: number; className?: string }> = ({ value, className = '' }) => {
    const percent = Math.round(value * 100);
    const color = percent >= 80 ? 'bg-emerald-500' : percent >= 50 ? 'bg-yellow-500' : 'bg-red-500';

    return (
        <div className={`h-2 bg-gray-700 rounded-full overflow-hidden ${className}`}>
            <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percent}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className={`h-full ${color}`}
            />
        </div>
    );
};

// =============================================================================
// Shot Report Card
// =============================================================================

const ShotReportCard: React.FC<{
    report: ShotComplianceReport;
    defaultExpanded?: boolean;
}> = ({ report, defaultExpanded = false }) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    return (
        <div className="bg-gray-800 rounded-lg overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-750 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <span className="text-lg">{report.badge || '🎬'}</span>
                    <span className="font-mono text-sm text-cyan-400">{report.shot_id}</span>
                    <LevelBadge level={report.overall_level} />
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">
                        {(report.overall_confidence * 100).toFixed(0)}% 신뢰도
                    </span>
                    {isExpanded ? (
                        <ChevronUp size={16} className="text-gray-400" />
                    ) : (
                        <ChevronDown size={16} className="text-gray-400" />
                    )}
                </div>
            </button>

            {/* Expanded Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-3 pt-0 space-y-3">
                            {/* Violation Summary */}
                            {(report.critical_violations > 0 || report.high_violations > 0) && (
                                <div className="flex gap-3 text-xs">
                                    {report.critical_violations > 0 && (
                                        <span className="text-red-400">
                                            🔴 Critical: {report.critical_violations}
                                        </span>
                                    )}
                                    {report.high_violations > 0 && (
                                        <span className="text-orange-400">
                                            🟠 High: {report.high_violations}
                                        </span>
                                    )}
                                </div>
                            )}

                            {/* Rule Results */}
                            <div className="space-y-2">
                                {report.rule_results.map((rule) => (
                                    <div
                                        key={rule.rule_id}
                                        className="flex items-center justify-between p-2 bg-gray-900 rounded text-sm"
                                    >
                                        <div className="flex items-center gap-2">
                                            <PriorityBadge priority={rule.priority} />
                                            <span className="text-gray-300">{rule.rule_name}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-gray-500">{rule.message}</span>
                                            <LevelBadge level={rule.level} size="sm" />
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Suggestions */}
                            {report.suggestions.length > 0 && (
                                <div className="p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                                    <div className="text-xs font-semibold text-yellow-400 mb-1">💡 개선 제안</div>
                                    <ul className="text-xs text-gray-300 space-y-1">
                                        {report.suggestions.map((s, i) => (
                                            <li key={i}>• {s}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// =============================================================================
// Main Component
// =============================================================================

export const DNAComplianceViewer: React.FC<DNAComplianceViewerProps> = ({
    report,
    className = '',
    compact = false,
}) => {
    const [showAllShots, setShowAllShots] = useState(false);

    const displayedShots = showAllShots
        ? report.shot_reports
        : report.shot_reports.slice(0, 3);

    return (
        <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
            {/* Header with Summary */}
            <div className="p-4 bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-800">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">🧬</span>
                        <div>
                            <h3 className="text-lg font-bold text-white">DNA 준수 검증</h3>
                            <p className="text-xs text-gray-500">{report.summary}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-white">
                            {(report.overall_compliance_rate * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500">준수율</div>
                    </div>
                </div>

                {/* Progress Bar */}
                <ProgressBar value={report.overall_compliance_rate} className="mb-3" />

                {/* Stats */}
                <div className="grid grid-cols-4 gap-2 text-center">
                    <div className="p-2 bg-gray-800 rounded">
                        <div className="text-lg font-bold text-white">{report.total_shots}</div>
                        <div className="text-xs text-gray-500">전체</div>
                    </div>
                    <div className="p-2 bg-emerald-500/10 rounded">
                        <div className="text-lg font-bold text-emerald-400">{report.compliant_shots}</div>
                        <div className="text-xs text-gray-500">준수</div>
                    </div>
                    <div className="p-2 bg-yellow-500/10 rounded">
                        <div className="text-lg font-bold text-yellow-400">{report.partial_shots}</div>
                        <div className="text-xs text-gray-500">부분</div>
                    </div>
                    <div className="p-2 bg-red-500/10 rounded">
                        <div className="text-lg font-bold text-red-400">{report.violation_shots}</div>
                        <div className="text-xs text-gray-500">위반</div>
                    </div>
                </div>
            </div>

            {/* Shot Reports */}
            {!compact && (
                <div className="p-4 space-y-3">
                    <div className="text-sm font-semibold text-gray-400 mb-2">
                        샷별 상세 결과
                    </div>

                    {displayedShots.map((shot, idx) => (
                        <motion.div
                            key={shot.shot_id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.05 }}
                        >
                            <ShotReportCard
                                report={shot}
                                defaultExpanded={shot.overall_level === 'violation'}
                            />
                        </motion.div>
                    ))}

                    {/* Show More Button */}
                    {report.shot_reports.length > 3 && (
                        <button
                            onClick={() => setShowAllShots(!showAllShots)}
                            className="w-full py-2 text-sm text-gray-400 hover:text-white transition-colors"
                        >
                            {showAllShots
                                ? '접기'
                                : `${report.shot_reports.length - 3}개 더 보기`}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

// =============================================================================
// Compact Badge Component
// =============================================================================

export const ComplianceBadge: React.FC<{
    complianceRate: number;
    onClick?: () => void;
}> = ({ complianceRate, onClick }) => {
    const percent = Math.round(complianceRate * 100);
    const color = percent >= 80 ? 'emerald' : percent >= 50 ? 'yellow' : 'red';

    return (
        <button
            onClick={onClick}
            className={`px-3 py-1.5 rounded-lg flex items-center gap-2 text-xs
        bg-${color}-500/20 text-${color}-400 border border-${color}-500/30
        hover:bg-${color}-500/30 transition-colors`}
        >
            <span className="font-bold">{percent}%</span>
            <span>DNA 준수</span>
        </button>
    );
};

export default DNAComplianceViewer;
