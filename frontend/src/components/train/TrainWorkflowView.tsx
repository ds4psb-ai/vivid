"use client";

import { useState, forwardRef, useImperativeHandle, useCallback, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { TrainCar } from "./TrainCar";
import { ConnectionSelector } from "./ConnectionSelector";
import { Trash2, CheckCircle, XCircle } from "lucide-react";
import { api, DimensionResponse } from "@/lib/api";

// =============================================================================
// Types
// =============================================================================

interface Car {
    id: string;
    order: number;
    toolId: string;
    dimension: "1D" | "2D" | "3D" | "4D";
    displayName: string;
    icon: string;
    color: string;
    status: "pending" | "ready" | "executing" | "completed" | "failed";
    inputs: Record<string, unknown>;
    output?: Record<string, unknown>;
    error?: string;
    creditCost?: number;
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
// Dimension Tool Definitions (SSoT)
// =============================================================================

// Credit costs from dimension_capsules.py (gemini-3-flash-preview tier)
const DIMENSION_CREDIT_COSTS: Record<string, number> = {
    prompt_generator: 5,   // 1D
    storyboard: 10,        // 2D
    image_tool: 10,        // 3D
    reference_analyzer: 10, // 4D
};

const INITIAL_CAR: Car = {
    id: "car-1",
    order: 0,
    toolId: "prompt_generator",
    dimension: "1D",
    displayName: "Veo 프롬프트 생성기",
    icon: "sparkles",
    color: "violet",
    status: "ready",
    inputs: {},
    creditCost: DIMENSION_CREDIT_COSTS["prompt_generator"],
};

// Connection options based on dimension progression
const CONNECTION_OPTIONS: ConnectionOption[] = [
    {
        id: "opt-2d",
        label: "2차원으로 확장",
        description: "스토리보드 구조로 입체화",
        recommendedToolId: "storyboard",
        icon: "layout-grid",
        color: "emerald",
        confidence: 0.95,
    },
    {
        id: "opt-3d",
        label: "3차원으로",
        description: "이미지 프롬프트로 시각화",
        recommendedToolId: "image_tool",
        icon: "image",
        color: "amber",
        confidence: 0.85,
    },
    {
        id: "opt-4d",
        label: "레퍼런스 차원 탐색",
        description: "참고 영상 스타일 분석",
        recommendedToolId: "reference_analyzer",
        icon: "film",
        color: "cyan",
        confidence: 0.75,
    },
];

const TOOL_INFO: Record<string, { displayName: string; icon: string; color: string; dimension: "1D" | "2D" | "3D" | "4D" }> = {
    prompt_generator: { displayName: "Veo 프롬프트 생성기", icon: "sparkles", color: "violet", dimension: "1D" },
    storyboard: { displayName: "스토리보드 생성기", icon: "layout-grid", color: "emerald", dimension: "2D" },
    image_tool: { displayName: "이미지 프롬프트 생성기", icon: "image", color: "amber", dimension: "3D" },
    reference_analyzer: { displayName: "레퍼런스 분석기", icon: "film", color: "cyan", dimension: "4D" },
};

// 차원 레이블
const DIMENSION_LABELS = ["1D", "2D", "3D", "4D", "5D"];

// =============================================================================
// Component
// =============================================================================

// =============================================================================
// Input Validation
// =============================================================================

function validateInputs(dimension: "1D" | "2D" | "3D" | "4D", inputs: Record<string, unknown>): { valid: boolean; error?: string } {
    switch (dimension) {
        case "1D": {
            const topic = String(inputs.topic || "").trim();
            if (!topic || topic.length < 2) {
                return { valid: false, error: "주제를 2자 이상 입력해주세요" };
            }
            return { valid: true };
        }
        case "2D": {
            const concept = String(inputs.concept || inputs.topic || "").trim();
            if (!concept || concept.length < 2) {
                return { valid: false, error: "컨셉을 2자 이상 입력해주세요" };
            }
            return { valid: true };
        }
        case "3D": {
            const description = String(inputs.description || "").trim();
            if (!description || description.length < 2) {
                return { valid: false, error: "설명을 2자 이상 입력해주세요" };
            }
            return { valid: true };
        }
        case "4D": {
            const videoDesc = String(inputs.video_description || inputs.description || "").trim();
            if (!videoDesc || videoDesc.length < 2) {
                return { valid: false, error: "영상 설명을 2자 이상 입력해주세요" };
            }
            return { valid: true };
        }
        default:
            return { valid: true };
    }
}

// =============================================================================
// Component
// =============================================================================

export const TrainWorkflowView = forwardRef<TrainWorkflowHandle, TrainWorkflowViewProps>(
    ({ onComplete }, ref) => {
        const [cars, setCars] = useState<Car[]>([INITIAL_CAR]);
        const [pendingConnections, setPendingConnections] = useState<ConnectionOption[]>(CONNECTION_OPTIONS);
        const [isLoadingOptions, setIsLoadingOptions] = useState(false);
        const [activeCarIndex, setActiveCarIndex] = useState(0);
        const [isExecutingAll, setIsExecutingAll] = useState(false);
        const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

        // Track executing cars to prevent double-click
        const executingCarsRef = useRef<Set<string>>(new Set());

        // Auto-dismiss notification
        const showNotification = useCallback((type: "success" | "error", message: string) => {
            setNotification({ type, message });
            setTimeout(() => setNotification(null), 3000);
        }, []);

        // Output → Input 체이닝: 이전 노드 출력을 다음 노드 입력으로 변환
        const prepareInputsFromPreviousOutput = useCallback(
            (dimension: "1D" | "2D" | "3D" | "4D", prevOutput: Record<string, unknown> | undefined, baseInputs: Record<string, unknown>) => {
                if (!prevOutput) return baseInputs;

                switch (dimension) {
                    case "2D":
                        // 1D output의 prompt를 2D의 concept으로 사용
                        return {
                            ...baseInputs,
                            concept: prevOutput.prompt || prevOutput.veo_prompt || baseInputs.concept || baseInputs.topic,
                            prompt: prevOutput.prompt || prevOutput.veo_prompt,
                        };
                    case "3D":
                        // 2D output의 scenes를 3D description으로 사용
                        if (prevOutput.scenes && Array.isArray(prevOutput.scenes)) {
                            const firstScene = prevOutput.scenes[0] as Record<string, unknown> | undefined;
                            return {
                                ...baseInputs,
                                description: firstScene?.description || firstScene?.visual || baseInputs.description,
                            };
                        }
                        return {
                            ...baseInputs,
                            description: prevOutput.prompt || prevOutput.concept || baseInputs.description,
                        };
                    case "4D":
                        // 이전 output을 video_description으로 사용
                        return {
                            ...baseInputs,
                            video_description: prevOutput.prompt || prevOutput.description || baseInputs.video_description,
                        };
                    default:
                        return baseInputs;
                }
            },
            []
        );

        // 노드 실행 핸들러 - 실제 API 호출 (하드닝 적용)
        const handleExecuteCar = async (carId: string) => {
            // [TIER1] 중복 실행 방지
            if (executingCarsRef.current.has(carId)) {
                console.warn(`Car ${carId} is already executing, ignoring duplicate call`);
                return;
            }

            const carIndex = cars.findIndex((c) => c.id === carId);
            if (carIndex === -1) return;

            const car = cars[carIndex];

            // 이전 노드의 output을 가져와서 inputs 준비
            const prevCar = carIndex > 0 ? cars[carIndex - 1] : undefined;
            const preparedInputs = prepareInputsFromPreviousOutput(
                car.dimension,
                prevCar?.output,
                car.inputs
            );

            // [TIER1] 입력 검증
            const validation = validateInputs(car.dimension, preparedInputs);
            if (!validation.valid) {
                setCars((prev) =>
                    prev.map((c) =>
                        c.id === carId
                            ? { ...c, status: "failed", error: validation.error }
                            : c
                    )
                );
                showNotification("error", validation.error || "입력 검증 실패");
                return;
            }

            // 실행 시작 마킹
            executingCarsRef.current.add(carId);

            // executing 상태로 변경
            setCars((prev) =>
                prev.map((c) =>
                    c.id === carId ? { ...c, status: "executing", error: undefined } : c
                )
            );

            try {
                // 실제 Dimension API 호출
                const response: DimensionResponse = await api.executeDimension(
                    car.dimension,
                    preparedInputs
                );

                if (response.success) {
                    // 성공: output 저장 및 상태 업데이트
                    // creditCost: API 응답에서 가져오거나 차원별 기본값 사용
                    const actualCreditCost = response.metrics?.credit_cost
                        ?? DIMENSION_CREDIT_COSTS[car.toolId]
                        ?? 10;

                    setCars((prev) =>
                        prev.map((c) =>
                            c.id === carId
                                ? {
                                    ...c,
                                    status: "completed",
                                    output: response.output,
                                    creditCost: actualCreditCost,
                                }
                                : c
                        )
                    );

                    // [TIER2] 성공 피드백
                    showNotification("success", `${car.displayName} 완료!`);

                    // 다음 노드 활성화
                    if (carIndex < cars.length - 1) {
                        setCars((prev) =>
                            prev.map((c, i) =>
                                i === carIndex + 1 ? { ...c, status: "ready" } : c
                            )
                        );
                        setActiveCarIndex(carIndex + 1);
                    }
                } else {
                    // API 반환은 성공이지만 success: false인 경우
                    throw new Error(response.error || "실행 실패");
                }
            } catch (error) {
                // [TIER1] 에러 분류 및 메시지 개선
                let errorMessage = "알 수 없는 오류";
                if (error instanceof Error) {
                    if (error.message.includes("timeout") || error.message.includes("Timeout")) {
                        errorMessage = "요청 시간 초과 - 다시 시도해주세요";
                    } else if (error.message.includes("network") || error.message.includes("fetch")) {
                        errorMessage = "네트워크 오류 - 연결을 확인해주세요";
                    } else if (error.message.includes("402") || error.message.includes("credit")) {
                        errorMessage = "크레딧 부족 - 충전이 필요합니다";
                    } else {
                        errorMessage = error.message;
                    }
                }

                setCars((prev) =>
                    prev.map((c) =>
                        c.id === carId
                            ? { ...c, status: "failed", error: errorMessage }
                            : c
                    )
                );
                showNotification("error", errorMessage);
                console.error(`Car ${carId} execution failed:`, error);
            } finally {
                // 실행 완료 마킹 해제
                executingCarsRef.current.delete(carId);
            }
        };

        // [TIER2] 재시도 핸들러
        const handleRetryCar = useCallback((carId: string) => {
            // 먼저 상태를 ready로 변경
            setCars((prev) =>
                prev.map((c) =>
                    c.id === carId ? { ...c, status: "ready", error: undefined } : c
                )
            );
            // 그 다음 실행
            setTimeout(() => handleExecuteCar(carId), 100);
        }, []);

        // 전체 실행 핸들러 (하드닝 적용)
        const handleExecuteAll = async () => {
            // [TIER2] 중복 전체 실행 방지
            if (isExecutingAll) {
                console.warn("Already executing all, ignoring duplicate call");
                return;
            }

            setIsExecutingAll(true);
            try {
                for (const car of cars) {
                    if (car.status !== "completed" && car.status !== "failed") {
                        await handleExecuteCar(car.id);
                        // 실패 시 중단
                        const updatedCar = cars.find(c => c.id === car.id);
                        if (updatedCar?.status === "failed") {
                            showNotification("error", "워크플로우 실행 중 오류 발생");
                            break;
                        }
                    }
                }
                onComplete?.(cars.map((c) => c.output || {}));
            } finally {
                setIsExecutingAll(false);
            }
        };

        // Expose methods to parent
        useImperativeHandle(ref, () => ({
            executeAll: handleExecuteAll,
            reset: () => setCars([INITIAL_CAR]),

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
                setPendingConnections(CONNECTION_OPTIONS);
            },

            getCars: () => cars,
        }), [cars, handleExecuteAll]);

        // 연결 옵션 선택 핸들러
        const handleSelectConnection = async (optionId: string) => {
            const selectedOption = pendingConnections.find((opt) => opt.id === optionId);
            if (!selectedOption) return;

            const toolInfo = TOOL_INFO[selectedOption.recommendedToolId];
            if (!toolInfo) return;

            // 이전 노드의 output에서 기본 inputs 생성
            const prevCar = cars[cars.length - 1];
            const baseInputs: Record<string, unknown> = {};

            // 이전 노드 output을 기반으로 다음 노드 inputs 설정
            if (prevCar?.output) {
                if (toolInfo.dimension === "2D") {
                    baseInputs.concept = prevCar.output.prompt || prevCar.output.veo_prompt || "";
                } else if (toolInfo.dimension === "3D") {
                    baseInputs.description = prevCar.output.prompt || "";
                } else if (toolInfo.dimension === "4D") {
                    baseInputs.video_description = prevCar.output.prompt || prevCar.output.description || "";
                }
            }

            const newCar: Car = {
                id: `car-${cars.length + 1}`,
                order: cars.length,
                toolId: selectedOption.recommendedToolId,
                dimension: toolInfo.dimension,
                displayName: toolInfo.displayName,
                icon: toolInfo.icon,
                color: toolInfo.color,
                status: "pending",
                inputs: baseInputs,
            };

            setCars((prev) => [...prev, newCar]);
            setActiveCarIndex(cars.length);

            // 다음 연결 옵션 로드 - 사용한 차원 제외
            setIsLoadingOptions(true);
            await new Promise((resolve) => setTimeout(resolve, 300));

            // 이미 사용한 차원 제외하고 다음 옵션 생성
            const usedDimensions = new Set([...cars.map(c => c.dimension), toolInfo.dimension]);
            const nextOptions = CONNECTION_OPTIONS.filter(
                (opt) => {
                    const optToolInfo = TOOL_INFO[opt.recommendedToolId];
                    return optToolInfo && !usedDimensions.has(optToolInfo.dimension);
                }
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
            <div className="w-full min-h-[400px] p-8 relative">
                {/* [TIER2] 알림 토스트 */}
                <AnimatePresence>
                    {notification && (
                        <div
                            className={`
                                fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg
                                flex items-center gap-2 animate-in slide-in-from-right
                                ${notification.type === "success"
                                    ? "bg-emerald-500/90 text-white"
                                    : "bg-red-500/90 text-white"
                                }
                            `}
                        >
                            {notification.type === "success" ? (
                                <CheckCircle className="h-4 w-4" />
                            ) : (
                                <XCircle className="h-4 w-4" />
                            )}
                            <span className="text-sm font-medium">{notification.message}</span>
                        </div>
                    )}
                </AnimatePresence>

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
                                            onRetry={
                                                car.status === "failed"
                                                    ? () => handleRetryCar(car.id)
                                                    : undefined
                                            }
                                        />

                                        {/* 삭제 버튼 (첫 번째 노드 제외, 실행 중 비활성화) */}
                                        {index > 0 && (
                                            <button
                                                onClick={() => handleDeleteCar(car.id)}
                                                disabled={car.status === "executing" || isExecutingAll}
                                                className={`
                                                    absolute -top-1 -right-1 h-6 w-6 rounded-full
                                                    border flex items-center justify-center transition-all
                                                    ${car.status === "executing" || isExecutingAll
                                                        ? "bg-zinc-800/50 border-zinc-700 text-zinc-600 cursor-not-allowed"
                                                        : "bg-red-500/20 border-red-500/50 text-red-400 hover:bg-red-500/30 opacity-0 group-hover:opacity-100"
                                                    }
                                                `}
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
                                                    setPendingConnections(CONNECTION_OPTIONS);
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
                                    {cars.reduce((sum, c) => sum + (c.creditCost ?? DIMENSION_CREDIT_COSTS[c.toolId] ?? 10), 0)}
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
