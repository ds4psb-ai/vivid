"use client";

import { useState, useRef, useCallback, useMemo, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import { AuroraBackground } from "@/components/AuroraBackground";
import { TrainWorkflowView, TrainWorkflowHandle } from "@/components/train/TrainWorkflowView";
import { AgentChatAccordion } from "@/components/AgentChatAccordion";
import { WorkflowCanvas } from "@/components/flow/WorkflowCanvas";
import { FlowSidebar } from "@/components/flow/FlowSidebar";
import { useLanguage } from "@/contexts/LanguageContext";
import { useDimensionConfig } from "@/contexts/DimensionConfigContext";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Copy, Check, Sparkles, LayoutGrid, Image as ImageIcon, Film, X, Download, Save, CheckCircle, Palette, Moon, Video, Loader2, BookOpen, Music, Construction, ArrowLeft, AlertCircle, Workflow, Search, Layers, Wand2, PanelLeft } from "lucide-react";
import { api, SingularityTemplate } from "@/lib/api";
import { FLOW_ENABLED } from "@/lib/feature-flags";
import { dimensionIdToCode, getDimensionToken } from "@/lib/tokens";
import { normalizeWorkflowDimension, type WorkflowDimension } from "@/lib/dimension-types";
import { FLOW_START_OPTIONS, STANDALONE_TOOLS } from "@/lib/dimension-data";
import { useMachine } from "@xstate/react";
import { workflowMachine, type WorkflowPhase } from "@/machines/workflowMachine";
import Link from "next/link";
import type {
    WorkflowStartEvent,
    WorkflowStepEvent,
    WorkflowCreatedEvent,
} from "@/types/agent";

// WorkflowDimension shared in lib/dimension-types

// Agent tool names to toolId mapping (for workflow events) - 10개 전체
const AGENT_TOOL_TO_TOOL_ID: Record<string, string> = {
    // Core Dimensions (1D-4D)
    "generate_veo_prompt": "prompt_generator",
    "create_storyboard": "storyboard",
    "generate_image_prompt": "image_tool",
    "analyze_reference": "reference_analyzer",
    // Extended Dimensions
    "quality_check": "quality_check",
    "aesthetic_direct": "aesthetic_direct",
    "persona_analyze": "persona_analyze",
    "veo_generate": "veo_generate",
    "story_architect": "story_architect",
    "sound_craft": "sound_craft",
};

// Dimension code to toolId mapping (for template loading) - 10개 전체
const DIMENSION_TO_TOOL_ID: Record<string, string> = {
    // Core dimensions (1D-4D)
    "1D": "prompt_generator",
    "2D": "storyboard",
    "3D": "image_tool",
    "4D": "reference_analyzer",
    // Extended dimensions (10개 전체)
    "QC": "quality_check",
    "AD": "aesthetic_direct",
    "AI": "persona_analyze",
    "VEO": "veo_generate",
    "SA": "story_architect",
    "SC": "sound_craft",
    // 4-Stage Workflow aliases
    "STORY": "story_architect",
    "STORYBOARD": "storyboard",
    "SOUND": "sound_craft",
    "REF": "reference_analyzer",
    "VIS": "image_tool",
};

// Icon components - 10개 차원 전체
const ICON_COMPONENTS: Record<string, React.ReactNode> = {
    // Core Dimensions
    sparkles: <Sparkles className="h-5 w-5" />,
    "layout-grid": <LayoutGrid className="h-5 w-5" />,
    image: <ImageIcon className="h-5 w-5" />,
    film: <Film className="h-5 w-5" />,
    // Extended Dimension Capsules
    "check-circle": <CheckCircle className="h-5 w-5" />,
    palette: <Palette className="h-5 w-5" />,
    moon: <Moon className="h-5 w-5" />,
    video: <Video className="h-5 w-5" />,
    "book-open": <BookOpen className="h-5 w-5" />,  // SA: Story Architect
    music: <Music className="h-5 w-5" />,           // SC: Sound Crafter
};

// Workflow result type
interface WorkflowResult {
    dimension: string;
    dimensionName: string;
    toolName: string;
    inputs: Record<string, unknown>;  // 🆕 Added: input prompts/options
    output: Record<string, unknown>;
    creditCost?: number;
    executedAt: Date;  // 🆕 Added: execution timestamp
}

// Safe JSON stringify to handle circular references and large objects
function safeStringify(value: unknown, maxLength = 5000): string {
    const seen = new WeakSet();
    try {
        const result = JSON.stringify(value, (key, val) => {
            // Handle circular references
            if (typeof val === 'object' && val !== null) {
                if (seen.has(val)) {
                    return '[Circular]';
                }
                seen.add(val);
            }
            // Truncate very long strings
            if (typeof val === 'string' && val.length > 1000) {
                return val.slice(0, 1000) + '...';
            }
            return val;
        }, 2);

        // Truncate overall result if too long
        if (result && result.length > maxLength) {
            return result.slice(0, maxLength) + '\n...(truncated)';
        }
        return result || '(empty)';
    } catch {
        return '(serialization error)';
    }
}

// 🆕 Download utility functions
function downloadFile(content: string, filename: string, mimeType: string) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadResultAsJSON(result: WorkflowResult) {
    const data = {
        dimension: result.dimension,
        dimensionName: result.dimensionName,
        toolName: result.toolName,
        inputs: result.inputs,
        output: result.output,
        executedAt: result.executedAt?.toISOString(),
    };
    downloadFile(
        JSON.stringify(data, null, 2),
        `${result.dimension}-${result.toolName}.json`,
        'application/json'
    );
}

function downloadResultAsMarkdown(result: WorkflowResult) {
    let md = `# ${result.dimension} - ${result.dimensionName}\n\n`;
    md += `**도구**: ${result.toolName}\n`;
    md += `**실행 시간**: ${result.executedAt?.toLocaleString('ko-KR')}\n\n`;

    if (Object.keys(result.inputs).length > 0) {
        md += `## 입력\n\n`;
        Object.entries(result.inputs).forEach(([key, value]) => {
            md += `### ${key.replace(/_/g, ' ')}\n${typeof value === 'string' ? value : JSON.stringify(value, null, 2)}\n\n`;
        });
    }

    md += `## 출력\n\n`;
    Object.entries(result.output).forEach(([key, value]) => {
        md += `### ${key.replace(/_/g, ' ')}\n`;
        if (typeof value === 'string') {
            md += `${value}\n\n`;
        } else {
            md += `\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\`\n\n`;
        }
    });

    downloadFile(md, `${result.dimension}-${result.toolName}.md`, 'text/markdown');
}

const BRAND_TONE = {
    text: "text-[var(--color-brand-primary)]",
    textSoft: "text-[var(--color-brand-primary)]/70",
    textMuted: "text-[var(--color-brand-primary)]/60",
    bgSubtle: "bg-[var(--color-brand-primary)]/10",
    bg: "bg-[var(--color-brand-primary)]/20",
    border: "border-[var(--color-brand-primary)]/30",
    borderStrong: "border-[var(--color-brand-primary)]/50",
    hoverBg: "hover:bg-[var(--color-brand-primary)]/30",
    solid: "bg-[var(--color-brand-primary)]",
};

const SUCCESS_TONE = {
    text: "text-[var(--success)]",
    textSoft: "text-[var(--success)]/70",
    bgSubtle: "bg-[var(--success)]/10",
    bg: "bg-[var(--success)]/20",
    border: "border-[var(--success)]/30",
};

const ERROR_TONE = {
    text: "text-[var(--error)]",
    textSoft: "text-[var(--error)]/70",
    bgSubtle: "bg-[var(--error)]/10",
    bg: "bg-[var(--error)]/20",
    border: "border-[var(--error)]/30",
};

