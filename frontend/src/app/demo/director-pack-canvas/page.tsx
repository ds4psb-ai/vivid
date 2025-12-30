'use client';

import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import type { DirectorPack } from '@/types/director-pack';
import { DirectorPackSelector, DirectorPackBadge } from '@/components/DirectorPackSelector';
import { DirectorPackViewer } from '@/components/DirectorPackViewer';

// =============================================================================
// Page Component
// =============================================================================

export default function DirectorPackDemoPage() {
    const [selectedPack, setSelectedPack] = useState<DirectorPack | null>(null);
    const [showViewer, setShowViewer] = useState(false);
    const [simulatedResult, setSimulatedResult] = useState<{
        storyboardCount: number;
        shotContracts: Array<{
            shot_id: string;
            prompt: string;
            dna_compliance: {
                applied_rules: string[];
                confidence: number;
            };
        }>;
        dna_mode: string;
    } | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);

    const handleSelectPack = useCallback((pack: DirectorPack | null) => {
        setSelectedPack(pack);
        setSimulatedResult(null);
    }, []);

    const handleOpenEditor = useCallback(() => {
        // Navigate to SceneDNAEditor or open modal
        console.log('Open SceneDNAEditor for:', selectedPack?.meta.pack_id);
    }, [selectedPack]);

    // Simulate capsule run with DirectorPack
    const handleSimulateRun = useCallback(async () => {
        setIsGenerating(true);
        setSimulatedResult(null);

        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 2000));

        if (selectedPack) {
            // DNA-enabled result
            setSimulatedResult({
                storyboardCount: 5,
                shotContracts: [
                    {
                        shot_id: 'shot_001',
                        prompt: '봉준호 스타일의 대칭 구도, 수직 블로킹 강조, 창문을 통한 자연광, 중앙에 위치한 주인공, 35mm 렌즈, 슬로우 푸시인',
                        dna_compliance: {
                            applied_rules: ['hook_timing_2s', 'center_composition', 'vertical_blocking'],
                            confidence: 0.92,
                        },
                    },
                    {
                        shot_id: 'shot_002',
                        prompt: '계단 모티프를 활용한 상승 샷, 조명은 창문 쪽에서 들어오는 방향광, 주인공 오른쪽 1/3 배치, 깊은 포커스',
                        dna_compliance: {
                            applied_rules: ['center_composition', 'audio_clarity'],
                            confidence: 0.88,
                        },
                    },
                    {
                        shot_id: 'shot_003',
                        prompt: '와이드 에스타블리싱 샷, 상류층 집 전경, 대칭적 프레이밍, 차가운 색감의 그레이딩',
                        dna_compliance: {
                            applied_rules: ['cut_frequency', 'vertical_blocking'],
                            confidence: 0.85,
                        },
                    },
                ],
                dna_mode: 'enabled',
            });
        } else {
            // Without DNA
            setSimulatedResult({
                storyboardCount: 5,
                shotContracts: [
                    {
                        shot_id: 'shot_001',
                        prompt: 'Wide shot of a person by a window, natural light',
                        dna_compliance: { applied_rules: [], confidence: 0 },
                    },
                    {
                        shot_id: 'shot_002',
                        prompt: 'Medium shot of character walking up stairs',
                        dna_compliance: { applied_rules: [], confidence: 0 },
                    },
                    {
                        shot_id: 'shot_003',
                        prompt: 'Establishing shot of a house',
                        dna_compliance: { applied_rules: [], confidence: 0 },
                    },
                ],
                dna_mode: 'disabled',
            });
        }

        setIsGenerating(false);
    }, [selectedPack]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 py-8">
            <div className="max-w-6xl mx-auto px-4 space-y-8">
                {/* Header */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-white mb-2">
                        🧬 DirectorPack Canvas Integration
                    </h1>
                    <p className="text-gray-400">
                        다중 씬 일관성을 위한 DNA 규칙 적용 데모
                    </p>
                </div>

                {/* Main Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left: DirectorPack Selector */}
                    <div className="space-y-6">
                        <DirectorPackSelector
                            capsuleId="auteur.bong-joon-ho"
                            onSelect={handleSelectPack}
                            onOpenEditor={handleOpenEditor}
                        />

                        {/* Current Selection Badge */}
                        <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-400">현재 선택:</span>
                            <DirectorPackBadge
                                pack={selectedPack}
                                onClick={() => setShowViewer(!showViewer)}
                            />
                        </div>

                        {/* Run Button */}
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleSimulateRun}
                            disabled={isGenerating}
                            className={`w-full py-4 rounded-xl font-semibold text-lg transition-all flex items-center justify-center gap-3 ${isGenerating
                                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-emerald-500/20'
                                }`}
                        >
                            {isGenerating ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                                    생성 중...
                                </>
                            ) : (
                                <>
                                    <span>▶️</span>
                                    Shot Contracts 생성 {selectedPack ? '(DNA 적용)' : '(DNA 미적용)'}
                                </>
                            )}
                        </motion.button>
                    </div>

                    {/* Right: Results */}
                    <div className="space-y-6">
                        {simulatedResult ? (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden"
                            >
                                {/* Result Header */}
                                <div className={`p-4 ${simulatedResult.dna_mode === 'enabled'
                                    ? 'bg-gradient-to-r from-emerald-900/50 to-gray-900'
                                    : 'bg-gray-800'
                                    }`}>
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="font-bold text-white flex items-center gap-2">
                                                {simulatedResult.dna_mode === 'enabled' ? '🧬' : '⚠️'}
                                                Shot Contracts 생성 완료
                                            </h3>
                                            <p className="text-sm text-gray-400">
                                                {simulatedResult.storyboardCount} storyboard → {simulatedResult.shotContracts.length} shots
                                            </p>
                                        </div>
                                        <span className={`px-3 py-1 text-xs rounded-full ${simulatedResult.dna_mode === 'enabled'
                                            ? 'bg-emerald-500/20 text-emerald-400'
                                            : 'bg-yellow-500/20 text-yellow-400'
                                            }`}>
                                            DNA: {simulatedResult.dna_mode}
                                        </span>
                                    </div>
                                </div>

                                {/* Shot List */}
                                <div className="p-4 space-y-4">
                                    {simulatedResult.shotContracts.map((shot, idx) => (
                                        <motion.div
                                            key={shot.shot_id}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: idx * 0.1 }}
                                            className="p-4 bg-gray-800 rounded-lg"
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="font-mono text-sm text-cyan-400">{shot.shot_id}</span>
                                                {shot.dna_compliance.confidence > 0 && (
                                                    <span className="px-2 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 rounded-full">
                                                        신뢰도 {(shot.dna_compliance.confidence * 100).toFixed(0)}%
                                                    </span>
                                                )}
                                            </div>

                                            <p className="text-sm text-gray-300 mb-3">{shot.prompt}</p>

                                            {shot.dna_compliance.applied_rules.length > 0 && (
                                                <div className="flex flex-wrap gap-1">
                                                    {shot.dna_compliance.applied_rules.map((rule) => (
                                                        <span
                                                            key={rule}
                                                            className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded"
                                                        >
                                                            {rule}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </motion.div>
                                    ))}
                                </div>
                            </motion.div>
                        ) : (
                            <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center">
                                <div className="text-4xl mb-4">🎬</div>
                                <h3 className="text-lg font-semibold text-white mb-2">
                                    Shot Contracts 미리보기
                                </h3>
                                <p className="text-sm text-gray-500">
                                    DirectorPack을 선택하고 생성 버튼을 클릭하면<br />
                                    DNA 규칙이 적용된 샷 결과를 확인할 수 있습니다.
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Full DirectorPack Viewer */}
                {showViewer && selectedPack && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="flex justify-end mb-2">
                            <button
                                onClick={() => setShowViewer(false)}
                                className="text-xs text-gray-400 hover:text-white"
                            >
                                닫기 ✕
                            </button>
                        </div>
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        <DirectorPackViewer pack={selectedPack as any} />
                    </motion.div>
                )}

                {/* Integration Guide */}
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-white mb-4">📌 캔버스 통합 가이드</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="p-4 bg-gray-800 rounded-lg">
                            <div className="text-emerald-400 font-semibold mb-2">1. DirectorPack 선택</div>
                            <p className="text-gray-400">
                                캡슐 실행 전 사이드 패널에서 DirectorPack을 선택합니다.
                                기본 제공 팩을 사용하거나 캡슐에서 새로 컴파일할 수 있습니다.
                            </p>
                        </div>
                        <div className="p-4 bg-gray-800 rounded-lg">
                            <div className="text-cyan-400 font-semibold mb-2">2. 씬별 오버라이드</div>
                            <p className="text-gray-400">
                                SceneDNAEditor에서 특정 씬의 DNA 규칙을 커스터마이즈할 수 있습니다.
                                규칙 완화, 강화, 또는 커스텀 프롬프트 추가가 가능합니다.
                            </p>
                        </div>
                        <div className="p-4 bg-gray-800 rounded-lg">
                            <div className="text-purple-400 font-semibold mb-2">3. 일관된 결과</div>
                            <p className="text-gray-400">
                                모든 샷에 DNA 규칙이 적용되어 다중 씬 간 시각적 일관성을 유지합니다.
                                각 샷의 준수 여부를 dna_compliance로 확인할 수 있습니다.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
