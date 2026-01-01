'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { DirectorPack } from '@/types/director-pack';

// =============================================================================
// Types
// =============================================================================

export interface DirectorPackSelectorProps {
    capsuleId?: string;
    selectedPackId?: string | null;
    onSelect: (pack: DirectorPack | null) => void;
    onOpenEditor?: (pack: DirectorPack) => void;
    className?: string;
}

interface PackSummary {
    pack_id: string;
    pattern_id: string;
    version: string;
    compiled_at: string;
    invariant_count: number;
    slot_count: number;
    forbidden_count: number;
}

// =============================================================================
// Helper Components
// =============================================================================

const PackCard: React.FC<{
    pack: PackSummary;
    isSelected: boolean;
    onSelect: () => void;
    onEdit?: () => void;
}> = ({ pack, isSelected, onSelect, onEdit }) => {
    const patternName = pack.pattern_id.split('.').pop()?.replace(/-/g, ' ') || pack.pattern_id;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onSelect}
            className={`
        relative p-4 rounded-xl border-2 cursor-pointer transition-all
        ${isSelected
                    ? 'border-emerald-500 bg-emerald-950/30 shadow-lg shadow-emerald-500/20'
                    : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                }
      `}
        >
            {/* Selection indicator */}
            {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                    <span className="text-black text-xs">✓</span>
                </div>
            )}

            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">🧬</span>
                <div>
                    <h4 className="font-semibold text-white capitalize">{patternName}</h4>
                    <p className="text-xs text-gray-500">v{pack.version}</p>
                </div>
            </div>

            {/* Stats */}
            <div className="flex flex-wrap gap-2 mt-3">
                <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded-full">
                    {pack.invariant_count} DNA
                </span>
                <span className="px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded-full">
                    {pack.slot_count} Slots
                </span>
                <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded-full">
                    {pack.forbidden_count} 금지
                </span>
            </div>

            {/* Edit button */}
            {isSelected && onEdit && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onEdit();
                    }}
                    className="mt-3 w-full py-1.5 text-xs bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
                >
                    씬별 오버라이드 편집
                </button>
            )}
        </motion.div>
    );
};

// =============================================================================
// Main Component
// =============================================================================

