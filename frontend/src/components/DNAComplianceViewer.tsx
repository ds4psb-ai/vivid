'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CheckCircle, AlertTriangle, XCircle, HelpCircle,
    ChevronDown, RefreshCw, Wand2,
    Shield
} from 'lucide-react';
import type { BatchComplianceReport, ShotComplianceReport, RuleResult } from '@/types/storyFirst';

// Re-export for compatibility
export type { BatchComplianceReport, ShotComplianceReport, RuleResult };

// =============================================================================
// Props
// =============================================================================

export interface DNAComplianceViewerProps {
    report: BatchComplianceReport;
    className?: string;
    compact?: boolean;
    onRegenerateShot?: (shotId: string, suggestions: string[]) => void;
    onApplyAllSuggestions?: (shotIds: string[]) => void;
    onExport?: (format: 'json' | 'csv') => void;
    isActionsLoading?: boolean;
}

// =============================================================================
// Helper Components
// =============================================================================

const LevelBadge: React.FC<{ level: string; size?: 'sm' | 'md' }> = ({ level, size = 'sm' }) => {
    const config = {
        compliant: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', label: '적합' },
        partial: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', label: '주의' },
        violation: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', label: '위반' },
        unknown: { icon: HelpCircle, color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/20', label: '확인불가' },
    }[level] || { icon: HelpCircle, color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/20', label: '알수없음' };

    const Icon = config.icon;
    const iconSize = size === 'sm' ? 14 : 16;
    const textSize = size === 'sm' ? 'text-[10px]' : 'text-xs';
    const px = size === 'sm' ? 'px-2' : 'px-2.5';
    const py = size === 'sm' ? 'py-0.5' : 'py-1';

    return (
        <span className={`inline-flex items-center gap-1.5 ${px} ${py} rounded-full border ${config.bg} ${config.border} ${config.color} ${textSize} font-medium`}>
            <Icon size={iconSize} />
            {config.label}
        </span>
    );
};

const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
    const config = {
        critical: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
        high: { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
        medium: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
        low: { color: 'text-gray-400', bg: 'bg-white/5', border: 'border-white/10' },
    }[priority] || { color: 'text-gray-400', bg: 'bg-white/5', border: 'border-white/10' };

    return (
        <span className={`px-1.5 py-0.5 text-[10px] uppercase tracking-wider rounded border ${config.bg} ${config.color} ${config.border}`}>
            {priority}
        </span>
    );
};

const ProgressBar: React.FC<{ value: number; className?: string }> = ({ value, className = '' }) => {
    const percent = Math.round(value * 100);
    const color = percent >= 80 ? 'bg-emerald-500' : percent >= 50 ? 'bg-yellow-500' : 'bg-red-500';

    return (
        <div className={`h-1.5 w-full bg-white/5 rounded-full overflow-hidden ${className}`}>
            <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${percent}%` }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className={`h-full ${color} shadow-[0_0_10px_rgba(255,255,255,0.2)]`}
            />
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
    onRegenerateShot,
    onApplyAllSuggestions,
    isActionsLoading = false,
}) => {
    const [expandedShots, setExpandedShots] = useState<Set<string>>(new Set());

    const toggleShot = (shotId: string) => {
        const newSet = new Set(expandedShots);
        if (newSet.has(shotId)) {
            newSet.delete(shotId);
        } else {
            newSet.add(shotId);
        }
        setExpandedShots(newSet);
    };

    const hasCriticalIssues = report.violation_shots > 0;
    const violationsList = report.shot_reports.filter(r => r.overall_level === 'violation' || r.overall_level === 'partial');
    const compliantList = report.shot_reports.filter(r => r.overall_level === 'compliant');

    return (
        <div className={`space-y-6 ${className}`}>
            {/* Summary Card */}
            <div className={`
                rounded-xl border p-5 backdrop-blur-md transition-all
                ${hasCriticalIssues
                    ? 'bg-red-500/5 border-red-500/20 shadow-[0_0_20px_-10px_rgba(239,68,68,0.2)]'
                    : 'bg-emerald-500/5 border-emerald-500/20 shadow-[0_0_20px_-10px_rgba(16,185,129,0.2)]'
                }
            `}>
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl ${hasCriticalIssues ? 'bg-red-500/10 text-red-500' : 'bg-emerald-500/10 text-emerald-500'}`}>
                            <Shield size={24} />
                        </div>
                        <div>
                            <h3 className={`text-lg font-bold ${hasCriticalIssues ? 'text-white' : 'text-white'}`}>
                                {hasCriticalIssues ? 'DNA 가이드라인 위반 감지' : 'DNA 가이드라인 준수'}
                            </h3>
                            <p className="text-sm text-gray-400">
                                {hasCriticalIssues
                                    ? `${report.violation_shots}개의 샷에서 수정이 필요한 항목이 발견되었습니다.`
                                    : '모든 샷이 브랜드 가이드라인을 준수하고 있습니다.'}
                            </p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-2xl font-bold text-white mb-0.5">
                            {(report.overall_compliance_rate * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-500 uppercase tracking-wider">준수율</div>
                    </div>
                </div>

                <div className="space-y-4">
                    <ProgressBar value={report.overall_compliance_rate} />

                    <div className="grid grid-cols-3 gap-2">
                        <div className="bg-black/20 rounded-lg p-2.5 flex flex-col items-center border border-white/5">
                            <span className="text-emerald-400 font-bold text-lg">{report.compliant_shots}</span>
                            <span className="text-[10px] text-gray-500">적합</span>
                        </div>
                        <div className="bg-black/20 rounded-lg p-2.5 flex flex-col items-center border border-white/5">
                            <span className="text-yellow-400 font-bold text-lg">{report.partial_shots}</span>
                            <span className="text-[10px] text-gray-500">주의</span>
                        </div>
                        <div className="bg-black/20 rounded-lg p-2.5 flex flex-col items-center border border-white/5">
                            <span className="text-red-400 font-bold text-lg">{report.violation_shots}</span>
                            <span className="text-[10px] text-gray-500">위반</span>
                        </div>
                    </div>
                </div>

                {hasCriticalIssues && onApplyAllSuggestions && (
                    <div className="mt-5 pt-4 border-t border-white/5">
                        <button
                            onClick={() => onApplyAllSuggestions(violationsList.map(r => r.shot_id))}
                            disabled={isActionsLoading}
                            className="w-full py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-all shadow-lg shadow-red-900/40"
                        >
                            {isActionsLoading ? <RefreshCw size={16} className="animate-spin" /> : <Wand2 size={16} />}
                            모든 위반 사항 자동 수정 ({violationsList.length}건)
                        </button>
                    </div>
                )}
            </div>

            {/* Violation Shots List */}
            {violationsList.length > 0 && (
                <div className="space-y-3">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider pl-1">수정이 필요한 샷</h4>
                    {violationsList.map(shot => (
                        <div key={shot.shot_id} className="bg-white/5 border border-white/5 rounded-xl overflow-hidden backdrop-blur-sm hover:border-white/10 transition-colors">
                            <button
                                onClick={() => toggleShot(shot.shot_id)}
                                className="w-full p-4 flex items-center justify-between text-left"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-sm font-mono text-gray-400">{shot.shot_id}</span>
                                    <LevelBadge level={shot.overall_level} />
                                    {shot.critical_violations > 0 && (
                                        <span className="text-[10px] font-bold text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                                            CRITICAL
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-3">
                                    <div className="flex gap-1.5">
                                        {shot.suggestions.length > 0 && (
                                            <span className="px-2 py-0.5 bg-purple-500/10 text-purple-300 text-[10px] rounded border border-purple-500/20 flex items-center gap-1">
                                                <Wand2 size={10} />
                                                제안 {shot.suggestions.length}
                                            </span>
                                        )}
                                    </div>
                                    <ChevronDown size={16} className={`text-gray-500 transition-transform ${expandedShots.has(shot.shot_id) ? 'rotate-180' : ''}`} />
                                </div>
                            </button>

                            <AnimatePresence>
                                {expandedShots.has(shot.shot_id) && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="border-t border-white/5 bg-black/20"
                                    >
                                        <div className="p-4 space-y-4">
                                            {/* Rule Results */}
                                            <div className="space-y-2">
                                                {shot.rule_results.map((rule, idx) => (
                                                    <div key={idx} className="flex items-start gap-3 text-sm p-2 rounded hover:bg-white/5 transition-colors">
                                                        <div className="mt-0.5"><LevelBadge level={rule.level} size="sm" /></div>
                                                        <div className="flex-1">
                                                            <div className="flex items-baseline gap-2 mb-0.5">
                                                                <span className="font-medium text-gray-200">{rule.rule_name}</span>
                                                                <PriorityBadge priority={rule.priority} />
                                                            </div>
                                                            <p className="text-gray-400 text-xs leading-relaxed">{rule.message}</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Suggestions Action */}
                                            {shot.suggestions.length > 0 && (
                                                <div className="bg-purple-500/5 border border-purple-500/10 rounded-lg p-3">
                                                    <div className="flex items-center gap-2 mb-2 text-purple-300">
                                                        <Wand2 size={14} />
                                                        <span className="text-xs font-bold">AI 수정 제안</span>
                                                    </div>
                                                    <ul className="space-y-1 mb-3">
                                                        {shot.suggestions.map((s, i) => (
                                                            <li key={i} className="text-xs text-gray-400 pl-4 relative before:content-['•'] before:absolute before:left-1 before:text-purple-500">
                                                                {s}
                                                            </li>
                                                        ))}
                                                    </ul>
                                                    <button
                                                        onClick={() => onRegenerateShot?.(shot.shot_id, shot.suggestions)}
                                                        disabled={isActionsLoading}
                                                        className="w-full py-2 bg-purple-600 hover:bg-purple-500 text-white rounded text-xs font-medium transition-colors shadow-lg shadow-purple-900/20"
                                                    >
                                                        이 제안으로 샷 재생성
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    ))}
                </div>
            )}

            {/* Compliant List (Collapsible) */}
            {compliantList.length > 0 && !compact && (
                <div className="pt-4 border-t border-white/5">
                    <button
                        onClick={() => { }} // Could add toggle logic for this section
                        className="flex items-center gap-2 text-xs font-medium text-gray-500 hover:text-gray-300 transition-colors"
                    >
                        <span>통과된 샷 ({compliantList.length})</span>
                        <ChevronDown size={12} />
                    </button>
                </div>
            )}
        </div>
    );
};

export default DNAComplianceViewer;
