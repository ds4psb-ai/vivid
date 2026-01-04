"use client";

import { useState, forwardRef, useImperativeHandle } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrainCar } from "./TrainCar";
import { ConnectionSelector } from "./ConnectionSelector";
import { Trash2 } from "lucide-react";

// =============================================================================
// Types
// =============================================================================

interface Car {
    id: string;
    order: number;
    toolId: string;
    displayName: string;
    icon: string;
    color: string;
    status: "pending" | "ready" | "executing" | "completed" | "failed";
    inputs: Record<string, unknown>;
    output?: Record<string, unknown>;
}

interface ConnectionOption {
    id: string;
    label: string;
    description: string;
    recommendedToolId: string;
    icon: string;
    color: string;
    confidence: number;
}

export interface TrainWorkflowHandle {
    executeAll: () => Promise<void>;
    reset: () => void;
    // Agent integration methods
    addCar: (car: Omit<Car, "id" | "order">) => string; // Returns new car ID
    updateCarStatus: (carId: string, status: Car["status"], output?: Record<string, unknown>) => void;
    clearCars: () => void;
    getCars: () => Car[];
}

interface TrainWorkflowViewProps {
    sessionId?: string;
    initialRequest?: string;
    onComplete?: (results: Record<string, unknown>[]) => void;
}

// =============================================================================
// Mock Data (API 연동 전 테스트용)
// =============================================================================

const MOCK_INITIAL_CAR: Car = {
    id: "car-1",
    order: 0,
    toolId: "prompt_generator",
    displayName: "Veo 프롬프트 생성기",
    icon: "sparkles",
    color: "violet",
    status: "ready",
    inputs: { topic: "2분짜리 요리 브이로그" },
};

const MOCK_CONNECTION_OPTIONS: ConnectionOption[] = [
    {
        id: "opt-1",
        label: "2차원으로 확장",
        description: "스토리보드 구조로 입체화",
        recommendedToolId: "storyboard",
        icon: "layout-grid",
        color: "emerald",
        confidence: 0.92,
    },
    {
        id: "opt-2",
        label: "바로 3차원으로",
        description: "즉시 이미지로 시각화",
        recommendedToolId: "image_tool",
        icon: "image",
        color: "amber",
        confidence: 0.78,
    },
    {
        id: "opt-3",
        label: "레퍼런스 차원 탐색",
        description: "참고 영상 스타일 분석",
        recommendedToolId: "reference_analyzer",
        icon: "film",
        color: "cyan",
        confidence: 0.65,
    },
];

const TOOL_INFO: Record<string, { displayName: string; icon: string; color: string }> = {
    prompt_generator: { displayName: "Veo 프롬프트 생성기", icon: "sparkles", color: "violet" },
    storyboard: { displayName: "스토리보드 생성기", icon: "layout-grid", color: "emerald" },
    image_tool: { displayName: "이미지 프롬프트 생성기", icon: "image", color: "amber" },
    reference_analyzer: { displayName: "레퍼런스 분석기", icon: "film", color: "cyan" },
};

// 차원 레이블
const DIMENSION_LABELS = ["1D", "2D", "3D", "4D", "5D"];

// =============================================================================
// Component
// =============================================================================

