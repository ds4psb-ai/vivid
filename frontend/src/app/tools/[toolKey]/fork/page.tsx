"use client";

/**
 * Fork Creation Page - Production Ready
 * 
 * Complete fork workflow with proper API integration:
 * 1. Load tool with code from /mcp/tools/{key}?include_code=true
 * 2. Edit code with live diff preview
 * 3. Attribution score & Sybil detection
 * 4. Submit fork → pending review
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft,
    GitFork,
    Code,
    AlertTriangle,
    CheckCircle,
    Loader2,
    Save,
    Diff,
    TrendingUp,
    Shield,
    FileCode,
    Info,
    Zap,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types
// =============================================================================

interface DiffStats {
    lines_added: number;
    lines_removed: number;
    lines_modified: number;
    similarity_ratio: number;
    diff_score: number;
    is_trivial: boolean;
}

interface DiffPreview {
    diff_content: string;
    stats: DiffStats;
    semantic_changes: Record<string, any>;
    sybil_warning: string | null;
}

interface LiveVersion {
    id: string;
    version: string;
    code_type: string;
    code_content: string;
    system_prompt: string | null;
    status: string;
}

interface Tool {
    id: string;
    tool_key: string;
    display_name: string;
    description: string;
    category: string;
    tier: string;
    input_schema: any;
    output_schema: any;
    live_version: LiveVersion | null;
}

// =============================================================================
// API Functions
// =============================================================================

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem("token");
    const res = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `Error: ${res.status}`);
    }
    return res.json();
}

async function getToolWithCode(toolKey: string): Promise<Tool> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/mcp/tools/${toolKey}?include_code=true`);
}

async function previewDiff(toolId: string, code: string): Promise<DiffPreview> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/fork/tools/${toolId}/preview-diff`, {
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
    return fetchWithAuth(`${API_BASE_URL}/api/v1/fork/tools/${toolId}/fork`, {
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
// Components
// =============================================================================

function AttributionIndicator({ score, isTrivial }: { score: number; isTrivial: boolean }) {
    const getScoreColor = () => {
        if (score >= 75) return "text-green-400";
        if (score >= 50) return "text-blue-400";
        if (score >= 25) return "text-yellow-400";
        return "text-red-400";
    };

    const getShareRate = () => {
        if (score >= 75) return "75%";
        if (score >= 50) return "50%";
        if (score >= 25) return "25%";
        return "10%";
    };

    return (
        <div className={`p-4 rounded-lg border ${isTrivial ? "bg-red-500/10 border-red-500/30" : "bg-gray-800/50 border-gray-700"}`}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-purple-400" />
                    <span className="text-sm text-gray-400">Attribution Score</span>
                </div>
                {isTrivial && (
                    <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">⚠️ Sybil</span>
                )}
            </div>
            <div className="flex items-center gap-4">
                <div className={`text-3xl font-bold ${getScoreColor()}`}>{score}</div>
                <div className="flex-1">
                    <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-300 ${isTrivial ? "bg-red-500" : "bg-gradient-to-r from-purple-500 to-blue-500"}`}
                            style={{ width: `${Math.min(100, score)}%` }}
                        />
                    </div>
                </div>
                <div className="text-right">
                    <div className={`text-xl font-bold ${getScoreColor()}`}>{getShareRate()}</div>
                    <div className="text-xs text-gray-500">Revenue Share</div>
                </div>
            </div>
        </div>
    );
}

function DiffViewer({ diffContent }: { diffContent: string }) {
    const lines = diffContent.split("\n");

    return (
        <div className="bg-gray-900 rounded-lg overflow-hidden font-mono text-sm max-h-80 overflow-y-auto">
            <div className="p-4">
                {lines.map((line, i) => {
                    let className = "text-gray-400";
                    let bg = "";
                    if (line.startsWith("+") && !line.startsWith("+++")) {
                        className = "text-green-400";
                        bg = "bg-green-500/10";
                    } else if (line.startsWith("-") && !line.startsWith("---")) {
                        className = "text-red-400";
                        bg = "bg-red-500/10";
                    } else if (line.startsWith("@@")) {
                        className = "text-blue-400";
                    }
                    return (
                        <div key={i} className={`${className} ${bg} px-2 py-0.5 whitespace-pre`}>
                            {line || " "}
                        </div>
                    );
                })}
                {lines.length === 0 && (
                    <div className="text-gray-500 text-center py-8">
                        No changes yet. Edit the code to see diff.
                    </div>
                )}
            </div>
        </div>
    );
}

function NoLiveVersionWarning({
    tool,
    onCreatePlaceholder,
}: {
    tool: Tool;
    onCreatePlaceholder: () => void;
}) {
    return (
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-6 text-center">
            <AlertTriangle className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-yellow-400 mb-2">
                No Code Version Available
            </h3>
            <p className="text-gray-300 mb-4">
                This tool doesn&apos;t have a live code version yet. The administrator needs to run the seed script.
            </p>
            <div className="bg-gray-900 rounded-lg p-4 text-left font-mono text-sm text-gray-400 mb-4">
                <code>python -m backend.scripts.seed_tool_versions</code>
            </div>
            <button
                onClick={onCreatePlaceholder}
                className="px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-lg"
            >
                Use placeholder code instead
            </button>
        </div>
    );
}

// =============================================================================
// Main Component
// =============================================================================

export default function ForkEditorPage() {
    const params = useParams();
    const router = useRouter();
    const toolKey = params.toolKey as string;

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

                // Generate fork key
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
                // Don't show error - not critical
            } finally {
                setDiffLoading(false);
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [tool, forkCode, originalCode]);

    // Placeholder code for tools without versions
    const usePlaceholder = useCallback(() => {
        if (!tool) return;

        const placeholder = `# ${tool.display_name}
# Tool Key: ${tool.tool_key}

## Description
${tool.description || "No description"}

## Input Schema
${JSON.stringify(tool.input_schema, null, 2)}

## Your Code Here
# Modify this template to create your fork
# Add your custom logic, prompts, or configurations

def process(input_data):
    # Your implementation here
    return {"result": "processed"}
`;
        setOriginalCode(placeholder);
        setForkCode(placeholder);
    }, [tool]);

    // Submit fork
    const handleSubmit = async () => {
        if (!tool || !forkKey || forkCode === originalCode) return;

        // Validate key format
        if (!/^[a-z][a-z0-9_]*$/.test(forkKey)) {
            setError("Tool key must start with letter and contain only lowercase letters, numbers, and underscores");
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const result = await createFork(
                tool.id,
                forkKey,
                forkName,
                forkCode,
                changelog || undefined
            );

            // Show success message and redirect
            const message = result.sybil_flagged
                ? "Fork created but flagged for low originality. Consider making more significant changes."
                : "Fork created successfully! Pending review.";

            alert(message);
            router.push(`/tools/${result.tool_key}`);

        } catch (err) {
            setError(err instanceof Error ? err.message : "Fork creation failed");
        } finally {
            setSubmitting(false);
        }
    };

    // Check if can submit
    const canSubmit = tool && forkKey && forkName && forkCode !== originalCode && !submitting;

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

    if (error && !tool) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                    <p className="text-red-300 mb-4">{error}</p>
                    <button
                        onClick={() => router.back()}
                        className="text-purple-400 hover:underline"
                    >
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
                    <button
                        onClick={() => router.back()}
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-3 text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to {toolKey}
                    </button>

                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-xl font-bold flex items-center gap-2">
                                <GitFork className="w-5 h-5 text-purple-400" />
                                Create Fork
                            </h1>
                            <p className="text-gray-400 text-sm">
                                {tool?.display_name || toolKey}
                            </p>
                        </div>

                        <button
                            onClick={handleSubmit}
                            disabled={!canSubmit}
                            className="flex items-center gap-2 px-5 py-2.5 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {submitting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    Create Fork
                                </>
                            )}
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
                        <button
                            onClick={() => setError(null)}
                            className="ml-auto text-red-400 hover:text-red-300"
                        >
                            ×
                        </button>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-6 py-6">
                {/* No Live Version Warning */}
                {tool && !tool.live_version && !originalCode && (
                    <div className="mb-6">
                        <NoLiveVersionWarning tool={tool} onCreatePlaceholder={usePlaceholder} />
                    </div>
                )}

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Left: Editor Area */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* Tabs */}
                        <div className="flex gap-1 p-1 bg-gray-800/50 rounded-lg w-fit">
                            {[
                                { id: "editor", label: "Code Editor", icon: Code },
                                { id: "diff", label: "View Changes", icon: Diff },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id
                                            ? "bg-purple-500 text-white"
                                            : "text-gray-400 hover:text-white hover:bg-gray-700"
                                        }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    {tab.label}
                                    {tab.id === "diff" && diffLoading && (
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* Editor Tab */}
                        {activeTab === "editor" && (
                            <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                                <div className="bg-gray-800 px-4 py-3 flex items-center justify-between border-b border-gray-700">
                                    <div className="flex items-center gap-2">
                                        <FileCode className="w-4 h-4 text-gray-400" />
                                        <span className="text-sm text-gray-300">
                                            {tool?.live_version?.code_type || "code"}
                                        </span>
                                    </div>
                                    <span className="text-xs text-gray-500">
                                        {forkCode.length} characters
                                        {forkCode !== originalCode && (
                                            <span className="ml-2 text-yellow-400">• Modified</span>
                                        )}
                                    </span>
                                </div>
                                <textarea
                                    value={forkCode}
                                    onChange={(e) => setForkCode(e.target.value)}
                                    className="w-full h-[500px] p-4 bg-gray-900 text-gray-100 font-mono text-sm resize-none focus:outline-none"
                                    placeholder={originalCode ? "Edit the code..." : "No code available. Click 'Use placeholder code' above."}
                                    spellCheck={false}
                                    disabled={!originalCode}
                                />
                            </div>
                        )}

                        {/* Diff Tab */}
                        {activeTab === "diff" && (
                            <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                                <div className="bg-gray-800 px-4 py-3 border-b border-gray-700">
                                    <span className="text-sm text-gray-300">
                                        Changes from original
                                    </span>
                                </div>
                                {diffPreview ? (
                                    <DiffViewer diffContent={diffPreview.diff_content} />
                                ) : forkCode === originalCode ? (
                                    <div className="p-12 text-center text-gray-500">
                                        <Diff className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                        <p>No changes yet</p>
                                        <p className="text-sm mt-1">Edit the code to see the diff</p>
                                    </div>
                                ) : (
                                    <div className="p-12 text-center">
                                        <Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto" />
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Right: Fork Settings & Stats */}
                    <div className="space-y-4">
                        {/* Fork Details */}
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
                            <h3 className="font-semibold mb-4 flex items-center gap-2">
                                <Zap className="w-4 h-4 text-purple-400" />
                                Fork Details
                            </h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1.5">
                                        Tool Key <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={forkKey}
                                        onChange={(e) => setForkKey(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                                        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:border-purple-500"
                                        placeholder="my_fork_name"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">Lowercase, numbers, underscores only</p>
                                </div>

                                <div>
                                    <label className="block text-sm text-gray-400 mb-1.5">
                                        Display Name <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={forkName}
                                        onChange={(e) => setForkName(e.target.value)}
                                        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm text-gray-400 mb-1.5">Changelog</label>
                                    <textarea
                                        value={changelog}
                                        onChange={(e) => setChangelog(e.target.value)}
                                        rows={3}
                                        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white resize-none focus:outline-none focus:border-purple-500"
                                        placeholder="What did you change? (optional)"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Attribution Score */}
                        {diffPreview && (
                            <AttributionIndicator
                                score={diffPreview.stats.diff_score}
                                isTrivial={diffPreview.stats.is_trivial}
                            />
                        )}

                        {/* Sybil Warning */}
                        {diffPreview?.sybil_warning && (
                            <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
                                <div className="flex items-start gap-3">
                                    <Shield className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <h4 className="font-medium text-orange-400 mb-1">Low Originality</h4>
                                        <p className="text-sm text-gray-300">{diffPreview.sybil_warning}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Change Stats */}
                        {diffPreview && (
                            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-5">
                                <h4 className="font-semibold mb-3 flex items-center gap-2">
                                    <Info className="w-4 h-4 text-gray-400" />
                                    Change Statistics
                                </h4>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Lines Added</span>
                                        <span className="text-green-400 font-mono">+{diffPreview.stats.lines_added}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Lines Removed</span>
                                        <span className="text-red-400 font-mono">-{diffPreview.stats.lines_removed}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-400">Lines Modified</span>
                                        <span className="text-yellow-400 font-mono">~{diffPreview.stats.lines_modified}</span>
                                    </div>
                                    <div className="flex justify-between pt-2 border-t border-gray-700 mt-2">
                                        <span className="text-gray-400">Similarity</span>
                                        <span className="text-purple-400 font-mono">
                                            {(diffPreview.stats.similarity_ratio * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Revenue Info */}
                        <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/30 rounded-xl p-5">
                            <h4 className="font-semibold mb-3 flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-purple-400" />
                                Revenue Sharing
                            </h4>
                            <p className="text-sm text-gray-300 mb-3">
                                When users run your fork, you earn based on your attribution score:
                            </p>
                            <ul className="text-sm text-gray-400 space-y-1">
                                <li>• <span className="text-green-400">75+</span>: You get 75% of creator pool</li>
                                <li>• <span className="text-blue-400">50-74</span>: You get 50%</li>
                                <li>• <span className="text-yellow-400">25-49</span>: You get 25%</li>
                                <li>• <span className="text-red-400">&lt;25</span>: Only 10% (Sybil flag)</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
