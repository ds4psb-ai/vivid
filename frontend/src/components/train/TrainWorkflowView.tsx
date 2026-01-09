"use client";

import { useState, forwardRef, useImperativeHandle, useCallback, useRef, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { TrainCar } from "./TrainCar";
import { ConnectionSelector } from "./ConnectionSelector";
import { DimensionPortalModal } from "./DimensionPortalModal";
import { Trash2, CheckCircle, XCircle } from "lucide-react";
import { api, DimensionResponse } from "@/lib/api";
import { useDimensionConfig, type ConnectionOption } from "@/contexts/DimensionConfigContext";

// =============================================================================
// Types
// =============================================================================

interface Car {
    id: string;
    order: number;
    toolId: string;
    dimension: "1D" | "2D" | "3D" | "4D" | "QC" | "AD" | "AI" | "VEO";
    displayName: string;
    icon: string;
    color: string;
    status: "pending" | "ready" | "executing" | "completed" | "failed";
    inputs: Record<string, unknown>;
    output?: Record<string, unknown>;
    error?: string;
    creditCost?: number;
}

// ConnectionOption is now imported from DimensionConfigContext

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
// Dimension Tool Definitions (Now fetched from DimensionConfigContext SSoT)
// =============================================================================

type DimensionType = "1D" | "2D" | "3D" | "4D" | "QC" | "AD" | "AI" | "VEO" | "SA" | "SC";

// Display labels for dimension positions
const DIMENSION_LABELS = ["Origin", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"];

// =============================================================================
// Context-Aware Recommendation Logic (confidence boosts based on workflow)
// =============================================================================

// Base confidence adjustments based on previous dimension
const CONFIDENCE_BOOSTS: Partial<Record<DimensionType, Partial<Record<string, number>>>> = {
    "1D": { storyboard: 0.2, aesthetic_direct: 0.15, quality_check: 0.05 },
    "2D": { image_tool: 0.2, quality_check: 0.15, veo_generate: 0.1, aesthetic_direct: 0.1 },
    "3D": { quality_check: 0.15, veo_generate: 0.15, reference_analyzer: 0.1 },
    "4D": { prompt_generator: 0.2, aesthetic_direct: 0.15, storyboard: 0.1 },
    "QC": { aesthetic_direct: 0.1, veo_generate: 0.1 },
    "AD": { prompt_generator: 0.15, storyboard: 0.15, image_tool: 0.1 },
    "AI": { prompt_generator: 0.2, storyboard: 0.1, aesthetic_direct: 0.1 },
    "VEO": { quality_check: 0.15 },
};

// Output type-based adjustments
const OUTPUT_TYPE_BOOSTS: Record<string, Partial<Record<string, number>>> = {
    scenes: { veo_generate: 0.15, quality_check: 0.1 },
    prompt: { storyboard: 0.1, image_tool: 0.1, aesthetic_direct: 0.05 },
    style_guide: { prompt_generator: 0.1, storyboard: 0.1 },
};

// =============================================================================
// Input Validation
// =============================================================================

function validateInputs(dimension: "1D" | "2D" | "3D" | "4D" | "QC" | "AD" | "AI" | "VEO", inputs: Record<string, unknown>): { valid: boolean; error?: string } {
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
        // Get dimension config from context (SSoT)
        const { toolsById, getInitialOptions, getConnectionOptions } = useDimensionConfig();

        const [cars, setCars] = useState<Car[]>([]);
        const [isLoadingOptions, setIsLoadingOptions] = useState(false);
        const [activeCarIndex, setActiveCarIndex] = useState(0);
        const [isExecutingAll, setIsExecutingAll] = useState(false);
        const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);
        const [portalCarId, setPortalCarId] = useState<string | null>(null);

        // Initial connection options from context
        const initialOptions = useMemo(() => getInitialOptions(), [getInitialOptions]);
        const [pendingConnections, setPendingConnections] = useState<ConnectionOption[]>([]);

        // Initialize pendingConnections when context loads
        useMemo(() => {
            if (initialOptions.length > 0 && pendingConnections.length === 0) {
                setPendingConnections(initialOptions);
            }
        }, [initialOptions, pendingConnections.length]);

        // Track executing cars to prevent double-click
        const executingCarsRef = useRef<Set<string>>(new Set());

        // Helper: Get tool info from context
        const getToolInfo = useCallback((toolId: string) => {
            return toolsById[toolId];
        }, [toolsById]);

        // Context-aware recommendations using context data
        const getContextAwareRecommendations = useCallback((
            prevDimension: DimensionType | undefined,
            prevOutput: Record<string, unknown> | undefined,
            usedDimensions: Set<DimensionType>
        ): ConnectionOption[] => {
            const usedToolIds = cars.map(c => c.toolId);
            const allOptions = getConnectionOptions(usedToolIds);

            const adjustedOptions = allOptions.map(opt => {
                const optToolInfo = getToolInfo(opt.recommendedToolId);
                if (!optToolInfo || usedDimensions.has(optToolInfo.dimension as DimensionType)) {
                    return null;
                }

                let adjustedConfidence = opt.confidence;

                // Apply dimension-based boost
                if (prevDimension && CONFIDENCE_BOOSTS[prevDimension]) {
                    const boost = CONFIDENCE_BOOSTS[prevDimension]?.[opt.recommendedToolId] || 0;
                    adjustedConfidence += boost;
                }

                // Apply output type-based boost
                if (prevOutput) {
                    Object.keys(OUTPUT_TYPE_BOOSTS).forEach(key => {
                        if (prevOutput[key]) {
                            const boost = OUTPUT_TYPE_BOOSTS[key]?.[opt.recommendedToolId] || 0;
                            adjustedConfidence += boost;
                        }
                    });
                }

                adjustedConfidence = Math.min(adjustedConfidence, 0.99);
                return { ...opt, confidence: adjustedConfidence };
            }).filter((opt): opt is ConnectionOption => opt !== null);

            return adjustedOptions.sort((a, b) => b.confidence - a.confidence);
        }, [cars, getConnectionOptions, getToolInfo]);

        // Auto-dismiss notification
        const showNotification = useCallback((type: "success" | "error", message: string) => {
            setNotification({ type, message });
            setTimeout(() => setNotification(null), 3000);
        }, []);

        // Output → Input 체이닝: 이전 노드 출력을 다음 노드 입력으로 변환
        const prepareInputsFromPreviousOutput = useCallback(
            (dimension: "1D" | "2D" | "3D" | "4D" | "QC" | "AD" | "AI" | "VEO", prevOutput: Record<string, unknown> | undefined, baseInputs: Record<string, unknown>) => {
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
                    // Extended Dimension Capsules Input Chaining
                    case "QC":
                        // QC는 이전 output 전체를 content로 사용
                        return {
                            ...baseInputs,
                            content: JSON.stringify(prevOutput, null, 2),
                            content_type: prevOutput.scenes ? "storyboard" : prevOutput.prompt ? "prompt" : "general",
                        };
                    case "AD":
                        // AD는 이전 prompt/concept을 미학 컨셉으로 사용
                        return {
                            ...baseInputs,
                            concept: prevOutput.prompt || prevOutput.concept || prevOutput.description || baseInputs.concept,
                            reference_style: prevOutput.style || prevOutput.visual_style,
                        };
                    case "AI":
                        // AI는 이전 컨텐츠를 분석 대상으로 사용
                        return {
                            ...baseInputs,
                            subject: prevOutput.prompt || prevOutput.concept || prevOutput.description || baseInputs.subject,
                            depth: "comprehensive",
                        };
                    case "VEO":
                        // VEO는 scenes (storyboard)나 prompt를 비디오 프롬프트로 사용
                        if (prevOutput.scenes && Array.isArray(prevOutput.scenes)) {
                            // Storyboard scenes를 비디오 프롬프트로 변환
                            const scenesText = (prevOutput.scenes as Array<Record<string, unknown>>)
                                .map((s, i) => `Scene ${i + 1}: ${s.description || s.visual || ""}`)
                                .join("\n");
                            return {
                                ...baseInputs,
                                prompt: scenesText,
                                duration: 8,
                                aspect_ratio: "16:9",
                            };
                        }
                        return {
                            ...baseInputs,
                            prompt: prevOutput.prompt || prevOutput.veo_prompt || prevOutput.description || baseInputs.prompt,
                            duration: 8,
                            aspect_ratio: "16:9",
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
                    // creditCost: API 응답에서 가져오거나 context 기본값 사용
                    const toolConfig = getToolInfo(car.toolId);
                    const actualCreditCost = response.metrics?.credit_cost
                        ?? toolConfig?.creditCost
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
            // eslint-disable-next-line react-hooks/exhaustive-deps
        }, []);

        // Portal modal handlers
        const handlePortalInputChange = useCallback((carId: string, inputs: Record<string, unknown>) => {
            setCars((prev) =>
                prev.map((c) => c.id === carId ? { ...c, inputs } : c)
            );
        }, []);

        const handlePortalOutputUpdate = useCallback((carId: string, output: Record<string, unknown>, creditCost?: number) => {
            setCars((prev) =>
                prev.map((c) =>
                    c.id === carId
                        ? { ...c, output, creditCost: creditCost ?? c.creditCost }
                        : c
                )
            );
        }, []);

        const handlePortalStatusChange = useCallback((carId: string, status: Car["status"], error?: string) => {
            setCars((prev) =>
                prev.map((c) =>
                    c.id === carId
                        ? { ...c, status, error: error ?? undefined }
                        : c
                )
            );
            // Update active car index if needed
            if (status === "completed") {
                const carIndex = cars.findIndex(c => c.id === carId);
                if (carIndex >= 0 && carIndex < cars.length - 1) {
                    setActiveCarIndex(carIndex + 1);
                    // Mark next car as ready
                    setCars((prev) =>
                        prev.map((c, i) => i === carIndex + 1 ? { ...c, status: "ready" } : c)
                    );
                }
                showNotification("success", "차원 전개 완료!");
            } else if (status === "failed") {
                showNotification("error", error || "실행 실패");
            }
        }, [cars, showNotification]);

        // 전체 실행 핸들러 (하드닝 적용)
        const handleExecuteAll = useCallback(async () => {
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
            // eslint-disable-next-line react-hooks/exhaustive-deps
        }, [cars, isExecutingAll, onComplete, showNotification]);

        // Expose methods to parent
        useImperativeHandle(ref, () => ({
            executeAll: handleExecuteAll,
            reset: () => {
                setCars([]);
                setPendingConnections(initialOptions);
                setActiveCarIndex(0);
            },

            // Agent integration methods
            addCar: (carData: Omit<Car, "id" | "order">) => {
                // Use combination of timestamp, order, and random suffix for truly unique IDs
                const uniqueSuffix = Math.random().toString(36).substring(2, 8);
                const newId = `agent-car-${Date.now()}-${cars.length}-${uniqueSuffix}`;
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
                setPendingConnections(initialOptions);
            },

            getCars: () => cars,
        }), [cars, handleExecuteAll, initialOptions]);

        // 연결 옵션 선택 핸들러
        const handleSelectConnection = async (optionId: string) => {
            const selectedOption = pendingConnections.find((opt) => opt.id === optionId);
            if (!selectedOption) return;

            const toolConfig = getToolInfo(selectedOption.recommendedToolId);
            if (!toolConfig) return;

            // 첫 번째 차원 선택인지 체크
            const isFirstCar = cars.length === 0;

            // 이전 노드의 output에서 기본 inputs 생성
            const prevCar = cars.length > 0 ? cars[cars.length - 1] : undefined;
            const baseInputs: Record<string, unknown> = {};

            // 이전 노드 output을 기반으로 다음 노드 inputs 설정
            if (prevCar?.output) {
                if (toolConfig.dimension === "2D") {
                    baseInputs.concept = prevCar.output.prompt || prevCar.output.veo_prompt || "";
                } else if (toolConfig.dimension === "3D") {
                    baseInputs.description = prevCar.output.prompt || "";
                } else if (toolConfig.dimension === "4D") {
                    baseInputs.video_description = prevCar.output.prompt || prevCar.output.description || "";
                }
            }

            const newCar: Car = {
                id: `car-${cars.length + 1}`,
                order: cars.length,
                toolId: selectedOption.recommendedToolId,
                dimension: toolConfig.dimension as Car["dimension"],
                displayName: toolConfig.displayName,
                icon: toolConfig.icon,
                color: toolConfig.color,
                // 첫 번째 차원은 바로 ready 상태로
                status: isFirstCar ? "ready" : "pending",
                inputs: baseInputs,
                creditCost: toolConfig.creditCost,
            };

            setCars((prev) => [...prev, newCar]);
            setActiveCarIndex(cars.length);

            // 다음 연결 옵션 로드 - 컨텍스트 인식 추천
            setIsLoadingOptions(true);
            await new Promise((resolve) => setTimeout(resolve, 300));

            // 이미 사용한 차원 제외하고 컨텍스트 기반 추천 생성
            const usedDimensions = new Set([...cars.map(c => c.dimension), toolConfig.dimension as DimensionType]);
            const lastCar = cars[cars.length - 1];
            const nextOptions = getContextAwareRecommendations(
                toolConfig.dimension as DimensionType,  // 방금 추가된 차원
                lastCar?.output,     // 마지막 차원의 출력
                usedDimensions
            );

            setPendingConnections(nextOptions);
            setIsLoadingOptions(false);
        };

        // 노드 삭제 핸들러
        const handleDeleteCar = (carId: string) => {
            const carIndex = cars.findIndex((c) => c.id === carId);
            if (carIndex < 0) return;

            const newCars = cars.filter((c) => c.id !== carId);
            setCars(newCars);

            // 모든 노드가 삭제되면 초기 차원 선택 옵션 복원
            if (newCars.length === 0) {
                setPendingConnections(initialOptions);
                setActiveCarIndex(0);
            } else {
                setActiveCarIndex(Math.min(activeCarIndex, newCars.length - 1));
                // 마지막 노드 삭제 후 연결 옵션 재계산
                const usedDimensions = new Set(newCars.map(c => c.dimension));
                const lastCar = newCars[newCars.length - 1];
                const freshOptions = getContextAwareRecommendations(
                    lastCar?.dimension,
                    lastCar?.output,
                    usedDimensions
                );
                setPendingConnections(freshOptions);
            }
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

                    {/* 빈 상태: 중앙 집중형 스타터 */}
                    <AnimatePresence mode="wait">
                        {cars.length === 0 && (
                            <motion.div
                                key="starter"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, x: -100, scale: 0.9 }}
                                transition={{ duration: 0.3 }}
                                className="flex flex-col items-center justify-center h-[50vh] w-full"
                            >
                                {/* 중앙 배치된 ConnectionSelector */}
                                <ConnectionSelector
                                    options={pendingConnections}
                                    onSelect={handleSelectConnection}
                                    onReRecommend={() => {
                                        setIsLoadingOptions(true);
                                        setTimeout(() => {
                                            setPendingConnections(initialOptions);
                                            setIsLoadingOptions(false);
                                        }, 300);
                                    }}
                                    isLoading={isLoadingOptions}
                                    isPrimarySelection
                                />
                            </motion.div>
                        )}
                    </AnimatePresence>

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
                                            onViewDetails={() => setPortalCarId(car.id)}
                                        />

                                        {/* 삭제 버튼 (실행 중 비활성화) */}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteCar(car.id);
                                            }}
                                            disabled={car.status === "executing" || isExecutingAll}
                                            className={`
                                                absolute -top-1 -right-1 h-6 w-6 rounded-full
                                                border flex items-center justify-center transition-all
                                                ${car.status === "executing" || isExecutingAll
                                                    ? "bg-zinc-800/50 border-zinc-700 text-zinc-600 cursor-not-allowed"
                                                    : "bg-red-500/20 border-red-500/50 text-red-400 hover:bg-red-500/30"
                                                }
                                            `}
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </button>
                                    </div>

                                    {/* 차원문 (마지막 노드 후에만 표시) */}
                                    {index === cars.length - 1 && pendingConnections.length > 0 && (
                                        <ConnectionSelector
                                            options={pendingConnections}
                                            onSelect={handleSelectConnection}
                                            onReRecommend={() => {
                                                setIsLoadingOptions(true);
                                                setTimeout(() => {
                                                    // 컨텍스트 인식 재추천
                                                    const usedDimensions = new Set(cars.map(c => c.dimension));
                                                    const lastCar = cars[cars.length - 1];
                                                    const freshOptions = getContextAwareRecommendations(
                                                        lastCar?.dimension,
                                                        lastCar?.output,
                                                        usedDimensions
                                                    );
                                                    setPendingConnections(freshOptions);
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
                {cars.length > 0 && (
                    <div className="mt-8 p-4 rounded-xl bg-zinc-900/50 border border-zinc-800">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div>
                                    <span className="text-[10px] text-zinc-500 uppercase tracking-widest">
                                        현재 차원
                                    </span>
                                    <p className="text-lg font-bold text-white">
                                        {cars[cars.length - 1]?.dimension || "—"}
                                    </p>
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
                                        {cars.reduce((sum, c) => sum + (c.creditCost ?? toolsById[c.toolId]?.creditCost ?? 10), 0)}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                {cars.map((car) => (
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
                )}

                {/* Dimension Portal Modal */}
                <DimensionPortalModal
                    isOpen={!!portalCarId}
                    onClose={() => setPortalCarId(null)}
                    cars={cars}
                    currentCarId={portalCarId || ""}
                    onNavigate={setPortalCarId}
                    onInputChange={handlePortalInputChange}
                    onExecute={handleExecuteCar}
                    onOutputUpdate={handlePortalOutputUpdate}
                    onStatusChange={handlePortalStatusChange}
                />
            </div>
        );
    }
);

TrainWorkflowView.displayName = "TrainWorkflowView";