export const TrainWorkflowView = forwardRef<TrainWorkflowHandle, TrainWorkflowViewProps>(
    ({ sessionId, initialRequest, onComplete }, ref) => {
        const [cars, setCars] = useState<Car[]>([MOCK_INITIAL_CAR]);
        const [pendingConnections, setPendingConnections] = useState<ConnectionOption[]>(MOCK_CONNECTION_OPTIONS);
        const [isLoadingOptions, setIsLoadingOptions] = useState(false);
        const [activeCarIndex, setActiveCarIndex] = useState(0);

        // 노드 실행 핸들러
        const handleExecuteCar = async (carId: string) => {
            const carIndex = cars.findIndex((c) => c.id === carId);
            if (carIndex === -1) return;

            setCars((prev) =>
                prev.map((car) =>
                    car.id === carId ? { ...car, status: "executing" } : car
                )
            );

            // Mock: 실행 시뮬레이션
            await new Promise((resolve) => setTimeout(resolve, 1500));

            setCars((prev) =>
                prev.map((car) =>
                    car.id === carId
                        ? { ...car, status: "completed", output: { result: "생성 완료" } }
                        : car
                )
            );

            // 다음 노드 활성화
            if (carIndex < cars.length - 1) {
                setCars((prev) =>
                    prev.map((car, i) =>
                        i === carIndex + 1 ? { ...car, status: "ready" } : car
                    )
                );
                setActiveCarIndex(carIndex + 1);
            }
        };

        // 전체 실행 핸들러
        const handleExecuteAll = async () => {
            for (const car of cars) {
                if (car.status !== "completed") {
                    await handleExecuteCar(car.id);
                }
            }
            onComplete?.(cars.map((c) => c.output || {}));
        };

        // Expose methods to parent
        useImperativeHandle(ref, () => ({
            executeAll: handleExecuteAll,
            reset: () => setCars([MOCK_INITIAL_CAR]),

            // Agent integration methods
            addCar: (carData: Omit<Car, "id" | "order">) => {
                const newId = `agent-car-${Date.now()}`;
                const newCar: Car = {
                    ...carData,
                    id: newId,
                    order: cars.length,
                };
                setCars((prev) => [...prev, newCar]);
                setActiveCarIndex(cars.length);
                setPendingConnections([]); // Hide manual selector when agent is adding cars
                return newId;
            },

            updateCarStatus: (carId: string, status: Car["status"], output?: Record<string, unknown>) => {
                setCars((prev) =>
                    prev.map((car) =>
                        car.id === carId
                            ? { ...car, status, ...(output ? { output } : {}) }
                            : car
                    )
                );
            },

            clearCars: () => {
                setCars([]);
                setActiveCarIndex(0);
                setPendingConnections(MOCK_CONNECTION_OPTIONS);
            },

            getCars: () => cars,
        }), [cars, handleExecuteAll]);

        // 연결 옵션 선택 핸들러
        const handleSelectConnection = async (optionId: string) => {
            const selectedOption = pendingConnections.find((opt) => opt.id === optionId);
            if (!selectedOption) return;

            const toolInfo = TOOL_INFO[selectedOption.recommendedToolId];
            const newCar: Car = {
                id: `car-${cars.length + 1}`,
                order: cars.length,
                toolId: selectedOption.recommendedToolId,
                displayName: toolInfo.displayName,
                icon: toolInfo.icon,
                color: toolInfo.color,
                status: "pending",
                inputs: {},
            };

            setCars((prev) => [...prev, newCar]);
            setActiveCarIndex(cars.length);

            // 다음 연결 옵션 로드 (실제로는 API 호출)
            setIsLoadingOptions(true);
            await new Promise((resolve) => setTimeout(resolve, 800));

            // Mock: 다음 옵션 생성
            const nextOptions = MOCK_CONNECTION_OPTIONS.filter(
                (opt) => opt.recommendedToolId !== selectedOption.recommendedToolId
            ).slice(0, 3);

            setPendingConnections(nextOptions);
            setIsLoadingOptions(false);
        };

        // 노드 삭제 핸들러
        const handleDeleteCar = (carId: string) => {
            const carIndex = cars.findIndex((c) => c.id === carId);
            if (carIndex <= 0) return; // 첫 번째 노드는 삭제 불가

            setCars((prev) => prev.filter((c) => c.id !== carId));
            setActiveCarIndex(Math.min(activeCarIndex, cars.length - 2));
        };

        return (
            <div className="w-full min-h-[400px] p-8">
                {/* 헤더 */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h2 className="text-xl font-bold text-white">차원 확장 워크플로우</h2>
                        <p className="text-sm text-zinc-500 mt-1">
                            차원문을 선택하여 아이디어를 확장하세요
                        </p>
                    </div>
                </div>

                {/* 차원 트랙 */}
                <div className="relative">
                    {/* 차원 연결선 */}
                    <div className="absolute top-[120px] left-0 right-0 h-1 bg-gradient-to-r from-violet-500/30 via-emerald-500/30 to-amber-500/30 rounded-full" />
                    <div className="absolute top-[125px] left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-zinc-600 to-transparent rounded-full" />

                    {/* 차원 노드들 + 차원문 */}
                    <div className="flex items-start gap-4 overflow-x-auto pb-8 pt-4">
                        <AnimatePresence>
                            {cars.map((car, index) => (
                                <div key={car.id} className="flex items-start gap-4">
                                    {/* 차원 노드 */}
                                    <div className="relative">
                                        {/* 차원 레이블 */}
                                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-gradient-to-r from-violet-500/20 to-purple-500/20 border border-violet-500/30 text-xs font-bold text-violet-400">
                                            {DIMENSION_LABELS[index] || `${index + 1}D`}
                                        </div>

                                        <TrainCar
                                            {...car}
                                            isActive={index === activeCarIndex}
                                            onExecute={
                                                car.status === "ready"
                                                    ? () => handleExecuteCar(car.id)
                                                    : undefined
                                            }
                                        />

                                        {/* 삭제 버튼 (첫 번째 노드 제외) */}
                                        {index > 0 && car.status !== "executing" && (
                                            <button
                                                onClick={() => handleDeleteCar(car.id)}
                                                className="absolute -top-1 -right-1 h-6 w-6 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center text-red-400 hover:bg-red-500/30 transition-all opacity-0 group-hover:opacity-100"
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </button>
                                        )}
                                    </div>

                                    {/* 차원문 (마지막 노드 후에만 표시) */}
                                    {index === cars.length - 1 && pendingConnections.length > 0 && (
                                        <ConnectionSelector
                                            options={pendingConnections}
                                            onSelect={handleSelectConnection}
                                            onReRecommend={() => {
                                                setIsLoadingOptions(true);
                                                setTimeout(() => {
                                                    setPendingConnections(MOCK_CONNECTION_OPTIONS);
                                                    setIsLoadingOptions(false);
                                                }, 500);
                                            }}
                                            isLoading={isLoadingOptions}
                                        />
                                    )}
                                </div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>

                {/* 요약 패널 */}
                <div className="mt-8 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-6">
                            <div>
                                <span className="text-[10px] text-zinc-500 uppercase tracking-widest">
                                    현재 차원
                                </span>
                                <p className="text-lg font-bold text-white">{DIMENSION_LABELS[cars.length - 1] || `${cars.length}D`}</p>
                            </div>
                            <div>
                                <span className="text-[10px] text-zinc-500 uppercase tracking-widest">
                                    완료됨
                                </span>
                                <p className="text-lg font-bold text-emerald-400">
                                    {cars.filter((c) => c.status === "completed").length}
                                </p>
                            </div>
                            <div>
                                <span className="text-[10px] text-zinc-500 uppercase tracking-widest">
                                    예상 크레딧
                                </span>
                                <p className="text-lg font-bold text-amber-400">
                                    {cars.length * 10}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {cars.map((car, i) => (
                                <div
                                    key={car.id}
                                    className={`
                                    h-2 w-8 rounded-full transition-all
                                    ${car.status === "completed" ? "bg-emerald-500" : ""}
                                    ${car.status === "executing" ? "bg-amber-500 animate-pulse" : ""}
                                    ${car.status === "ready" ? "bg-blue-500" : ""}
                                    ${car.status === "pending" ? "bg-zinc-700" : ""}
                                    ${car.status === "failed" ? "bg-red-500" : ""}
                                `}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }
);

TrainWorkflowView.displayName = "TrainWorkflowView";
