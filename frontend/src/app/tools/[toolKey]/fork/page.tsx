"use client";

/**
 * Fork Creation Page - Refactored
 * 
 * Now uses extracted components for better maintainability.
 * Main page is ~280 lines (down from 682)
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft,
    GitFork,
    Code,
    AlertTriangle,
    Loader2,
    Save,
    Diff,
    FileCode,
} from "lucide-react";

// Local components
import {
    AttributionIndicator,
    ForkDiffViewer,
    NoLiveVersionWarning,
    ForkDetailsForm,
    ChangeStats,
    RevenueInfo,
    SybilWarning,
} from "./_components";

// Shared
import { fetchWithAuth } from "@/lib/api";
import type { Tool, DiffPreview } from "@/types/api.types";
import { useToast } from "@/components/Toast";

// =============================================================================
// API Functions
// =============================================================================

async function getToolWithCode(toolKey: string): Promise<Tool> {
    return fetchWithAuth(`/api/v1/mcp/tools/${toolKey}?include_code=true`);
}

async function previewDiff(toolId: string, code: string): Promise<DiffPreview> {
    return fetchWithAuth(`/api/v1/fork/tools/${toolId}/preview-diff`, {
        method: "POST",
        body: JSON.stringify({ code_content: code }),
    });
}

async function createFork(
    toolId: string,
    toolKey: string,
    displayName: string,
    code: string,
    changelog?: string
): Promise<{ tool_id: string; tool_key: string; sybil_flagged: boolean }> {
    return fetchWithAuth(`/api/v1/fork/tools/${toolId}/fork`, {
        method: "POST",
        body: JSON.stringify({
            new_tool_key: toolKey,
            new_display_name: displayName,
            code_content: code,
            changelog,
        }),
    });
}

// =============================================================================
// Main Component
// =============================================================================

export default function ForkEditorPage() {
    const params = useParams();
    const router = useRouter();
    const toolKey = params.toolKey as string;
    const toast = useToast();

    // Loading states
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [diffLoading, setDiffLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Tool data
    const [tool, setTool] = useState<Tool | null>(null);
    const [originalCode, setOriginalCode] = useState("");

    // Fork data
    const [forkCode, setForkCode] = useState("");
    const [forkKey, setForkKey] = useState("");
    const [forkName, setForkName] = useState("");
    const [changelog, setChangelog] = useState("");

    // Diff
    const [diffPreview, setDiffPreview] = useState<DiffPreview | null>(null);
    const [activeTab, setActiveTab] = useState<"editor" | "diff">("editor");

    // Load tool
    useEffect(() => {
        const loadTool = async () => {
            setLoading(true);
            setError(null);
            try {
                const toolData = await getToolWithCode(toolKey);
                setTool(toolData);
                if (toolData.live_version?.code_content) {
                    setOriginalCode(toolData.live_version.code_content);
                    setForkCode(toolData.live_version.code_content);
                }
                const baseKey = toolKey.replace(/_fork.*$/, "");
                setForkKey(`${baseKey}_fork_${Date.now().toString(36)}`);
                setForkName(`Fork of ${toolData.display_name}`);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load tool");
            } finally {
                setLoading(false);
            }
        };
        loadTool();
    }, [toolKey]);

    // Debounced diff preview
    useEffect(() => {
        if (!tool || forkCode === originalCode || !originalCode) {
            setDiffPreview(null);
            return;
        }
        const timer = setTimeout(async () => {
            setDiffLoading(true);
            try {
                const preview = await previewDiff(tool.id, forkCode);
                setDiffPreview(preview);
            } catch (err) {
                console.error("Diff preview failed:", err);
                toast.warning("Diff 미리보기에 실패했습니다");
            } finally {
                setDiffLoading(false);
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [tool, forkCode, originalCode, toast]);

    // Placeholder code
    const usePlaceholder = useCallback(() => {
        if (!tool) return;
        const placeholder = `# ${tool.display_name}\n# Tool Key: ${tool.tool_key}\n\ndef process(input_data):\n    return {"result": "processed"}`;
        setOriginalCode(placeholder);
        setForkCode(placeholder);
    }, [tool]);

    // Submit fork
    const handleSubmit = async () => {
        if (!tool || !forkKey || forkCode === originalCode) return;
        if (!/^[a-z][a-z0-9_]*$/.test(forkKey)) {
            setError("Tool key must start with letter and contain only lowercase letters, numbers, and underscores");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            const result = await createFork(tool.id, forkKey, forkName, forkCode, changelog || undefined);
            const message = result.sybil_flagged
                ? "Fork created but flagged for low originality."
                : "Fork created successfully! Pending review.";
            alert(message);
            router.push(`/tools/${result.tool_key}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Fork creation failed");
        } finally {
            setSubmitting(false);
        }
    };

    const canSubmit = tool && forkKey && forkName && forkCode !== originalCode && !submitting;

    // Loading state
    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" />
                    <p className="text-gray-400">Loading tool...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error && !tool) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-300 mb-4">{error}</p>
                    <button onClick={() => router.back()} className="text-purple-400 hover:underline">
                        Go Back
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <button onClick={() => router.back()} className="flex items-center gap-2 text-gray-400 hover:text-white mb-3 text-sm">
                        <ArrowLeft className="w-4 h-4" />
                        Back to {toolKey}
                    </button>
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-xl font-bold flex items-center gap-2">
                                <GitFork className="w-5 h-5 text-purple-400" />
                                Create Fork
                            </h1>
                            <p className="text-gray-400 text-sm">{tool?.display_name || toolKey}</p>
                        </div>
                        <button
                            onClick={handleSubmit}
                            disabled={!canSubmit}
                            className="flex items-center gap-2 px-5 py-2.5 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            {submitting ? "Creating..." : "Create Fork"}
                        </button>
                    </div>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="max-w-7xl mx-auto px-6 pt-4">
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-red-300">{error}</p>
                        <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">×</button>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-6 py-6">
                {tool && !tool.live_version && !originalCode && (
                    <div className="mb-6">
                        <NoLiveVersionWarning tool={tool} onCreatePlaceholder={usePlaceholder} />
                    </div>
                )}

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left: Editor */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* Tabs */}
                        <div className="flex gap-1 p-1 bg-gray-800/50 rounded-lg w-fit">
                            {([
                                { id: "editor", label: "Code Editor", icon: Code },
                                { id: "diff", label: "View Changes", icon: Diff },
                            ] as const).map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id
                                        ? "bg-purple-500 text-white"
                                        : "text-gray-400 hover:text-white hover:bg-gray-700"
                                        }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    {tab.label}
                                    {tab.id === "diff" && diffLoading && <Loader2 className="w-3 h-3 animate-spin" />}
                                </button>
                            ))}
                        </div>

                        {/* Editor Tab */}
                        {activeTab === "editor" && (
                            <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                                <div className="bg-gray-800 px-4 py-3 flex items-center justify-between border-b border-gray-700">
                                    <div className="flex items-center gap-2">
                                        <FileCode className="w-4 h-4 text-gray-400" />
                                        <span className="text-sm text-gray-300">{tool?.live_version?.code_type || "code"}</span>
                                    </div>
                                    <span className="text-xs text-gray-500">
                                        {forkCode.length} chars
                                        {forkCode !== originalCode && <span className="ml-2 text-yellow-400">• Modified</span>}
                                    </span>
                                </div>
                                <textarea
                                    value={forkCode}
                                    onChange={(e) => setForkCode(e.target.value)}
                                    className="w-full h-[500px] p-4 bg-gray-900 text-gray-100 font-mono text-sm resize-none focus:outline-none"
                                    placeholder="Edit the code..."
                                    spellCheck={false}
                                    disabled={!originalCode}
                                />
                            </div>
                        )}

                        {/* Diff Tab */}
                        {activeTab === "diff" && (
                            <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                                <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
                                    <span className="text-sm text-gray-300">Changes from original</span>
                                </div>
                                {diffPreview ? (
                                    <ForkDiffViewer diffContent={diffPreview.diff_content} />
                                ) : forkCode === originalCode ? (
                                    <div className="p-12 text-center text-gray-500">
                                        <Diff className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                        <p>No changes yet</p>
                                    </div>
                                ) : (
                                    <div className="p-12 text-center">
                                        <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto" />
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Right: Settings & Stats */}
                    <div className="space-y-4">
                        <ForkDetailsForm
                            forkKey={forkKey}
                            forkName={forkName}
                            changelog={changelog}
                            onForkKeyChange={setForkKey}
                            onForkNameChange={setForkName}
                            onChangelogChange={setChangelog}
                        />

                        {diffPreview && (
                            <AttributionIndicator
                                score={diffPreview.stats.diff_score}
                                isTrivial={diffPreview.stats.is_trivial}
                            />
                        )}

                        {diffPreview?.sybil_warning && <SybilWarning warning={diffPreview.sybil_warning} />}
                        {diffPreview && <ChangeStats stats={diffPreview.stats} />}
                        <RevenueInfo />
                    </div>
                </div>
            </div>
        </div>
    );
}
