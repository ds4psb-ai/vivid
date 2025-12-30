'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Settings, Zap, AlertCircle, RefreshCw } from 'lucide-react';
import type { UseDirectorPackStateReturn } from '@/hooks/useDirectorPackState';

// =============================================================================
// Types
// =============================================================================

export interface CanvasDirectorPackPanelProps {
    /** State from useDirectorPackState hook */
    state: UseDirectorPackStateReturn;
    /** Current capsule ID (for loading appropriate pack) */
    capsuleId?: string;
    /** Callback when "Edit Overrides" is clicked */
    onEditOverrides?: () => void;
    /** Whether the panel is collapsed */
    defaultCollapsed?: boolean;
    /** Additional CSS classes */
    className?: string;
}

// =============================================================================
// Main Component
// =============================================================================

export const CanvasDirectorPackPanel: React.FC<CanvasDirectorPackPanelProps> = ({
    state,
    capsuleId,
    onEditOverrides,
    defaultCollapsed = true,
    className = '',
}) => {
    const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
    const [activeTab, setActiveTab] = useState<'dna' | 'scenes' | 'settings'>('dna');

    // Load packs when expanded and enabled
    useEffect(() => {
        if (!isCollapsed && state.isEnabled && state.availablePacks.length === 0) {
            const pattern = capsuleId?.split('.').pop();
            state.loadAvailablePacks(pattern);
        }
    }, [isCollapsed, state.isEnabled, state.availablePacks.length, capsuleId, state]);

    const handleToggleCollapse = useCallback(() => {
        setIsCollapsed(!isCollapsed);
    }, [isCollapsed]);

    const handleSelectPack = useCallback(async (packId: string) => {
        await state.loadPackById(packId);
    }, [state]);

    const handleRefresh = useCallback(() => {
        const pattern = capsuleId?.split('.').pop();
        state.loadAvailablePacks(pattern);
    }, [capsuleId, state]);

    const patternName = state.pack?.meta.pattern_id.split('.').pop()?.replace(/-/g, ' ') || '';

    return (
        <div className={`bg-[#151522]/95 backdrop-blur-md rounded-xl border border-white/5 overflow-hidden shadow-2xl transition-all duration-300 ${className}`}>
            {/* Header - Always Visible */}
            <div
                onClick={handleToggleCollapse}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleToggleCollapse();
                    }
                }}
                className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors cursor-pointer border-b border-white/5"
                role="button"
                tabIndex={0}
                aria-expanded={!isCollapsed}
            >
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-lg">
                        🧬
                    </div>
                    <div>
                        <div className="text-sm font-bold text-[#E8E8ED]">DirectorPack</div>
                        {state.isEnabled && state.pack && (
                            <div className="text-[10px] text-emerald-400 font-medium capitalize mt-0.5">
                                {patternName}
                            </div>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {/* Quick Toggle */}
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            state.setEnabled(!state.isEnabled);
                        }}
                        className={`w-10 h-5 rounded-full transition-colors relative ${state.isEnabled ? 'bg-emerald-500' : 'bg-gray-600'
                            }`}
                        aria-label={state.isEnabled ? 'Disable DNA mode' : 'Enable DNA mode'}
                    >
                        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${state.isEnabled ? 'translate-x-5' : 'translate-x-0.5'
                            }`} />
                    </button>
                    {isCollapsed ? (
                        <ChevronDown size={18} className="text-gray-400" />
                    ) : (
                        <ChevronUp size={18} className="text-gray-400" />
                    )}
                </div>
            </div>

            {/* Expanded Content */}
            <AnimatePresence>
                {!isCollapsed && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        {/* Tab Navigation */}
                        {state.isEnabled && state.pack && (
                            <div className="flex px-2 pt-2 border-b border-white/5 gap-1">
                                {[
                                    { id: 'dna', label: 'DNA', icon: '🧬' },
                                    { id: 'scenes', label: 'Scenes', icon: '🎬' },
                                    { id: 'settings', label: 'Settings', icon: '⚙️' }
                                ].map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id as any)}
                                        className={`flex-1 py-2 text-xs font-medium rounded-t-lg transition-colors flex items-center justify-center gap-1.5 ${activeTab === tab.id
                                            ? 'bg-white/10 text-emerald-400 border-b-2 border-emerald-500'
                                            : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                                            }`}
                                    >
                                        <span>{tab.icon}</span>
                                        {tab.label}
                                    </button>
                                ))}
                            </div>
                        )}

                        <div className="p-4 bg-[#0F0F1A]/50 min-h-[200px] max-h-[400px] overflow-y-auto custom-scrollbar">
                            {!state.isEnabled ? (
                                <div className="text-center py-8">
                                    <div className="w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-4 text-3xl">
                                        🎬
                                    </div>
                                    <h3 className="text-white font-medium mb-2">Director Mode 대기 중</h3>
                                    <p className="text-xs text-gray-400 leading-relaxed mb-6">
                                        DNA 모드를 활성화하여<br />
                                        일관된 연출 스타일을 적용하세요.
                                    </p>
                                    <button
                                        onClick={() => state.setEnabled(true)}
                                        className="px-6 py-2 text-sm bg-emerald-500 hover:bg-emerald-400 text-white font-medium rounded-lg transition-all shadow-lg shadow-emerald-500/20"
                                    >
                                        모드 활성화
                                    </button>
                                </div>
                            ) : state.isLoading ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-3">
                                    <div className="animate-spin w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full" />
                                    <span className="text-xs text-gray-400">데이터 로드 중...</span>
                                </div>
                            ) : !state.pack ? (
                                <div className="space-y-3">
                                    <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                                        <span>사용 가능한 팩</span>
                                        <button onClick={handleRefresh} className="hover:text-white"><RefreshCw size={12} /></button>
                                    </div>
                                    {state.availablePacks.map((pack) => (
                                        <button
                                            key={pack.pack_id}
                                            onClick={() => handleSelectPack(pack.pack_id)}
                                            className="w-full p-3 rounded-xl bg-[#1A1A2E] border border-white/5 hover:border-emerald-500/50 hover:bg-[#252540] transition-all text-left group"
                                        >
                                            <div className="flex justify-between items-center mb-1">
                                                <span className="text-sm font-medium text-white capitalize group-hover:text-emerald-300">
                                                    {pack.pattern_id.split('.').pop()?.replace(/-/g, ' ')}
                                                </span>
                                            </div>
                                            <div className="flex gap-2 text-[10px] text-gray-500">
                                                <span>{pack.invariant_count} Rules</span>
                                                <span>•</span>
                                                <span>{pack.slot_count} Slots</span>
                                            </div>
                                        </button>
                                    ))}
                                    {state.availablePacks.length === 0 && (
                                        <div className="text-center py-8 text-xs text-gray-500">사용 가능한 팩이 없습니다.</div>
                                    )}
                                </div>
                            ) : (
                                // Tab Content
                                <div className="space-y-4">
                                    {activeTab === 'dna' && (
                                        <div className="space-y-6">
                                            {/* Summary Stats */}
                                            <div className="grid grid-cols-3 gap-2">
                                                <div className="p-2 bg-emerald-500/10 rounded-lg text-center border border-emerald-500/20">
                                                    <div className="text-lg font-bold text-emerald-400">{state.pack.dna_invariants.length}</div>
                                                    <div className="text-[10px] text-emerald-200/50">Rules</div>
                                                </div>
                                                <div className="p-2 bg-blue-500/10 rounded-lg text-center border border-blue-500/20">
                                                    <div className="text-lg font-bold text-blue-400">{state.pack.mutation_slots.length}</div>
                                                    <div className="text-[10px] text-blue-200/50">Slots</div>
                                                </div>
                                                <div className="p-2 bg-red-500/10 rounded-lg text-center border border-red-500/20">
                                                    <div className="text-lg font-bold text-red-400">{state.pack.forbidden_mutations.length}</div>
                                                    <div className="text-[10px] text-red-200/50">Limits</div>
                                                </div>
                                            </div>

                                            <div className="space-y-2">
                                                <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Active Invariants</h4>
                                                {state.pack.dna_invariants.slice(0, 5).map(inv => (
                                                    <div key={inv.rule_id} className="p-2 bg-white/5 rounded border border-white/5 text-xs">
                                                        <div className="text-emerald-400 font-medium mb-0.5">{inv.name}</div>
                                                        <div className="text-gray-500 truncate">{inv.description}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === 'scenes' && (
                                        <div className="space-y-4">
                                            <div className="flex items-center justify-between">
                                                <h4 className="text-xs font-bold text-gray-500 uppercase">Scene Overrides</h4>
                                                {onEditOverrides && (
                                                    <button onClick={onEditOverrides} className="text-xs text-emerald-400 hover:text-emerald-300 underline">
                                                        편집
                                                    </button>
                                                )}
                                            </div>
                                            {Object.keys(state.sceneOverrides).length === 0 ? (
                                                <div className="text-center py-6 text-xs text-gray-600 border border-dashed border-gray-700 rounded-lg">
                                                    적용된 씬별 오버라이드가 없습니다.
                                                </div>
                                            ) : (
                                                <div className="space-y-2">
                                                    {Object.entries(state.sceneOverrides).map(([sceneId, override]) => (
                                                        <div key={sceneId} className="p-2 bg-purple-500/10 border border-purple-500/20 rounded-lg flex justify-between items-center">
                                                            <span className="text-xs text-purple-300">Scene {sceneId}</span>
                                                            <span className="text-[10px] bg-purple-500/20 px-1.5 py-0.5 rounded text-purple-200">Applied</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {activeTab === 'settings' && (
                                        <div className="space-y-4">
                                            <div className="p-3 bg-white/5 rounded-lg space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs text-gray-300">위반 시 중단</span>
                                                    <div className={`w-2 h-2 rounded-full ${state.pack.policy.interrupt_on_violation ? 'bg-green-500' : 'bg-red-500'}`} />
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs text-gray-300">코칭 언어</span>
                                                    <span className="text-xs font-mono text-gray-500">{state.pack.policy.language.toUpperCase()}</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => state.reset()}
                                                className="w-full py-2 text-xs border border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/10 transition-colors"
                                            >
                                                현재 팩 연결 해제
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default CanvasDirectorPackPanel;
