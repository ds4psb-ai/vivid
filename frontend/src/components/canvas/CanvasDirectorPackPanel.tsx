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
        <div className={`bg-gray-900/90 backdrop-blur-md rounded-lg border border-gray-700 overflow-hidden shadow-lg ${className}`}>
            {/* Header - Always Visible */}
            <div
                onClick={handleToggleCollapse}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleToggleCollapse();
                    }
                }}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-800/50 transition-colors cursor-pointer"
                role="button"
                tabIndex={0}
                aria-expanded={!isCollapsed}
                aria-controls="director-pack-panel-content"
            >
                <div className="flex items-center gap-2">
                    <span className="text-lg" role="img" aria-label="DNA">🧬</span>
                    <span className="text-sm font-medium text-white">DirectorPack</span>
                    {state.isEnabled && state.pack && (
                        <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full capitalize">
                            {patternName}
                        </span>
                    )}
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
                        role="switch"
                        aria-checked={state.isEnabled}
                    >
                        <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${state.isEnabled ? 'translate-x-5' : 'translate-x-0.5'
                            }`} />
                    </button>
                    {isCollapsed ? (
                        <ChevronDown size={16} className="text-gray-400" />
                    ) : (
                        <ChevronUp size={16} className="text-gray-400" />
                    )}
                </div>
            </div>

            {/* Expanded Content */}
            <AnimatePresence>
                {!isCollapsed && (
                    <motion.div
                        id="director-pack-panel-content"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="p-3 pt-0 space-y-3">
                            {/* Disabled State */}
                            {!state.isEnabled ? (
                                <div className="text-center py-4">
                                    <div className="text-2xl mb-2">🎬</div>
                                    <p className="text-xs text-gray-500">
                                        DNA 모드를 활성화하면<br />
                                        다중 씬 간 일관성을 유지할 수 있습니다.
                                    </p>
                                    <button
                                        onClick={() => state.setEnabled(true)}
                                        className="mt-3 px-4 py-1.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors"
                                    >
                                        DNA 모드 활성화
                                    </button>
                                </div>
                            ) : (
                                <>
                                    {/* Loading State */}
                                    {state.isLoading && (
                                        <div className="flex items-center justify-center py-4 gap-2">
                                            <div className="animate-spin w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full" />
                                            <span className="text-xs text-gray-400">로딩 중...</span>
                                        </div>
                                    )}

                                    {/* Error State */}
                                    {state.error && (
                                        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                                            <div className="flex items-center gap-2 text-red-400 mb-2">
                                                <AlertCircle size={14} />
                                                <span className="text-xs font-medium">오류</span>
                                            </div>
                                            <p className="text-xs text-red-300 mb-2">{state.error}</p>
                                            <button
                                                onClick={() => {
                                                    state.clearError();
                                                    handleRefresh();
                                                }}
                                                className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300"
                                            >
                                                <RefreshCw size={12} />
                                                다시 시도
                                            </button>
                                        </div>
                                    )}

                                    {/* Pack List */}
                                    {!state.isLoading && !state.error && state.availablePacks.length > 0 && (
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                                                <span>사용 가능한 팩</span>
                                                <button
                                                    onClick={handleRefresh}
                                                    className="hover:text-gray-400"
                                                    title="새로고침"
                                                >
                                                    <RefreshCw size={12} />
                                                </button>
                                            </div>
                                            {state.availablePacks.map((pack) => (
                                                <button
                                                    key={pack.pack_id}
                                                    onClick={() => handleSelectPack(pack.pack_id)}
                                                    disabled={state.isLoading}
                                                    className={`w-full p-2.5 rounded-lg text-left transition-all ${state.pack?.meta.pack_id === pack.pack_id
                                                        ? 'bg-emerald-500/20 border border-emerald-500/50 ring-1 ring-emerald-500/20'
                                                        : 'bg-gray-800 border border-gray-700 hover:border-gray-600 hover:bg-gray-750'
                                                        }`}
                                                >
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-sm text-white capitalize font-medium">
                                                            {pack.pattern_id.split('.').pop()?.replace(/-/g, ' ')}
                                                        </span>
                                                        {state.pack?.meta.pack_id === pack.pack_id && (
                                                            <Zap size={14} className="text-emerald-400" />
                                                        )}
                                                    </div>
                                                    <div className="flex gap-3 text-xs">
                                                        <span className="text-blue-400">🧬 {pack.invariant_count}</span>
                                                        <span className="text-purple-400">🎛️ {pack.slot_count}</span>
                                                        <span className="text-red-400">🚫 {pack.forbidden_count}</span>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    {/* Empty State */}
                                    {!state.isLoading && !state.error && state.availablePacks.length === 0 && (
                                        <div className="text-center py-4">
                                            <p className="text-xs text-gray-500 mb-2">
                                                사용 가능한 팩이 없습니다
                                            </p>
                                            <button
                                                onClick={handleRefresh}
                                                className="text-xs text-gray-400 hover:text-white flex items-center gap-1 mx-auto"
                                            >
                                                <RefreshCw size={12} />
                                                새로고침
                                            </button>
                                        </div>
                                    )}

                                    {/* Selected Pack Details */}
                                    {state.pack && (
                                        <div className="p-3 bg-gradient-to-r from-emerald-950/50 to-gray-900 border border-emerald-500/30 rounded-lg">
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                                                    <Zap size={12} />
                                                    적용 중
                                                </span>
                                                <span className="text-xs text-gray-500">v{state.pack.meta.version}</span>
                                            </div>

                                            {/* Rule Summary */}
                                            <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                                                <div className="p-2 bg-gray-800/50 rounded">
                                                    <span className="text-gray-400">DNA 규칙</span>
                                                    <span className="block text-white font-medium">
                                                        {state.pack.dna_invariants.length}개
                                                    </span>
                                                </div>
                                                <div className="p-2 bg-gray-800/50 rounded">
                                                    <span className="text-gray-400">체크포인트</span>
                                                    <span className="block text-white font-medium">
                                                        {state.pack.checkpoints.length}개
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Scene Overrides Info */}
                                            {Object.keys(state.sceneOverrides).length > 0 && (
                                                <div className="text-xs text-purple-400 mb-2">
                                                    🎨 {Object.keys(state.sceneOverrides).length}개 씬 오버라이드 적용됨
                                                </div>
                                            )}

                                            {/* Edit Overrides Button */}
                                            {onEditOverrides && (
                                                <button
                                                    onClick={onEditOverrides}
                                                    className="w-full py-2 flex items-center justify-center gap-1.5 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
                                                >
                                                    <Settings size={12} />
                                                    씬별 오버라이드 편집
                                                </button>
                                            )}
                                        </div>
                                    )}

                                    {/* Clear Button */}
                                    {state.pack && (
                                        <button
                                            onClick={() => state.reset()}
                                            className="w-full py-1.5 text-xs text-gray-500 hover:text-red-400 transition-colors"
                                        >
                                            팩 해제
                                        </button>
                                    )}
                                </>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default CanvasDirectorPackPanel;
