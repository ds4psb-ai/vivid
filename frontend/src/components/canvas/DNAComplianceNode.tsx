'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Dna, CheckCircle, XCircle, AlertTriangle, RefreshCw,
    ChevronDown, ChevronUp, Sparkles, Eye, Settings
} from 'lucide-react';
import { api, NarrativeDNA, DnaComplianceResponse } from '@/lib/api';

// =============================================================================
// Types
// =============================================================================

export interface DNAComplianceNodeProps {
    nodeId: string;
    content: string;
    contentType: 'script' | 'dialogue' | 'description' | 'visual';
    narrativeDna: NarrativeDNA;
    onComplianceResult?: (result: DnaComplianceResponse) => void;
    autoCheck?: boolean;
}

// =============================================================================
// Main Component
// =============================================================================

export default function DNAComplianceNode({
    nodeId,
    content,
    contentType,
    narrativeDna,
    onComplianceResult,
    autoCheck = false,
}: DNAComplianceNodeProps) {
    const [isChecking, setIsChecking] = useState(false);
    const [result, setResult] = useState<DnaComplianceResponse | null>(null);
    const [isExpanded, setIsExpanded] = useState(true);
    const [showDnaDetails, setShowDnaDetails] = useState(false);

    const checkCompliance = useCallback(async () => {
        if (!content || content.length < 10) return;

        setIsChecking(true);
        try {
            const response = await api.checkDnaCompliance({
                content,
                content_type: contentType,
                narrative_dna: narrativeDna,
                node_id: nodeId,
            });
            setResult(response);
            onComplianceResult?.(response);
        } catch (e) {
            console.error('DNA compliance check failed:', e);
        } finally {
            setIsChecking(false);
        }
    }, [content, contentType, narrativeDna, nodeId, onComplianceResult]);

    // Auto-check on content change (debounced)
    useEffect(() => {
        if (!autoCheck || !content || content.length < 10) return;

        const timer = setTimeout(() => {
            checkCompliance();
        }, 1000);

        return () => clearTimeout(timer);
    }, [autoCheck, content, checkCompliance]);

    const getScoreColor = (score: number) => {
        if (score >= 0.8) return 'text-emerald-400';
        if (score >= 0.5) return 'text-amber-400';
        return 'text-rose-400';
    };

    const getScoreBg = (score: number) => {
        if (score >= 0.8) return 'from-emerald-500/20 to-emerald-500/5';
        if (score >= 0.5) return 'from-amber-500/20 to-amber-500/5';
        return 'from-rose-500/20 to-rose-500/5';
    };

    return (
        <div className="w-full rounded-xl border border-white/10 bg-gray-900/80 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 border-b border-white/5">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-purple-500/20">
                        <Dna size={16} className="text-purple-400" />
                    </div>
                    <span className="text-sm font-medium text-white">DNA 컴플라이언스</span>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowDnaDetails(!showDnaDetails)}
                        className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                        title="DNA 설정 보기"
                    >
                        <Settings size={14} />
                    </button>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                    >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        {/* DNA Details Panel */}
                        {showDnaDetails && (
                            <div className="p-3 border-b border-white/5 bg-purple-500/5">
                                <div className="text-xs text-gray-400 mb-2">현재 서사 DNA</div>
                                <div className="space-y-1.5 text-xs">
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">테마:</span>
                                        <span className="text-purple-300">{narrativeDna.core_theme}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">톤:</span>
                                        <span className="text-purple-300">{narrativeDna.overall_tone}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">스타일:</span>
                                        <span className="text-purple-300 truncate max-w-[150px]">{narrativeDna.visual_style}</span>
                                    </div>
                                    {narrativeDna.forbidden_tones.length > 0 && (
                                        <div className="flex justify-between">
                                            <span className="text-gray-500">금지:</span>
                                            <span className="text-rose-400">{narrativeDna.forbidden_tones.join(', ')}</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Score Display */}
                        {result ? (
                            <div className={`p-4 bg-gradient-to-b ${getScoreBg(result.compliance_score)}`}>
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        {result.is_compliant ? (
                                            <CheckCircle size={20} className="text-emerald-400" />
                                        ) : (
                                            <AlertTriangle size={20} className="text-amber-400" />
                                        )}
                                        <span className="text-white font-medium">
                                            {result.is_compliant ? '준수 통과' : '검토 필요'}
                                        </span>
                                    </div>
                                    <div className={`text-2xl font-bold ${getScoreColor(result.compliance_score)}`}>
                                        {Math.round(result.compliance_score * 100)}%
                                    </div>
                                </div>

                                {/* Issues */}
                                {result.issues.length > 0 && (
                                    <div className="space-y-2 mt-3">
                                        <div className="text-xs text-gray-400">감지된 이슈 ({result.issues.length})</div>
                                        {result.issues.slice(0, 3).map((issue) => (
                                            <div
                                                key={issue.id}
                                                className="p-2 rounded-lg bg-black/30 border border-white/5"
                                            >
                                                <div className="flex items-start gap-2">
                                                    <XCircle size={12} className={
                                                        issue.severity === 'high' ? 'text-rose-400' :
                                                            issue.severity === 'medium' ? 'text-amber-400' : 'text-gray-400'
                                                    } />
                                                    <div>
                                                        <div className="text-xs text-white">{issue.message}</div>
                                                        <div className="text-[10px] text-gray-500 mt-0.5">
                                                            💡 {issue.suggestion}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="p-4 flex flex-col items-center justify-center text-center">
                                <Eye size={24} className="text-gray-600 mb-2" />
                                <div className="text-sm text-gray-400 mb-3">
                                    콘텐츠가 서사 DNA를 준수하는지 검증합니다
                                </div>
                                <button
                                    onClick={checkCompliance}
                                    disabled={isChecking || !content}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${isChecking || !content
                                            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                                            : 'bg-purple-600 hover:bg-purple-500 text-white'
                                        }`}
                                >
                                    {isChecking ? (
                                        <>
                                            <RefreshCw size={14} className="animate-spin" />
                                            검증 중...
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles size={14} />
                                            DNA 검증 실행
                                        </>
                                    )}
                                </button>
                            </div>
                        )}

                        {/* Re-check button */}
                        {result && (
                            <div className="p-2 border-t border-white/5">
                                <button
                                    onClick={checkCompliance}
                                    disabled={isChecking}
                                    className="w-full flex items-center justify-center gap-2 py-1.5 rounded-lg text-xs text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                                >
                                    <RefreshCw size={12} className={isChecking ? 'animate-spin' : ''} />
                                    다시 검증
                                </button>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