const WARNING_TONE = {
    text: "text-[var(--warning)]",
    textSoft: "text-[var(--warning)]/70",
    bgSubtle: "bg-[var(--warning)]/10",
    bg: "bg-[var(--warning)]/20",
    border: "border-[var(--warning)]/30",
};

const INFO_TONE = {
    solid: "bg-[var(--info)]",
    hover: "hover:opacity-90",
};

function FlowPageContent() {
    const [workflowResults, setWorkflowResults] = useState<WorkflowResult[]>([]);
    const [showResults, setShowResults] = useState(false);
    const [expandedResult, setExpandedResult] = useState<string | null>(null);
    const [copiedField, setCopiedField] = useState<string | null>(null);

    // XState workflow machine for structured state management
    const [workflowState, sendWorkflow] = useMachine(workflowMachine);

    // Show DAG canvas toggle
    const [showDagCanvas, setShowDagCanvas] = useState(false);

    // Sidebar state
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [showMobileSidebar, setShowMobileSidebar] = useState(false);

    // 🆕 Template save modal state
    const [showTemplateModal, setShowTemplateModal] = useState(false);
    const [templateTitle, setTemplateTitle] = useState("");
    const [templateDescription, setTemplateDescription] = useState("");
    const [templateTags, setTemplateTags] = useState("");
    const [isSavingTemplate, setIsSavingTemplate] = useState(false);
    const [templateSaveSuccess, setTemplateSaveSuccess] = useState(false);
    const [savedTemplateId, setSavedTemplateId] = useState<string | null>(null);  // 🆕 For singularity link
    const [templateSaveError, setTemplateSaveError] = useState<string | null>(null);  // 🆕 Inline error

    const workflowRef = useRef<TrainWorkflowHandle>(null);
    const { language } = useLanguage();
    const { toolsById, tools, isLoading: isConfigLoading } = useDimensionConfig();
    const searchParams = useSearchParams();

    // Template loading state
    const [loadedTemplate, setLoadedTemplate] = useState<SingularityTemplate | null>(null);
    const [isLoadingTemplate, setIsLoadingTemplate] = useState(false);
    const [templateApplied, setTemplateApplied] = useState(false);
    const [appliedTemplateSequence, setAppliedTemplateSequence] = useState<string[]>([]);
    const [templateSkippedDimensions, setTemplateSkippedDimensions] = useState<string[]>([]);

    // Helper: Get tool info from agent tool name
    const getToolInfoFromAgentTool = useCallback((agentToolName: string) => {
        const toolId = AGENT_TOOL_TO_TOOL_ID[agentToolName];
        if (!toolId) return null;
        return toolsById[toolId] || null;
    }, [toolsById]);

    const dimensionToToolId = useMemo(() => {
        const mapping: Record<string, string> = { ...DIMENSION_TO_TOOL_ID };
        tools.forEach((tool) => {
            if (!tool?.dimension) return;
            mapping[tool.dimension] = tool.toolId;
            const code = dimensionIdToCode(tool.dimension);
            if (code) {
                const normalized = code.toUpperCase().replace(/-/g, "_");
                mapping[normalized] ??= tool.toolId;
                mapping[code] ??= tool.toolId;
            }
        });
        return mapping;
    }, [tools]);

    // Helper: Get tool info from dimension code, tool id, or agent tool name
    const getToolInfoFromDimension = useCallback((value: string) => {
        if (!value) return null;
        if (toolsById[value]) return toolsById[value];
        const agentToolId = AGENT_TOOL_TO_TOOL_ID[value];
        if (agentToolId && toolsById[agentToolId]) return toolsById[agentToolId];
        const toolId = dimensionToToolId[value];
        if (toolId && toolsById[toolId]) return toolsById[toolId];
        const code = dimensionIdToCode(value);
        if (code) {
            const normalized = code.toUpperCase().replace(/-/g, "_");
            const mappedToolId = dimensionToToolId[normalized] ?? dimensionToToolId[code];
            if (mappedToolId && toolsById[mappedToolId]) return toolsById[mappedToolId];
        }
        return null;
    }, [dimensionToToolId, toolsById]);

    // Template loading error state
    const [templateLoadError, setTemplateLoadError] = useState<string | null>(null);

    // Load template from URL parameter with validation
    useEffect(() => {
        const templateId = searchParams.get("template");
        if (!templateId || templateApplied || isConfigLoading) return;

        // Validate template ID format (basic UUID/alphanumeric check)
        const isValidId = /^[a-zA-Z0-9_-]{1,100}$/.test(templateId);
        if (!isValidId) {
            console.warn("[Flow] Invalid template ID format:", templateId);
            setTemplateLoadError("잘못된 템플릿 ID 형식입니다.");
            return;
        }

        const loadTemplate = async () => {
            setIsLoadingTemplate(true);
            setTemplateLoadError(null);
            try {
                const template = await api.getSingularityTemplate(templateId);

                // Validate template structure
                if (!template || typeof template !== "object") {
                    throw new Error("Invalid template response");
                }
                if (!template.title || typeof template.title !== "string") {
                    throw new Error("Template missing title");
                }

                // Validate tool_sequence or dimension_sequence exists
                const sequence = template.tool_sequence || template.dimension_sequence;
                if (!Array.isArray(sequence) || sequence.length === 0) {
                    console.warn("[Flow] Template has no tool sequence:", template.title);
                    // Still allow loading, but log warning
                }

                setLoadedTemplate(template);
                console.log("[Flow] Loaded template:", template.title);
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : "템플릿 로드 실패";
                console.error("[Flow] Failed to load template:", err);
                setTemplateLoadError(errorMessage);
                setLoadedTemplate(null);
            } finally {
                setIsLoadingTemplate(false);
            }
        };

        loadTemplate();
    }, [searchParams, templateApplied, isConfigLoading]);

    useEffect(() => {
        if (!loadedTemplate) {
            setAppliedTemplateSequence([]);
            setTemplateSkippedDimensions([]);
        }
    }, [loadedTemplate]);

    // Apply loaded template to workflow
    useEffect(() => {
        if (!loadedTemplate || !workflowRef.current || templateApplied || isConfigLoading) return;
        if (Object.keys(toolsById).length === 0) return; // Wait for config

        const toolSequence = loadedTemplate.tool_sequence || loadedTemplate.dimension_sequence;
        if (!toolSequence || toolSequence.length === 0) return;

        console.log("[Flow] Applying template:", loadedTemplate.title, "with sequence:", toolSequence);

        // Clear existing cars
        workflowRef.current.clearCars();

        // P1: Extract dimension-specific presets from input_preset
        // Format: { "1d_topic": "value", "2d_style": "value", ... }
        // Priority: user_input > preset > defaults
        const extractDimensionPreset = (dimCode: string, fullPreset: Record<string, unknown> = {}): Record<string, unknown> => {
            const normalized = normalizeWorkflowDimension(dimCode) ?? dimCode.toUpperCase();
            const prefixCandidates = new Set<string>([`${dimCode.toLowerCase()}_`]);

            switch (normalized) {
                case "1D":
                    prefixCandidates.add("1d_");
                    prefixCandidates.add("prompt_");
                    break;
                case "2D":
                    prefixCandidates.add("2d_");
                    prefixCandidates.add("storyboard_");
                    break;
                case "3D":
                    prefixCandidates.add("3d_");
                    prefixCandidates.add("vis_");
                    break;
                case "4D":
                    prefixCandidates.add("4d_");
                    prefixCandidates.add("ref_");
                    break;
                case "QC":
                    prefixCandidates.add("qc_");
                    break;
                case "AD":
                    prefixCandidates.add("ad_");
                    break;
                case "AI":
                    prefixCandidates.add("ai_");
                    prefixCandidates.add("mirror_");
                    break;
                case "VEO":
                    prefixCandidates.add("veo_");
                    break;
                case "STORY":
                    prefixCandidates.add("story_");
                    prefixCandidates.add("sa_");
                    break;
                case "SOUND":
                    prefixCandidates.add("sound_");
                    prefixCandidates.add("sc_");
                    break;
                default:
                    break;
            }
            const dimensionPreset: Record<string, unknown> = {};

            // Extract prefixed keys for this dimension
            Object.entries(fullPreset).forEach(([key, value]) => {
                const lowerKey = key.toLowerCase();
                for (const prefix of prefixCandidates) {
                    if (lowerKey.startsWith(prefix)) {
                        // Remove prefix: "1d_topic" -> "topic"
                        const fieldName = key.slice(prefix.length);
                        dimensionPreset[fieldName] = value;
                        break;
                    }
                }
            });

            // Also include non-prefixed keys as defaults (for backward compatibility)
            Object.entries(fullPreset).forEach(([key, value]) => {
                const lowerKey = key.toLowerCase();
                // Skip if already has a prefix for any dimension
                if (!lowerKey.match(/^[0-9]d_|^qc_|^ad_|^ai_|^veo_|^sa_|^sc_|^story_|^sound_|^storyboard_|^prompt_|^mirror_|^ref_|^vis_/)) {
                    // Only add if not already set by prefixed version
                    if (!(key in dimensionPreset)) {
                        dimensionPreset[key] = value;
                    }
                }
            });

            return dimensionPreset;
        };

        const resolveToolId = (value: string) => {
            if (toolsById[value]) return value;
            const agentToolId = AGENT_TOOL_TO_TOOL_ID[value];
            if (agentToolId) return agentToolId;
            const mapped = dimensionToToolId[value];
            if (mapped) return mapped;
            const code = dimensionIdToCode(value);
            if (code) {
                const normalized = code.toUpperCase().replace(/-/g, "_");
                return dimensionToToolId[normalized] ?? dimensionToToolId[code] ?? value;
            }
            return value;
        };

        const appliedSequence: string[] = [];
        const skippedSequence: string[] = [];

        // Add cars from template's tool sequence
        toolSequence.forEach((dimCode, idx) => {
            const toolInfo = getToolInfoFromDimension(dimCode);
            if (!toolInfo || !workflowRef.current) {
                skippedSequence.push(dimCode);
                return;
            }
            const normalizedDimension = normalizeWorkflowDimension(toolInfo.dimension || dimCode);
            if (!normalizedDimension) {
                console.warn("[Flow] Unsupported workflow dimension:", dimCode);
                skippedSequence.push(dimCode);
                return;
            }

            // P1: Apply dimension-specific preset instead of full preset
            const dimensionPreset = extractDimensionPreset(dimCode, loadedTemplate.input_preset);

            workflowRef.current.addCar({
                toolId: resolveToolId(dimCode),
                dimension: normalizedDimension as WorkflowDimension,
                displayName: toolInfo.displayName,
                icon: toolInfo.icon,
                color: toolInfo.color,
                status: idx === 0 ? "ready" : "pending",
                inputs: dimensionPreset,  // P1: dimension-specific preset
            });
            appliedSequence.push(normalizedDimension);
        });

        setTemplateApplied(true);
        setAppliedTemplateSequence(appliedSequence);
        setTemplateSkippedDimensions(skippedSequence);
        console.log(`[Flow] Applied ${toolSequence.length} cars from template with dimension-specific presets`);
    }, [loadedTemplate, templateApplied, toolsById, isConfigLoading, getToolInfoFromDimension, dimensionToToolId]);

    // Track agent-created cars for updating status
    const carIdMapRef = useRef<Map<number, string>>(new Map());

    const labels = {
        badge: language === "ko" ? "디멘션 플로우" : "Dimension Flow",
        initialMessage: language === "ko"
            ? "안녕하세요! 차원 흐름을 함께 설계해드릴게요. 어떤 콘텐츠를 만들고 싶으신가요?"
            : "Hello! I'll help you design dimension flows. What content would you like to create?",
        results: language === "ko" ? "워크플로우 결과물" : "Workflow Results",
        copySuccess: language === "ko" ? "복사됨!" : "Copied!",
        selectStart: language === "ko" ? "워크플로우 시작점 선택" : "Select Workflow Start Point",
        startDescription: language === "ko"
            ? "거장 RAG 기반 세계관 컨텐츠 생성의 3가지 진입점 중 하나를 선택하세요."
            : "Choose one of three entry points for master's RAG-based worldbuilding content creation.",
        dagToggle: language === "ko" ? "DAG 캔버스" : "DAG Canvas",
        standaloneTools: language === "ko" ? "독립 도구" : "Standalone Tools",
    };

    // Workflow start handlers
    const handleStartWorkflow = useCallback((startOption: typeof FLOW_START_OPTIONS[number]) => {
        const phaseMap: Record<string, "START_4D" | "START_STORY" | "START_1D"> = {
            "reference-decoder": "START_4D",
            "story-architect": "START_STORY",
            "prompt-alchemy": "START_1D",
        };
        const event = phaseMap[startOption.key];
        if (event) {
            sendWorkflow({ type: event });
        }
    }, [sendWorkflow]);

    // Get current phase for DAG canvas
    const currentPhase = workflowState.context.currentPhase;

    // Handle phase click from sidebar
    const handlePhaseClick = useCallback((phase: WorkflowPhase) => {
        console.log("[Flow] Phase clicked:", phase);
        // If idle and valid start phase, start the workflow
        if (workflowState.matches("idle")) {
            const phaseMap: Record<string, "START_4D" | "START_STORY" | "START_1D" | null> = {
                "4D": "START_4D",
                "Story": "START_STORY",
                "1D": "START_1D",
            };
            const event = phaseMap[phase];
            if (event) {
                sendWorkflow({ type: event });
            }
        }
    }, [workflowState, sendWorkflow]);

    // Get workflow state for sidebar
    const getWorkflowStateForSidebar = useCallback((): "idle" | "running" | "completed" | "error" => {
        if (workflowState.matches("idle")) return "idle";
        if (workflowState.matches("completed")) return "completed";
        if (workflowState.matches("error")) return "error";
        return "running";
    }, [workflowState]);

    // Handle workflow control actions from sidebar
    const handleWorkflowControl = useCallback((action: "play" | "pause" | "reset") => {
        if (action === "reset") {
            sendWorkflow({ type: "RESET" });
        }
        // Note: play/pause would require additional state machine events
    }, [sendWorkflow]);

    // 🆕 Save workflow results as template
    const handleSaveAsTemplate = async () => {
        if (workflowResults.length === 0 || !templateTitle.trim()) return;

        setIsSavingTemplate(true);
        try {
            // Merge all inputs and outputs from workflow results
            const mergedInputs: Record<string, unknown> = {};
            const mergedOutputs: Record<string, unknown> = {};

            const getPresetPrefix = (dimension: string): string | null => {
                const code = dimensionIdToCode(dimension);
                if (!code) return null;
                return `${code.replace(/-/g, "_")}_`;
            };

            workflowResults.forEach(result => {
                Object.entries(result.inputs).forEach(([k, v]) => { mergedInputs[k] = v; });
                Object.entries(result.output).forEach(([k, v]) => { mergedOutputs[k] = v; });
                const prefix = getPresetPrefix(result.dimension);
                if (prefix) {
                    Object.entries(result.inputs).forEach(([k, v]) => {
                        mergedInputs[`${prefix}${k}`] = v;
                    });
                }
            });

            const normalizedSequence = workflowResults
                .map((result) => normalizeWorkflowDimension(result.dimension) ?? result.dimension)
                .filter(Boolean) as string[];

            const normalizedToolSequence = workflowResults
                .map((result) => result.toolName)
                .filter(Boolean);

            if (normalizedSequence.length === 0) {
                throw new Error("워크플로우 차원 순서를 확인할 수 없습니다.");
            }

            const response = await api.createSingularityTemplate({
                title: templateTitle.trim(),
                description: templateDescription.trim() || `${workflowResults.length}개 차원 워크플로우 템플릿`,
                dimension_source: normalizedSequence[0] || workflowResults[0]?.dimension || "1D",
                dimension_sequence: normalizedSequence,
                tool_sequence: normalizedToolSequence,
                input_preset: mergedInputs,
                output_example: mergedOutputs,
                tags: templateTags.split(",").map(t => t.trim()).filter(Boolean),
                category: "user_created",
            });

            console.log("[Flow] Template saved:", response);
            setSavedTemplateId(response.id);  // 🆕 Store for singularity link
            setTemplateSaveSuccess(true);
            setTemplateSaveError(null);
            // Auto-close after 5 seconds (longer for user to see link)
            setTimeout(() => {
                setShowTemplateModal(false);
                setTemplateSaveSuccess(false);
                setSavedTemplateId(null);
                setTemplateTitle("");
                setTemplateDescription("");
                setTemplateTags("");
            }, 5000);
        } catch (err) {
            console.error("[Flow] Template save failed:", err);
            setTemplateSaveError(err instanceof Error ? err.message : "템플릿 저장에 실패했습니다. 다시 시도해주세요.");
        } finally {
            setIsSavingTemplate(false);
        }
    };

    // Copy to clipboard with error handling
    const copyToClipboard = async (text: string, fieldId: string) => {
        try {
            if (!text || typeof text !== 'string') return;
            await navigator.clipboard.writeText(text);
            setCopiedField(fieldId);
            setTimeout(() => setCopiedField(null), 2000);
        } catch (err) {
            console.error('[Flow] Clipboard copy failed:', err);
            // Fallback: try execCommand (legacy)
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                setCopiedField(fieldId);
                setTimeout(() => setCopiedField(null), 2000);
            } catch {
                // Silent fail
            }
        }
    };

    // === Agent Workflow Event Handlers ===

    // Helper: Clear workflow state (shared by handleWorkflowStart and handleWorkflowCreated)
    const clearWorkflowState = useCallback(() => {
        try {
            if (workflowRef.current) {
                workflowRef.current.clearCars();
            }
            carIdMapRef.current.clear();
            setWorkflowResults([]);
            setShowResults(false);
            setExpandedResult(null);
        } catch (err) {
            console.error('[Flow] Error clearing workflow state:', err);
            return false;
        }
        return true;
    }, []);

    const handleWorkflowStart = useCallback((data: WorkflowStartEvent) => {
        console.log("[Flow] Workflow started:", data);

        // Defensive: validate data
        if (!data || typeof data !== 'object') {
            console.warn('[Flow] Invalid workflow start data');
            return;
        }

        clearWorkflowState();
    }, [clearWorkflowState]);

    // Handle workflow structure created (from create_workflow tool)
    const handleWorkflowCreated = useCallback((data: WorkflowCreatedEvent) => {
        console.log("[Flow] Workflow created:", data);

        // Defensive: validate data
        if (!data || typeof data !== 'object' || !Array.isArray(data.nodes)) {
            console.warn('[Flow] Invalid workflow created data');
            return;
        }

        // Clear existing state
        if (!clearWorkflowState()) return;

        // Add cars from workflow nodes
        data.nodes.forEach((node, idx) => {
            const toolInfo = getToolInfoFromAgentTool(node.tool_name);
            if (!toolInfo || !workflowRef.current) return;

            const normalizedDimension = normalizeWorkflowDimension(toolInfo.dimension || node.dimension || node.tool_name);
            if (!normalizedDimension) {
                console.warn("[Flow] Unsupported workflow dimension:", node.tool_name);
                return;
            }

            const carId = workflowRef.current.addCar({
                toolId: AGENT_TOOL_TO_TOOL_ID[node.tool_name] || node.tool_name,
                dimension: normalizedDimension as WorkflowDimension,
                displayName: toolInfo.displayName,
                icon: toolInfo.icon,
                color: toolInfo.color,
                status: idx === 0 ? "ready" : "pending",
                inputs: {},
            });

            if (carId) {
                carIdMapRef.current.set(idx, carId);
            }
        });

        console.log(`[Flow] Created ${data.nodes.length} cars from workflow structure`);
    }, [clearWorkflowState, getToolInfoFromAgentTool]);

    const handleWorkflowStep = useCallback((event: WorkflowStepEvent) => {
        console.log("[Flow] Workflow step:", event);

        if (!workflowRef.current) return;

        const toolInfo = getToolInfoFromAgentTool(event.tool_name) || {
            displayName: event.dimension_name,
            displayNameEn: event.dimension_name,
            icon: "zap",
            color: "zinc",
            dimension: event.dimension,
        };

        if (event.status === "start") {
            // Add new car with executing status
            const normalizedDimension = normalizeWorkflowDimension(toolInfo.dimension || event.dimension || event.tool_name);
            if (!normalizedDimension) {
                console.warn("[Flow] Unsupported workflow dimension:", event.tool_name);
                return;
            }

            const carId = workflowRef.current.addCar({
                toolId: AGENT_TOOL_TO_TOOL_ID[event.tool_name] || event.tool_name,
                dimension: normalizedDimension as WorkflowDimension,
                displayName: toolInfo.displayName,
                icon: toolInfo.icon,
                color: toolInfo.color,
                status: "executing",
                inputs: {},
            });
            // Track car ID by step number
            carIdMapRef.current.set(event.step, carId);
        } else if (event.status === "complete") {
            // Update existing car to completed
            const carId = carIdMapRef.current.get(event.step);
            if (carId) {
                workflowRef.current.updateCarStatus(carId, "completed", {
                    preview: event.output_preview,
                    credit_cost: event.credit_cost,
                });
            }
        } else if (event.status === "error") {
            // Update existing car to failed
            const carId = carIdMapRef.current.get(event.step);
            if (carId) {
                workflowRef.current.updateCarStatus(carId, "failed");
            }
        }
    }, [getToolInfoFromAgentTool]);

    const handleWorkflowComplete = useCallback((data: { total_credits: number; success_count: number }) => {
        console.log("[Flow] Workflow completed:", data);
        // Show results panel if there are results
        if (data.success_count > 0) {
            setShowResults(true);
        }
    }, []);

    // Handle tool result from agent
    const handleToolResult = useCallback((result: {
        name: string;
        status: string;
        output: Record<string, unknown>;
        arguments?: Record<string, unknown>;  // 🔧 Fixed: matches AgentChatAccordion
    }) => {
        console.log("[Flow] Tool result:", result);

        // Defensive: validate result
        if (!result || typeof result !== 'object') {
            console.warn('[Flow] Invalid tool result');
            return;
        }

        const { name, status, output, arguments: toolArguments } = result;

        // Only process workflow tool results
        if (!name || typeof name !== 'string') return;
        const toolInfo = getToolInfoFromAgentTool(name);
        if (!toolInfo) return;

        // Accept both 'completed' and 'success' status (case-insensitive)
        const normalizedStatus = (status || '').toLowerCase();
        if (normalizedStatus !== 'completed' && normalizedStatus !== 'success') return;

        // Ensure output is a valid object
        const safeOutput = (output && typeof output === 'object' && !Array.isArray(output))
            ? output
            : {};

        // Extract inputs (from 'arguments' field sent by backend)
        const safeInputs = (toolArguments && typeof toolArguments === 'object' && !Array.isArray(toolArguments))
            ? toolArguments
            : {};

        setWorkflowResults(prev => {
            try {
                // Avoid duplicates
                if (prev.some(r => r.toolName === name)) {
                    return prev.map(r => r.toolName === name
                        ? { ...r, output: safeOutput, inputs: safeInputs }
                        : r
                    );
                }
                return [...prev, {
                    dimension: toolInfo.dimension,
                    dimensionName: toolInfo.displayName,
                    toolName: name,
                    inputs: safeInputs,
                    output: safeOutput,
                    executedAt: new Date(),
                }];
            } catch (err) {
                console.error('[Flow] Error updating workflow results:', err);
                return prev;
            }
        });
    }, [getToolInfoFromAgentTool]);

    // Render output value based on type with error handling
    const renderOutputValue = (key: string, value: unknown, resultId: string) => {
        const fieldId = `${resultId}-${key}`;

        // Handle null/undefined
        if (value === null || value === undefined) {
            return <span className="text-xs text-[var(--fg-muted)] italic">(없음)</span>;
        }

        if (typeof value === "string") {
            const displayValue = value.trim() || '(빈 문자열)';
            return (
                <div className="relative group">
                    <div className="p-3 rounded-lg bg-[var(--surface-1)] border border-[var(--border-subtle)] text-sm text-[var(--fg-0)] whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {displayValue}
                    </div>
                    {value.trim() && (
                        <button
                            onClick={() => copyToClipboard(value, fieldId)}
                            className="absolute top-2 right-2 p-1.5 rounded-md bg-[var(--surface-1)] opacity-0 group-hover:opacity-100 hover:bg-[var(--surface-2)] transition-all"
                        >
                            {copiedField === fieldId ? (
                                <Check className={`h-3.5 w-3.5 ${SUCCESS_TONE.text}`} />
                            ) : (
                                <Copy className="h-3.5 w-3.5 text-[var(--fg-muted)]" />
                            )}
                        </button>
                    )}
                </div>
            );
        }

        if (typeof value === "number" || typeof value === "boolean") {
            return <span className="text-sm text-[var(--fg-0)]">{String(value)}</span>;
        }

        if (Array.isArray(value)) {
            if (value.length === 0) {
                return <span className="text-xs text-[var(--fg-muted)] italic">(빈 배열)</span>;
            }
            return (
                <div className="space-y-2">
                    {value.slice(0, 20).map((item, i) => (
                        <div key={i} className="p-2 rounded-lg bg-[var(--surface-1)] border border-[var(--border-subtle)] text-xs text-[var(--fg-muted)] overflow-x-auto">
                            {safeStringify(item)}
                        </div>
                    ))}
                    {value.length > 20 && (
                        <div className="text-xs text-[var(--fg-muted)] italic">...외 {value.length - 20}개 항목</div>
                    )}
                </div>
            );
        }

        if (typeof value === "object" && value !== null) {
            const stringified = safeStringify(value);
            return (
                <div className="p-3 rounded-lg bg-[var(--surface-1)] border border-[var(--border-subtle)] text-xs text-[var(--fg-muted)] font-mono whitespace-pre overflow-x-auto max-h-64">
                    {stringified}
                </div>
            );
        }

        return <span className="text-sm text-[var(--fg-0)]">{String(value)}</span>;
    };

    return (
        <AppShell showTopBar={false} showChokki={false}>
            <div className="relative min-h-screen flex">
                {/* Aurora Background */}
                <AuroraBackground />

                {/* Mobile Sidebar Toggle */}
                <button
                    onClick={() => setShowMobileSidebar(!showMobileSidebar)}
                    className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-xl bg-[var(--surface-1)]/90 backdrop-blur-xl border border-[var(--border-subtle)] shadow-lg"
                >
                    <PanelLeft className="w-5 h-5 text-[var(--fg-muted)]" />
                </button>

                {/* Sidebar - Desktop */}
                <div className="hidden lg:block relative z-20">
                    <FlowSidebar
                        activePhase={currentPhase}
                        chainData={workflowState.context.chainData}
                        workflowState={getWorkflowStateForSidebar()}
                        onStartSelect={(phase) => {
                            const option = FLOW_START_OPTIONS.find(o => {
                                const phaseMap: Record<string, WorkflowPhase> = {
                                    "reference-decoder": "4D",
                                    "story-architect": "Story",
                                    "prompt-alchemy": "1D",
                                };
                                return phaseMap[o.key] === phase;
                            });
                            if (option) handleStartWorkflow(option);
                        }}
                        onPhaseClick={handlePhaseClick}
                        onWorkflowControl={handleWorkflowControl}
                        language={language}
                        collapsed={sidebarCollapsed}
                        onCollapsedChange={setSidebarCollapsed}
                    />
                </div>

                {/* Sidebar - Mobile Overlay */}
                <AnimatePresence>
                    {showMobileSidebar && (
                        <>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setShowMobileSidebar(false)}
                                className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm lg:hidden"
                            />
                            <motion.div
                                initial={{ x: -320 }}
                                animate={{ x: 0 }}
                                exit={{ x: -320 }}
                                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                                className="fixed left-0 top-0 bottom-0 z-40 lg:hidden"
                            >
                                <FlowSidebar
                                    activePhase={currentPhase}
                                    chainData={workflowState.context.chainData}
                                    workflowState={getWorkflowStateForSidebar()}
                                    onStartSelect={(phase) => {
                                        const option = FLOW_START_OPTIONS.find(o => {
                                            const phaseMap: Record<string, WorkflowPhase> = {
                                                "reference-decoder": "4D",
                                                "story-architect": "Story",
                                                "prompt-alchemy": "1D",
                                            };
                                            return phaseMap[o.key] === phase;
                                        });
                                        if (option) handleStartWorkflow(option);
                                        setShowMobileSidebar(false);
                                    }}
                                    onPhaseClick={(phase) => {
                                        handlePhaseClick(phase);
                                        setShowMobileSidebar(false);
                                    }}
                                    onWorkflowControl={handleWorkflowControl}
                                    language={language}
                                    collapsed={false}
                                />
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>

                {/* Main Content Container */}
                <div className="relative z-10 flex-1 min-h-screen px-4 py-6 sm:px-6 sm:py-8 pb-20 overflow-y-auto">
                    <div className="mx-auto max-w-6xl">

                        {/* Page Header */}
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-6"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                                        <Workflow className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <h1 className="text-2xl font-bold text-[var(--fg-0)]">
                                            {language === "ko" ? "디멘션 플로우" : "Dimension Flow"}
                                        </h1>
                                        <p className="text-sm text-[var(--fg-muted)]">
                                            {language === "ko"
                                                ? "거장 RAG 기반 세계관 컨텐츠 생성 워크플로우"
                                                : "Master's RAG-based worldbuilding workflow"
                                            }
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => setShowDagCanvas(!showDagCanvas)}
                                        className={`
                                            flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                                            transition-all duration-200
                                            ${showDagCanvas
                                                ? "bg-gradient-to-r from-violet-500 to-cyan-500 text-white shadow-lg shadow-violet-500/20"
                                                : "bg-[var(--surface-1)] border border-[var(--border-subtle)] text-[var(--fg-muted)] hover:bg-[var(--surface-2)]"
                                            }
                                        `}
                                    >
                                        <LayoutGrid className="w-4 h-4" />
                                        {labels.dagToggle}
                                    </button>
                                </div>
                            </div>
                        </motion.div>

                        {/* Template Loading Indicator */}
                        {isLoadingTemplate && (
                            <div className="card-glass p-4 mb-4 flex items-center gap-3">
                                <Loader2 className={`w-5 h-5 animate-spin ${BRAND_TONE.text}`} />
                                <span className="text-sm text-[var(--fg-muted)]">템플릿을 불러오는 중...</span>
                            </div>
                        )}

                        {/* Template Load Error */}
                        {templateLoadError && !isLoadingTemplate && (
                            <div className={`card-glass p-4 mb-4 border ${ERROR_TONE.border} ${ERROR_TONE.bgSubtle}`}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-xl ${ERROR_TONE.bg} flex items-center justify-center`}>
                                            <X className={`w-5 h-5 ${ERROR_TONE.text}`} />
                                        </div>
                                        <div>
                                            <div className={`text-sm font-bold ${ERROR_TONE.text}`}>템플릿 로드 실패</div>
                                            <div className={`text-xs ${ERROR_TONE.textSoft}`}>{templateLoadError}</div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setTemplateLoadError(null)}
                                        className="text-xs text-[var(--fg-subtle)] hover:text-[var(--fg-0)] transition-colors"
                                    >
                                        닫기
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Template Applied Banner */}
                        {loadedTemplate && templateApplied && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`card-glass p-4 mb-4 border ${BRAND_TONE.border} ${BRAND_TONE.bgSubtle}`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-xl ${BRAND_TONE.bg} flex items-center justify-center`}>
                                            <Sparkles className={`w-5 h-5 ${BRAND_TONE.text}`} />
                                        </div>
                                        <div>
                                            <div className="text-sm font-bold text-[var(--fg-0)]">{loadedTemplate.title}</div>
                                            <div className="text-xs text-[var(--fg-muted)]">
                                                {appliedTemplateSequence.length > 0
                                                    ? `${appliedTemplateSequence.join(" → ")} 워크플로우가 적용되었습니다`
                                                    : "적용 가능한 차원이 없어 워크플로우가 비어 있습니다"}
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => {
                                            setLoadedTemplate(null);
                                            setTemplateApplied(false);
                                            setAppliedTemplateSequence([]);
                                            setTemplateSkippedDimensions([]);
                                            workflowRef.current?.clearCars();
                                        }}
                                        className="text-xs text-[var(--fg-subtle)] hover:text-[var(--fg-0)] transition-colors"
                                    >
                                        초기화
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {/* Template Skipped Dimensions Warning */}
                        {templateSkippedDimensions.length > 0 && (
                            <div className={`card-glass p-4 mb-4 border ${WARNING_TONE.border} ${WARNING_TONE.bgSubtle}`}>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-10 h-10 rounded-xl ${WARNING_TONE.bg} flex items-center justify-center`}>
                                            <AlertCircle className={`w-5 h-5 ${WARNING_TONE.text}`} />
                                        </div>
                                        <div>
                                            <div className={`text-sm font-bold ${WARNING_TONE.text}`}>일부 차원은 적용되지 않았습니다</div>
                                            <div className={`text-xs ${WARNING_TONE.textSoft}`}>
                                                {templateSkippedDimensions.join(", ")} 차원은 현재 워크플로우에서 지원되지 않아 제외되었습니다
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => setTemplateSkippedDimensions([])}
                                        className="text-xs text-[var(--fg-subtle)] hover:text-[var(--fg-0)] transition-colors"
                                    >
                                        닫기
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Workflow Start Options - 3옵션 시작점 고정 */}
                        {!loadedTemplate && !templateApplied && workflowState.matches("idle") && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="card-glass p-6 mb-6"
                            >
                                <div className="flex items-center justify-between mb-4">
                                    <div>
                                        <h2 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
                                            <Workflow className={`w-5 h-5 ${BRAND_TONE.text}`} />
                                            {labels.selectStart}
                                        </h2>
                                        <p className="text-sm text-[var(--fg-muted)] mt-1">
                                            {labels.startDescription}
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => setShowDagCanvas(!showDagCanvas)}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                            showDagCanvas
                                                ? `${BRAND_TONE.solid} text-[var(--fg-on-emphasis)]`
                                                : `${BRAND_TONE.bg} ${BRAND_TONE.textSoft} ${BRAND_TONE.hoverBg}`
                                        }`}
                                    >
                                        <LayoutGrid className="w-4 h-4" />
                                        {labels.dagToggle}
                                    </button>
                                </div>

                                {/* 3 Start Options */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                                    {FLOW_START_OPTIONS.map((option) => {
                                        const StartIcon = option.iconName === "search" ? Search
                                            : option.iconName === "layers" ? Layers
                                            : option.iconName === "wand" ? Wand2
                                            : Sparkles;

                                        return (
                                            <button
                                                key={option.key}
                                                onClick={() => handleStartWorkflow(option)}
                                                className={`
                                                    p-5 rounded-xl border-2 border-[var(--border-subtle)]
                                                    bg-[var(--surface-1)] hover:bg-[var(--surface-2)]
                                                    transition-all hover:scale-[1.02] hover:shadow-lg
                                                    text-left group
                                                `}
                                            >
                                                <div className={`
                                                    w-12 h-12 rounded-xl ${BRAND_TONE.bg}
                                                    flex items-center justify-center mb-3
                                                    group-hover:scale-110 transition-transform
                                                `}>
                                                    <StartIcon className={`w-6 h-6 ${BRAND_TONE.text}`} />
                                                </div>
                                                <div className={`text-sm font-bold ${BRAND_TONE.text} mb-1`}>
                                                    {option.dimension}
                                                </div>
                                                <div className="text-base font-semibold text-[var(--fg-0)] mb-2">
                                                    {language === "ko" ? option.name : option.nameEn}
                                                </div>
                                                <p className="text-sm text-[var(--fg-muted)]">
                                                    {language === "ko" ? option.description : option.descriptionEn}
                                                </p>
                                            </button>
                                        );
                                    })}
                                </div>

                                {/* Standalone Tools Section */}
                                <div className="border-t border-[var(--border-subtle)] pt-4">
                                    <h3 className="text-sm font-medium text-[var(--fg-muted)] mb-3">
                                        {labels.standaloneTools}
                                    </h3>
                                    <div className="flex gap-3">
                                        {STANDALONE_TOOLS.map((tool) => (
                                            <Link
                                                key={tool.key}
                                                href={`/dimension/abyss`}
                                                className={`
                                                    flex items-center gap-3 px-4 py-2.5 rounded-lg
                                                    border border-[var(--border-subtle)]
                                                    bg-[var(--surface-1)] hover:bg-[var(--surface-2)]
                                                    transition-colors text-sm
                                                `}
                                            >
                                                <div className={`w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center`}>
                                                    <Moon className="w-4 h-4 text-violet-400" />
                                                </div>
                                                <div>
                                                    <div className="font-medium text-[var(--fg-0)]">
                                                        {language === "ko" ? tool.name : tool.nameEn}
                                                    </div>
                                                    <div className="text-xs text-[var(--fg-muted)]">
                                                        {tool.dimension}
                                                    </div>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {/* DAG Canvas (Toggleable) */}
                        <AnimatePresence>
                            {showDagCanvas && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mb-6 overflow-hidden"
                                >
                                    <div className="card-glass p-1">
                                        <WorkflowCanvas
                                            activePhase={currentPhase}
                                            chainData={workflowState.context.chainData}
                                            onNodeClick={(phase) => {
                                                console.log("[Flow] Node clicked:", phase);
                                            }}
                                            onStartSelect={(phase) => {
                                                const eventMap: Record<WorkflowPhase, "START_4D" | "START_STORY" | "START_1D" | null> = {
                                                    "4D": "START_4D",
                                                    "Story": "START_STORY",
                                                    "1D": "START_1D",
                                                    "AD": null,
                                                    "2D": null,
                                                    "Sound": null,
                                                    "3D": null,
                                                    "VEO": null,
                                                    "QC": null,
                                                };
                                                const event = eventMap[phase];
                                                if (event) {
                                                    sendWorkflow({ type: event });
                                                }
                                            }}
                                            readOnly={!workflowState.matches("idle")}
                                        />
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Main Workflow View */}
                        <div className="card-glass p-1">
                            <div className="overflow-hidden p-6 sm:p-8">
                                <TrainWorkflowView
                                    ref={workflowRef}
                                    onComplete={(results) => {
                                        console.log("Workflow completed:", results);
                                    }}
                                />
                            </div>
                        </div>

                        {/* Workflow Results Panel */}
                        <AnimatePresence>
                            {showResults && workflowResults.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 20 }}
                                    transition={{ duration: 0.3 }}
                                    className="mt-8"
                                >
                                    <div className="card-glass p-1">
                                        <div className="p-6">
                                            {/* Results Header */}
                                            <div className="flex items-center justify-between mb-6">
                                                <h3 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
                                                    <Sparkles className={`h-5 w-5 ${BRAND_TONE.text}`} />
                                                    {labels.results}
                                                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${SUCCESS_TONE.bg} ${SUCCESS_TONE.text}`}>
                                                        {workflowResults.length}개 완료
                                                    </span>
                                                </h3>
                                                <div className="flex items-center gap-2">
                                                    {/* 🆕 Save as Template Button */}
                                                    <button
                                                        onClick={() => setShowTemplateModal(true)}
                                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${BRAND_TONE.bg} ${BRAND_TONE.hoverBg} ${BRAND_TONE.textSoft}`}
                                                    >
                                                        <Save className="h-3.5 w-3.5" />
                                                        템플릿 저장
                                                    </button>
                                                    <button
                                                        onClick={() => setShowResults(false)}
                                                        className="p-1.5 rounded-lg hover:bg-[var(--surface-2)] transition-colors"
                                                    >
                                                        <X className="h-4 w-4 text-[var(--fg-muted)]" />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Results List */}
                                            <div className="space-y-4">
                                                {workflowResults.map((result) => {
                                                    const isExpanded = expandedResult === result.toolName;
                                                    const toolInfo = getToolInfoFromAgentTool(result.toolName);
                                                    const Icon = ICON_COMPONENTS[toolInfo?.icon || "sparkles"];
                                                    const dimensionValue = toolInfo?.dimension ?? result.dimension;
                                                    const dimensionCode = dimensionValue
                                                        ? dimensionIdToCode(dimensionValue)
                                                        : null;
                                                    const toneKey = dimensionCode
                                                        ? getDimensionToken(dimensionCode).tailwindKey
                                                        : null;
                                                    const iconToneClass = toneKey
                                                        ? `bg-${toneKey}/20 text-${toneKey}`
                                                        : "bg-[var(--surface-1)] text-[var(--fg-muted)]";
                                                    const labelToneClass = toneKey
                                                        ? `text-${toneKey}`
                                                        : "text-[var(--fg-muted)]";

                                                    return (
                                                        <div
                                                            key={result.toolName}
                                                            className="rounded-xl border border-[var(--border-subtle)] bg-[var(--surface-1)] overflow-hidden"
                                                        >
                                                            {/* Result Header */}
                                                            <button
                                                                onClick={() => setExpandedResult(isExpanded ? null : result.toolName)}
                                                                className="w-full flex items-center justify-between p-4 hover:bg-[var(--surface-2)] transition-colors"
                                                            >
                                                                <div className="flex items-center gap-3">
                                                                    <div
                                                                        className={`h-10 w-10 rounded-xl flex items-center justify-center ${iconToneClass}`}
                                                                    >
                                                                        {Icon}
                                                                    </div>
                                                                    <div className="text-left">
                                                                        <div className="flex items-center gap-2">
                                                                            <span className={`text-xs font-bold ${labelToneClass}`}>
                                                                                {result.dimension}
                                                                            </span>
                                                                            <span className="text-sm font-medium text-[var(--fg-0)]">
                                                                                {result.dimensionName}
                                                                            </span>
                                                                        </div>
                                                                        <p className="text-xs text-[var(--fg-muted)]">
                                                                            {Object.keys(result.output).length}개 필드 생성됨
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-2">
                                                                    {/* 🆕 Download Buttons */}
                                                                        <div className="flex gap-1" onClick={e => e.stopPropagation()}>
                                                                            <button
                                                                                onClick={() => downloadResultAsJSON(result)}
                                                                                className="p-1.5 rounded-lg bg-[var(--surface-1)] hover:bg-[var(--surface-2)] transition-colors"
                                                                                title="JSON으로 다운로드"
                                                                            >
                                                                                <Download className="h-3.5 w-3.5 text-[var(--fg-subtle)]" />
                                                                            </button>
                                                                            <button
                                                                                onClick={() => downloadResultAsMarkdown(result)}
                                                                                className="p-1.5 rounded-lg bg-[var(--surface-1)] hover:bg-[var(--surface-2)] transition-colors"
                                                                                title="Markdown으로 다운로드"
                                                                            >
                                                                                <span className="text-[10px] font-bold text-[var(--fg-subtle)]">MD</span>
                                                                            </button>
                                                                        </div>
                                                                        <ChevronDown
                                                                            className={`h-5 w-5 text-[var(--fg-muted)] transition-transform ${isExpanded ? "rotate-180" : ""}`}
                                                                        />
                                                                </div>
                                                            </button>

                                                            {/* Result Content */}
                                                            <AnimatePresence>
                                                                {isExpanded && (
                                                                    <motion.div
                                                                        initial={{ height: 0, opacity: 0 }}
                                                                        animate={{ height: "auto", opacity: 1 }}
                                                                        exit={{ height: 0, opacity: 0 }}
                                                                        transition={{ duration: 0.2 }}
                                                                        className="overflow-hidden"
                                                                    >
                                                                        <div className="p-4 pt-0 space-y-4 border-t border-[var(--border-subtle)]">
                                                                            {/* 🆕 Inputs Section */}
                                                                            {result.inputs && Object.keys(result.inputs).length > 0 && (
                                                                                <details className="group">
                                                                                    <summary className={`text-xs font-medium cursor-pointer transition-colors flex items-center gap-1.5 ${BRAND_TONE.text} hover:text-[var(--color-brand-primary)]/80`}>
                                                                                        <span>📝 입력 프롬프트</span>
                                                                                        <ChevronDown className="h-3 w-3 group-open:rotate-180 transition-transform" />
                                                                                    </summary>
                                                                                    <div className={`mt-2 p-3 rounded-lg space-y-2 ${BRAND_TONE.bgSubtle} ${BRAND_TONE.border}`}>
                                                                                        {Object.entries(result.inputs).map(([key, value]) => (
                                                                                            <div key={key}>
                                                                                                <span className={`text-[10px] uppercase tracking-wider ${BRAND_TONE.textMuted}`}>{key.replace(/_/g, " ")}</span>
                                                                                                <p className="text-xs text-[var(--fg-0)]">
                                                                                                    {typeof value === "string" ? value : JSON.stringify(value)}
                                                                                                </p>
                                                                                            </div>
                                                                                        ))}
                                                                                    </div>
                                                                                </details>
                                                                            )}

                                                                            {/* Outputs Section */}
                                                                            {Object.entries(result.output).map(([key, value]) => (
                                                                                <div key={key}>
                                                                                    <label className="text-xs font-medium text-[var(--fg-muted)] uppercase tracking-wider mb-2 block">
                                                                                        {key.replace(/_/g, " ")}
                                                                                    </label>
                                                                                    {renderOutputValue(key, value, result.toolName)}
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* Flow-specific Chokki Agent with workflow callbacks */}
                <AgentChatAccordion
                    initialMessage={labels.initialMessage}
                    onWorkflowStart={handleWorkflowStart}
                    onWorkflowStep={handleWorkflowStep}
                    onWorkflowComplete={handleWorkflowComplete}
                    onWorkflowCreated={handleWorkflowCreated}
                    onToolResult={handleToolResult}
                    templateContext={loadedTemplate}
                />

                {/* 🆕 Template Save Modal */}
                <AnimatePresence>
                    {showTemplateModal && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 flex items-center justify-center dialog-overlay"
                            onClick={() => setShowTemplateModal(false)}
                        >
                            <motion.div
                                initial={{ scale: 0.95, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.95, opacity: 0 }}
                                onClick={e => e.stopPropagation()}
                                className="w-full max-w-md mx-4 dialog-panel rounded-[1.5rem] shadow-2xl overflow-hidden"
                            >
                                {/* Modal Header */}
                                <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-subtle)]">
                                    <h3 className="text-lg font-bold text-[var(--fg-0)] flex items-center gap-2">
                                        <Save className={`h-5 w-5 ${BRAND_TONE.text}`} />
                                        싱귤래리티 템플릿 저장
                                    </h3>
                                    <button
                                        onClick={() => setShowTemplateModal(false)}
                                        className="p-1.5 rounded-lg hover:bg-[var(--surface-2)] transition-colors"
                                    >
                                        <X className="h-4 w-4 text-[var(--fg-subtle)]" />
                                    </button>
                                </div>

                                {/* Modal Body */}
                                <div className="p-6 space-y-4">
                                    {templateSaveSuccess ? (
                                        <div className="text-center py-8">
                                            <div className={`h-16 w-16 mx-auto mb-4 rounded-full ${SUCCESS_TONE.bg} flex items-center justify-center`}>
                                                <Check className={`h-8 w-8 ${SUCCESS_TONE.text}`} />
                                            </div>
                                            <p className="text-lg font-medium text-[var(--fg-0)]">템플릿 저장 완료!</p>
                                            <p className="text-sm text-[var(--fg-muted)] mt-1 mb-4">싱귤래리티에서 확인하세요</p>

                                            {/* Singularity & Constellation Links */}
                                            <div className="flex flex-col gap-2">
                                                <a
                                                    href="/singularity"
                                                    className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-[var(--fg-on-emphasis)] text-sm font-medium transition-colors ${BRAND_TONE.solid} ${BRAND_TONE.hoverBg}`}
                                                >
                                                    <Sparkles className="h-4 w-4" />
                                                    싱귤래리티로 이동
                                                </a>
                                                {savedTemplateId && (
                                                    <a
                                                        href={`/constellation?new=true&singularity=${savedTemplateId}`}
                                                        className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-[var(--fg-on-emphasis)] text-sm font-medium transition-colors ${INFO_TONE.solid} ${INFO_TONE.hover}`}
                                                    >
                                                        <Sparkles className="h-4 w-4" />
                                                        별자리로 확장하기
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <>
                                            <div>
                                                <label className="text-xs font-medium text-[var(--fg-muted)] mb-1.5 block">
                                                    템플릿 제목 *
                                                </label>
                                                <input
                                                    type="text"
                                                    value={templateTitle}
                                                    onChange={e => setTemplateTitle(e.target.value)}
                                                    placeholder="예: 시네마틱 프롬프트 워크플로우"
                                                    className="input w-full text-sm"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-medium text-[var(--fg-muted)] mb-1.5 block">
                                                    설명
                                                </label>
                                                <textarea
                                                    value={templateDescription}
                                                    onChange={e => setTemplateDescription(e.target.value)}
                                                    placeholder="워크플로우 템플릿에 대한 설명을 입력하세요"
                                                    rows={3}
                                                    className="input w-full text-sm resize-none"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs font-medium text-[var(--fg-muted)] mb-1.5 block">
                                                    태그 (쉼표로 구분)
                                                </label>
                                                <input
                                                    type="text"
                                                    value={templateTags}
                                                    onChange={e => setTemplateTags(e.target.value)}
                                                    placeholder="예: cinematic, veo, prompt"
                                                    className="input w-full text-sm"
                                                />
                                            </div>

                                            {/* Workflow Summary */}
                                            <div className={`p-3 rounded-lg ${BRAND_TONE.bgSubtle} ${BRAND_TONE.border}`}>
                                                <p className={`text-xs font-medium mb-1 ${BRAND_TONE.textSoft}`}>포함된 도구</p>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {workflowResults.map(r => (
                                                        <span key={r.toolName} className={`px-2 py-0.5 rounded-md text-xs ${BRAND_TONE.bg} ${BRAND_TONE.textSoft}`}>
                                                            {r.dimension}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>

                                {/* Modal Footer */}
                                {!templateSaveSuccess && (
                                    <div className="px-6 py-4 border-t border-[var(--border-subtle)] space-y-3">
                                        {/* 🆕 Inline Error Display */}
                                        {templateSaveError && (
                                            <div className={`flex items-center gap-2 p-3 rounded-lg ${ERROR_TONE.bgSubtle} ${ERROR_TONE.border}`}>
                                                <span className={`text-xs ${ERROR_TONE.text}`}>⚠️</span>
                                                <span className={`text-xs flex-1 ${ERROR_TONE.text}`}>{templateSaveError}</span>
                                                <button
                                                    onClick={() => setTemplateSaveError(null)}
                                                    className={`text-xs ${ERROR_TONE.text} hover:opacity-80`}
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                        )}
                                        <div className="flex justify-end gap-3">
                                            <button
                                                onClick={() => setShowTemplateModal(false)}
                                                className="btn btn-secondary btn-size-default text-sm"
                                            >
                                                취소
                                            </button>
                                            <button
                                                onClick={handleSaveAsTemplate}
                                                disabled={!templateTitle.trim() || isSavingTemplate}
                                                className={`px-4 py-2 rounded-lg text-[var(--fg-on-emphasis)] text-sm font-medium transition-colors flex items-center gap-2 ${BRAND_TONE.solid} ${BRAND_TONE.hoverBg} disabled:opacity-60 disabled:cursor-not-allowed`}
                                            >
                                                {isSavingTemplate ? (
                                                    <>
                                                        <span className="h-4 w-4 border-2 spinner-on-emphasis rounded-full animate-spin" />
                                                        저장 중...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Save className="h-4 w-4" />
                                                        저장
                                                    </>
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </AppShell>
    );
}

// Coming Soon page for when Flow is disabled
function FlowComingSoon() {
    return (
        <AppShell>
            <AuroraBackground />
            <div className="min-h-screen flex items-center justify-center p-8 relative z-10">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-md text-center"
                >
                    <div className={`mx-auto w-20 h-20 rounded-2xl flex items-center justify-center mb-6 ${BRAND_TONE.bgSubtle} ${BRAND_TONE.border}`}>
                        <Construction className={`w-10 h-10 ${BRAND_TONE.text}`} />
                    </div>
                    <h1 className="text-3xl font-bold text-[var(--fg-0)] mb-3">
                        차원 플로우
                    </h1>
                    <p className={`text-lg mb-2 ${BRAND_TONE.textSoft}`}>
                        Coming Soon
                    </p>
                    <p className="text-[var(--fg-muted)] mb-8">
                        차원 플로우 기능은 현재 개발 중입니다.<br />
                        곧 여러 차원 도구를 조합하여 나만의 AI 파이프라인을 만들 수 있습니다.
                    </p>
                    <Link
                        href="/dimension"
                        className={`inline-flex items-center gap-2 px-6 py-3 rounded-xl text-[var(--fg-on-emphasis)] font-medium transition-colors ${BRAND_TONE.solid} ${BRAND_TONE.hoverBg}`}
                    >
                        <ArrowLeft className="w-4 h-4" />
                        차원 앱으로 돌아가기
                    </Link>
                </motion.div>
            </div>
        </AppShell>
    );
}

// Wrap with Suspense for useSearchParams
export default function FlowPage() {
    // Feature gate: show Coming Soon when Flow is disabled
    if (!FLOW_ENABLED) {
        return <FlowComingSoon />;
    }

    return (
        <Suspense fallback={
            <AppShell>
                <div className="min-h-screen flex items-center justify-center">
                    <Loader2 className={`w-8 h-8 animate-spin ${BRAND_TONE.text}`} />
                </div>
            </AppShell>
        }>
            <FlowPageContent />
        </Suspense>
    );
}
