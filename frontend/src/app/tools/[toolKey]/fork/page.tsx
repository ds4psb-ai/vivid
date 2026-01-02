"use client";

/**
 * Fork Tool Page
 * 
 * UX Hardening Features:
 * - Original tool display for reference
 * - Diff editor with syntax highlighting
 * - Real-time diff stats (added/removed/modified)
 * - Fork reason field
 * - Sybil warning preview
 * - Attribution score preview
 * - Confirmation with revenue sharing explanation
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft,
    GitFork,
    AlertTriangle,
    Check,
    Loader2,
    Info,
    Plus,
    Minus,
    RefreshCw,
    Shield,
    DollarSign,
} from "lucide-react";
import * as telemetryApi from "@/lib/telemetry-api";
import type { ToolManifest } from "@/lib/telemetry-api";

// =============================================================================
// Diff Stats Component
// =============================================================================

function DiffStats({
    added,
    removed,
    modified,
    diffScore,
}: {
    added: number;
    removed: number;
    modified: number;
    diffScore: number;
}) {
    const isSuspicious = diffScore < 5;

    return (
        <div
            className={`rounded-xl p-4 ${isSuspicious
                    ? "bg-yellow-500/10 border border-yellow-500/30"
                    : "bg-gray-800/50 border border-gray-700/50"
                }`}
        >
            <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-300">Diff Statistics</span>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">Score:</span>
                    <span
                        className={`text-lg font-bold ${isSuspicious ? "text-yellow-400" : "text-purple-400"
                            }`}
                    >
                        {diffScore.toFixed(1)}
                    </span>
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                    <Plus className="w-4 h-4 text-green-400" />
                    <span className="text-green-400 font-medium">{added}</span>
                    <span className="text-gray-500 text-sm">added</span>
                </div>
                <div className="flex items-center gap-2">
                    <Minus className="w-4 h-4 text-red-400" />
                    <span className="text-red-400 font-medium">{removed}</span>
                    <span className="text-gray-500 text-sm">removed</span>
                </div>
                <div className="flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 text-blue-400" />
                    <span className="text-blue-400 font-medium">{modified}</span>
                    <span className="text-gray-500 text-sm">modified</span>
                </div>
            </div>

            {isSuspicious && (
                <div className="mt-4 flex items-start gap-2 text-yellow-300 text-sm">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <p>
                        This fork has minimal changes and may be flagged for review.
                        Consider making more substantial modifications.
                    </p>
                </div>
            )}
        </div>
    );
}

// =============================================================================
// Revenue Share Preview
// =============================================================================

function RevenueSharePreview({ originalTool }: { originalTool: ToolManifest }) {
    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-medium text-gray-300">Revenue Sharing</span>
            </div>

            <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                    <span className="text-gray-400">Platform Fee</span>
                    <span className="text-gray-300">30%</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-400">Original Creator ({originalTool.created_by})</span>
                    <span className="text-gray-300">Based on Attribution</span>
                </div>
                <div className="flex justify-between">
                    <span className="text-gray-400">You (Forker)</span>
                    <span className="text-emerald-400">Based on Attribution</span>
                </div>
            </div>

            <div className="mt-4 p-3 bg-gray-900/50 rounded-lg">
                <p className="text-xs text-gray-400">
                    <Info className="w-3 h-3 inline mr-1" />
                    Attribution Score determines revenue split. Higher diff score, test pass rate,
                    usage, and quality ratings increase your share.
                </p>
            </div>
        </div>
    );
}

// =============================================================================
// Schema Editor
// =============================================================================

function SchemaEditor({
    label,
    original,
    value,
    onChange,
}: {
    label: string;
    original: Record<string, unknown>;
    value: string;
    onChange: (value: string) => void;
}) {
    const [error, setError] = useState<string | null>(null);

    const handleChange = (newValue: string) => {
        onChange(newValue);
        try {
            JSON.parse(newValue);
            setError(null);
        } catch (e) {
            setError((e as Error).message);
        }
    };

    return (
        <div className="grid grid-cols-2 gap-4">
            <div>
                <label className="block text-xs text-gray-500 mb-2">Original {label}</label>
                <pre className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs text-gray-400 overflow-x-auto h-40">
                    {JSON.stringify(original, null, 2)}
                </pre>
            </div>
            <div>
                <label className="block text-xs text-gray-500 mb-2">Your {label}</label>
                <textarea
                    value={value}
                    onChange={(e) => handleChange(e.target.value)}
                    className={`w-full h-40 bg-gray-900 border rounded-lg p-3 text-xs font-mono text-white resize-none
            ${error ? "border-red-500" : "border-gray-700 focus:border-purple-500"}`}
                />
                {error && <p className="text-xs text-red-400 mt-1">{error}</p>}
            </div>
        </div>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function ForkToolPage() {
    const params = useParams();
    const router = useRouter();
    const toolKey = params.toolKey as string;

    const [originalTool, setOriginalTool] = useState<ToolManifest | null>(null);
    const [loading, setLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showConfirm, setShowConfirm] = useState(false);

    // Form state
    const [displayName, setDisplayName] = useState("");
    const [description, setDescription] = useState("");
    const [forkReason, setForkReason] = useState("");
    const [inputSchema, setInputSchema] = useState("{}");
    const [outputSchema, setOutputSchema] = useState("{}");

    // Diff tracking
    const [diffStats, setDiffStats] = useState({
        added: 0,
        removed: 0,
        modified: 0,
        score: 0,
    });

    // Load original tool
    useEffect(() => {
        const fetchTool = async () => {
            try {
                const tool = await telemetryApi.getTool(toolKey);
                setOriginalTool(tool);
                setDisplayName(tool.display_name + " (Fork)");
                setDescription(tool.description);
                setInputSchema(JSON.stringify(tool.input_schema, null, 2));
                setOutputSchema(JSON.stringify(tool.output_schema, null, 2));
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load tool");
            } finally {
                setLoading(false);
            }
        };
        fetchTool();
    }, [toolKey]);

    // Calculate diff stats
    const calculateDiff = useCallback(() => {
        if (!originalTool) return;

        let added = 0;
        let removed = 0;
        let modified = 0;

        // Simple diff calculation based on description length difference
        const descDiff = Math.abs(description.length - originalTool.description.length);
        if (description !== originalTool.description) {
            modified += Math.min(descDiff, 10);
            if (description.length > originalTool.description.length) {
                added += Math.floor(descDiff / 10);
            } else {
                removed += Math.floor(descDiff / 10);
            }
        }

        // Schema diff
        try {
            const newInput = JSON.stringify(JSON.parse(inputSchema));
            const origInput = JSON.stringify(originalTool.input_schema);
            if (newInput !== origInput) {
                modified += 5;
            }
        } catch {
            // Ignore parse errors
        }

        try {
            const newOutput = JSON.stringify(JSON.parse(outputSchema));
            const origOutput = JSON.stringify(originalTool.output_schema);
            if (newOutput !== origOutput) {
                modified += 5;
            }
        } catch {
            // Ignore parse errors
        }

        // Calculate score using sigmoid
        const totalChanges = added + removed + modified;
        const score = totalChanges > 0 ? Math.min(100, 100 * (1 - Math.exp(-totalChanges / 50))) : 0;

        setDiffStats({ added, removed, modified, score });
    }, [originalTool, description, inputSchema, outputSchema]);

    useEffect(() => {
        calculateDiff();
    }, [calculateDiff]);

    const generateForkKey = () => {
        const timestamp = Date.now().toString(36);
        return `${toolKey}_fork_${timestamp}`;
    };

    const handleSubmit = async () => {
        if (!originalTool) return;

        setIsSubmitting(true);
        setError(null);

        try {
            // First create the new tool
            const newTool = await telemetryApi.createTool({
                tool_key: generateForkKey(),
                display_name: displayName,
                description,
                category: originalTool.category,
                credit_cost: originalTool.credit_cost,
                input_schema: JSON.parse(inputSchema),
                output_schema: JSON.parse(outputSchema),
                parent_tool_id: originalTool.id,
            });

            // Then create the fork event
            await telemetryApi.createFork({
                parent_tool_id: originalTool.id,
                child_tool_id: newTool.id,
                fork_reason: forkReason || undefined,
                diff_lines_added: diffStats.added,
                diff_lines_removed: diffStats.removed,
                diff_lines_modified: diffStats.modified,
            });

            router.push(`/tools/${newTool.tool_key}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create fork");
            setShowConfirm(false);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
            </div>
        );
    }

    if (error && !originalTool) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <h2 className="text-xl text-white mb-2">Failed to Load Tool</h2>
                    <p className="text-gray-400 mb-4">{error}</p>
                    <button
                        onClick={() => router.push("/tools")}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <button
                        onClick={() => router.push(`/tools/${toolKey}`)}
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-4 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to {originalTool?.display_name}
                    </button>

                    <div className="flex items-center gap-3">
                        <GitFork className="w-6 h-6 text-emerald-400" />
                        <h1 className="text-2xl font-bold">Fork Tool</h1>
                    </div>
                    <p className="text-gray-400 text-sm mt-1">
                        Create your own version of this tool
                    </p>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-6xl mx-auto px-6 py-8">
                {error && (
                    <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-red-300">{error}</p>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Form */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Original Reference */}
                        <div className="bg-gray-800/30 border border-gray-700/30 rounded-xl p-4">
                            <div className="flex items-center gap-2 mb-2 text-gray-400">
                                <span className="text-xs uppercase tracking-wide">Forking from</span>
                            </div>
                            <h3 className="text-lg font-semibold text-white">{originalTool?.display_name}</h3>
                            <p className="text-sm text-gray-400 font-mono">{originalTool?.tool_key}</p>
                        </div>

                        {/* Basic Info */}
                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-6">Fork Details</h2>

                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Display Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={displayName}
                                    onChange={(e) => setDisplayName(e.target.value)}
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                                />
                            </div>

                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Description <span className="text-red-400">*</span>
                                </label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={4}
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Fork Reason
                                    <span className="text-gray-500 text-xs ml-2">(optional, helps others understand your changes)</span>
                                </label>
                                <input
                                    type="text"
                                    value={forkReason}
                                    onChange={(e) => setForkReason(e.target.value)}
                                    placeholder="e.g., Added support for Korean language prompts"
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                                />
                            </div>
                        </div>

                        {/* Schemas */}
                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6">
                            <h2 className="text-lg font-semibold mb-6">Schemas</h2>

                            <div className="space-y-6">
                                <SchemaEditor
                                    label="Input Schema"
                                    original={originalTool?.input_schema || {}}
                                    value={inputSchema}
                                    onChange={setInputSchema}
                                />

                                <SchemaEditor
                                    label="Output Schema"
                                    original={originalTool?.output_schema || {}}
                                    value={outputSchema}
                                    onChange={setOutputSchema}
                                />
                            </div>
                        </div>

                        {/* Submit */}
                        <div className="flex items-center justify-end gap-4">
                            <button
                                onClick={() => router.push(`/tools/${toolKey}`)}
                                className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-medium rounded-lg"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => setShowConfirm(true)}
                                disabled={isSubmitting || !displayName || !description}
                                className="flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 
                         disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
                            >
                                <GitFork className="w-5 h-5" />
                                Create Fork
                            </button>
                        </div>
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        <DiffStats
                            added={diffStats.added}
                            removed={diffStats.removed}
                            modified={diffStats.modified}
                            diffScore={diffStats.score}
                        />

                        {originalTool && <RevenueSharePreview originalTool={originalTool} />}

                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4">
                            <div className="flex items-center gap-2 mb-3">
                                <Shield className="w-4 h-4 text-purple-400" />
                                <span className="text-sm font-medium text-gray-300">Attribution Info</span>
                            </div>
                            <p className="text-xs text-gray-400">
                                Your attribution score will be calculated based on:
                            </p>
                            <ul className="text-xs text-gray-500 mt-2 space-y-1">
                                <li>• Diff Score (20%): How much you changed</li>
                                <li>• Test Pass (15%): If automated tests pass</li>
                                <li>• Usage (25%): How often your fork is used</li>
                                <li>• Revenue (25%): Credits your fork earns</li>
                                <li>• Quality (15%): User ratings</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* Confirmation Modal */}
            {showConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-xl p-6 max-w-md w-full border border-gray-700">
                        <div className="flex items-center gap-3 mb-4">
                            <GitFork className="w-6 h-6 text-emerald-400" />
                            <h3 className="text-xl font-semibold">Confirm Fork</h3>
                        </div>

                        {diffStats.score < 5 && (
                            <div className="mb-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 flex items-start gap-2">
                                <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                                <p className="text-sm text-yellow-300">
                                    Your changes are minimal. This fork may be flagged for review.
                                </p>
                            </div>
                        )}

                        <p className="text-gray-400 mb-4">
                            You&apos;re about to fork <strong className="text-white">{originalTool?.display_name}</strong>.
                            Revenue will be shared based on your attribution score.
                        </p>

                        <div className="bg-gray-900/50 rounded-lg p-3 mb-6">
                            <div className="grid grid-cols-3 gap-2 text-center text-sm">
                                <div>
                                    <span className="text-green-400 font-bold">+{diffStats.added}</span>
                                    <span className="text-gray-500 block text-xs">added</span>
                                </div>
                                <div>
                                    <span className="text-red-400 font-bold">-{diffStats.removed}</span>
                                    <span className="text-gray-500 block text-xs">removed</span>
                                </div>
                                <div>
                                    <span className="text-blue-400 font-bold">~{diffStats.modified}</span>
                                    <span className="text-gray-500 block text-xs">modified</span>
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setShowConfirm(false)}
                                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={isSubmitting}
                                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 
                         text-white rounded-lg disabled:opacity-50"
                            >
                                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                <Check className="w-4 h-4" />
                                Confirm Fork
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