export const DirectorPackSelector: React.FC<DirectorPackSelectorProps> = ({
    capsuleId,
    onSelect,
    onOpenEditor,
    className = '',
}) => {
    const [packs, setPacks] = useState<PackSummary[]>([]);
    const [selectedPack, setSelectedPack] = useState<DirectorPack | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isEnabled, setIsEnabled] = useState(false);

    // Fetch available packs
    useEffect(() => {
        const fetchPacks = async () => {
            setIsLoading(true);
            setError(null);

            try {
                const params = new URLSearchParams();
                if (capsuleId) {
                    // Extract pattern from capsule ID (e.g., auteur.bong-joon-ho -> bong)
                    const pattern = capsuleId.split('.').pop() || '';
                    params.set('pattern_id', pattern);
                }

                const response = await fetch(`/api/v1/director-packs?${params}`);
                if (!response.ok) throw new Error('Failed to fetch packs');

                const data = await response.json();
                setPacks(data.data || []);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load DirectorPacks');
                // Use mock data on error
                setPacks([
                    {
                        pack_id: 'dp_bong_default',
                        pattern_id: 'auteur.bong-joon-ho',
                        version: '1.0.0',
                        compiled_at: new Date().toISOString(),
                        invariant_count: 5,
                        slot_count: 4,
                        forbidden_count: 3,
                    },
                ]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchPacks();
    }, [capsuleId]);

    // Handle pack selection
    const handleSelect = useCallback(async (packSummary: PackSummary) => {
        try {
            const response = await fetch(`/api/v1/director-packs/${packSummary.pack_id}`);
            if (!response.ok) throw new Error('Failed to fetch pack details');

            const data = await response.json();
            setSelectedPack(data.data);
            onSelect(data.data);
        } catch {
            // Use mock data on error
            const mockPack: DirectorPack = {
                meta: {
                    pack_id: packSummary.pack_id,
                    pattern_id: packSummary.pattern_id,
                    version: packSummary.version,
                    compiled_at: packSummary.compiled_at,
                    invariant_count: packSummary.invariant_count,
                    slot_count: packSummary.slot_count,
                    forbidden_count: packSummary.forbidden_count,
                    checkpoint_count: 6,
                },
                dna_invariants: [],
                mutation_slots: [],
                forbidden_mutations: [],
                checkpoints: [],
                policy: { interrupt_on_violation: false, suggest_on_medium: true, language: 'ko' },
                runtime_contract: { max_session_sec: 180, checkpoint_interval_sec: 30, enable_realtime_feedback: false, enable_audio_coach: false },
            };
            setSelectedPack(mockPack);
            onSelect(mockPack);
        }
    }, [onSelect]);

    // Handle clear selection
    const handleClear = useCallback(() => {
        setSelectedPack(null);
        onSelect(null);
    }, [onSelect]);

    // Toggle enable/disable
    const handleToggle = useCallback(() => {
        const newEnabled = !isEnabled;
        setIsEnabled(newEnabled);
        if (!newEnabled) {
            handleClear();
        }
    }, [isEnabled, handleClear]);

    return (
        <div className={`bg-gray-900 rounded-xl border border-gray-800 overflow-hidden ${className}`}>
            {/* Header */}
            <div className="p-4 bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-800">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">🧬</span>
                        <div>
                            <h3 className="text-lg font-bold text-white">DirectorPack DNA</h3>
                            <p className="text-xs text-gray-500">다중 씬 일관성 규칙</p>
                        </div>
                    </div>

                    {/* Enable toggle */}
                    <button
                        onClick={handleToggle}
                        className={`w-12 h-6 rounded-full transition-colors relative ${isEnabled ? 'bg-emerald-500' : 'bg-gray-600'
                            }`}
                    >
                        <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform ${isEnabled ? 'translate-x-6' : 'translate-x-0.5'
                            }`} />
                    </button>
                </div>
            </div>

            {/* Content */}
            <AnimatePresence mode="wait">
                {isEnabled ? (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-4">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-8">
                                    <div className="animate-spin w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full" />
                                </div>
                            ) : error && packs.length === 0 ? (
                                <div className="text-center py-8 text-gray-500">
                                    <p>{error}</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {packs.map((pack) => (
                                        <PackCard
                                            key={pack.pack_id}
                                            pack={pack}
                                            isSelected={selectedPack?.meta.pack_id === pack.pack_id}
                                            onSelect={() => handleSelect(pack)}
                                            onEdit={selectedPack && onOpenEditor ? () => onOpenEditor(selectedPack) : undefined}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* Selected pack info */}
                            {selectedPack && (
                                <div className="mt-4 p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <div className="text-sm text-emerald-400">
                                            <span className="font-semibold">적용됨:</span> {selectedPack.meta.pack_id}
                                        </div>
                                        <button
                                            onClick={handleClear}
                                            className="text-xs text-gray-400 hover:text-red-400"
                                        >
                                            해제
                                        </button>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        이 팩의 DNA 규칙이 모든 샷 생성에 적용됩니다.
                                    </p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="p-4 text-center"
                    >
                        <p className="text-sm text-gray-500">
                            DirectorPack을 활성화하면 다중 씬 간 일관성을 유지할 수 있습니다.
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// =============================================================================
// Compact Variant
// =============================================================================

export const DirectorPackBadge: React.FC<{
    pack: DirectorPack | null;
    onClick?: () => void;
}> = ({ pack, onClick }) => {
    if (!pack) {
        return (
            <button
                onClick={onClick}
                className="px-3 py-1.5 text-xs bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 transition-colors flex items-center gap-2"
            >
                <span>🧬</span>
                <span>DNA 미적용</span>
            </button>
        );
    }

    const patternName = pack.meta.pattern_id.split('.').pop()?.replace(/-/g, ' ') || '';

    return (
        <button
            onClick={onClick}
            className="px-3 py-1.5 text-xs bg-emerald-950/50 border border-emerald-500/30 text-emerald-400 rounded-lg hover:bg-emerald-950 transition-colors flex items-center gap-2"
        >
            <span>🧬</span>
            <span className="capitalize">{patternName}</span>
            <span className="text-emerald-500/50">v{pack.meta.version}</span>
        </button>
    );
};

export default DirectorPackSelector;
