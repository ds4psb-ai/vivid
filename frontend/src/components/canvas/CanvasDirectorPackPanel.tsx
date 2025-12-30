'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Settings, Zap } from 'lucide-react';
import type { DirectorPack } from '@/types/director-pack';
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

interface PackSummary {
    pack_id: string;
    pattern_id: string;
    version: string;
    invariant_count: number;
    slot_count: number;
    forbidden_count: number;
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
    const [availablePacks, setAvailablePacks] = useState<PackSummary[]>([]);
    const [packsLoaded, setPacksLoaded] = useState(false);

    // Load available packs when expanded
    const handleToggleCollapse = useCallback(async () => {
        const willExpand = isCollapsed;
        setIsCollapsed(!isCollapsed);

        if (willExpand && !packsLoaded) {
            try {
                const params = new URLSearchParams();
                if (capsuleId) {
                    const pattern = capsuleId.split('.').pop() || '';
                    if (pattern) params.set('pattern_id', pattern);
                }

                const response = await fetch(`/api/v1/director-packs?${params}`);
                if (response.ok) {
                    const data = await response.json();
                    setAvailablePacks(data.data || []);
                }
            } catch {
                // Use mock data on error
                setAvailablePacks([{
                    pack_id: 'dp_bong_default',
                    pattern_id: 'auteur.bong-joon-ho',
                    version: '1.0.0',
                    invariant_count: 5,
                    slot_count: 4,
                    forbidden_count: 3,
                }]);
            }
            setPacksLoaded(true);
        }
    }, [isCollapsed, packsLoaded, capsuleId]);

    // Handle pack selection
    const handleSelectPack = useCallback(async (packSummary: PackSummary) => {
        await state.loadPackById(packSummary.pack_id);
    }, [state]);

    const patternName = state.pack?.meta.pattern_id.split('.').pop()?.replace(/-/g, ' ') || '';

    return (
        <div className={`bg-gray-900/80 backdrop-blur-sm rounded-lg border border-gray-700 overflow-hidden ${className}`}>
            {/* Header - Always Visible */}
            <button
                onClick={handleToggleCollapse}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-800/50 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <span className="text-lg">🧬</span>
                    <span className="text-sm font-medium text-white">DirectorPack</span>
                    {state.isEnabled && state.pack && (
                        <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full">
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
                        className={`w-8 h-4 rounded-full transition-colors relative ${state.isEnabled ? 'bg-emerald-500' : 'bg-gray-600'
                            }`}
                    >
                        <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-transform ${state.isEnabled ? 'translate-x-4' : 'translate-x-0.5'
                            }`} />
                    </button>
                    {isCollapsed ? (
                        <ChevronDown size={16} className="text-gray-400" />
                    ) : (
                        <ChevronUp size={16} className="text-gray-400" />
                    )}
                </div>
            </button>

            {/* Expanded Content */}
            <AnimatePresence>
                {!isCollapsed && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-3 pt-0 space-y-3">
                            {/* Status Message */}
                            {!state.isEnabled ? (
                                <p className="text-xs text-gray-500 py-2">
                                    DNA 모드를 활성화하면 다중 씬 간 일관성을 유지할 수 있습니다.
                                </p>
                            ) : (
                                <>
                                    {/* Loading State */}
                                    {state.isLoading && (
                                        <div className="flex items-center justify-center py-4">
                                            <div className="animate-spin w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full" />
                                        </div>
                                    )}

                                    {/* Error State */}
                                    {state.error && (
                                        <div className="p-2 bg-red-500/10 border border-red-500/30 rounded text-xs text-red-400">
                                            {state.error}
                                        </div>
                                    )}

                                    {/* Pack List */}
                                    {!state.isLoading && availablePacks.length > 0 && (
                                        <div className="space-y-2">
                                            {availablePacks.map((pack) => (
                                                <button
                                                    key={pack.pack_id}
                                                    onClick={() => handleSelectPack(pack)}
                                                    className={`w-full p-2 rounded-lg text-left transition-all ${state.pack?.meta.pack_id === pack.pack_id
                                                            ? 'bg-emerald-500/20 border border-emerald-500/50'
                                                            : 'bg-gray-800 border border-gray-700 hover:border-gray-600'
                                                        }`}
                                                >
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="text-sm text-white capitalize">
                                                            {pack.pattern_id.split('.').pop()?.replace(/-/g, ' ')}
                                                        </span>
                                                        {state.pack?.meta.pack_id === pack.pack_id && (
                                                            <Zap size={12} className="text-emerald-400" />
                                                        )}
                                                    </div>
                                                    <div className="flex gap-2 text-xs">
                                                        <span className="text-blue-400">{pack.invariant_count} DNA</span>
                                                        <span className="text-purple-400">{pack.slot_count} Slots</span>
                                                        <span className="text-red-400">{pack.forbidden_count} 금지</span>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    )}

                                    {/* Selected Pack Info */}
                                    {state.pack && (
                                        <div className="p-2 bg-emerald-950/30 border border-emerald-500/30 rounded-lg">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-xs text-emerald-400 font-medium">적용됨</span>
                                                <span className="text-xs text-gray-500">v{state.pack.meta.version}</span>
                                            </div>
                                            <div className="flex gap-2 text-xs text-gray-400">
                                                <span>{state.pack.dna_invariants.length} 규칙</span>
                                                <span>·</span>
                                                <span>{state.pack.checkpoints.length} 체크포인트</span>
                                            </div>

                                            {/* Edit Overrides Button */}
                                            {onEditOverrides && (
                                                <button
                                                    onClick={onEditOverrides}
                                                    className="mt-2 w-full py-1.5 flex items-center justify-center gap-1 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition-colors"
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
                                            onClick={() => state.selectPack(null)}
                                            className="w-full py-1.5 text-xs text-gray-400 hover:text-red-400 transition-colors"
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
