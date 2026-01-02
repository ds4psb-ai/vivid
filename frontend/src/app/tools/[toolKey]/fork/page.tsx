"use client";

/**
 * Fork Creation Page with Code Editor
 * 
 * Full fork workflow:
 * 1. View original tool code
 * 2. Edit in Monaco-like code area
 * 3. See live diff preview
 * 4. Attribution score & Sybil warning
 * 5. Submit fork
 */

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    ArrowLeft,
    GitFork,
    Code,
    Eye,
    AlertTriangle,
    CheckCircle,
    Loader2,
    Save,
    Play,
    FileCode,
    Diff,
    TrendingUp,
    Shield,
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

interface ToolVersion {
    id: string;
    code_content: string;
    code_type: string;
    system_prompt: string | null;
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

async function getToolVersions(toolId: string): Promise<ToolVersion[]> {
    return fetchWithAuth(`${API_BASE_URL}/api/v1/fork/tools/${toolId}/versions`);
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
): Promise<{ tool_id: string; tool_key: string }> {
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
// Attribution Score Indicator
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
                <span className="text-sm text-gray-400">Attribution Score</span>
                {isTrivial && (
                    <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">Sybil Warning</span>
                )}
            </div>
            <div className="flex items-center gap-4">
                <div className={`text-3xl font-bold ${getScoreColor()}`}>{score}</div>
                <div className="flex-1">
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all ${isTrivial ? "bg-red-500" : "bg-gradient-to-r from-purple-500 to-blue-500"}`}
                            style={{ width: `${score}%` }}
                        />
                    </div>
                </div>
                <div className="text-right">
                    <div className={`text-lg font-bold ${getScoreColor()}`}>{getShareRate()}</div>
                    <div className="text-xs text-gray-500">Your share</div>
                </div>
            </div>
        </div>
    );
}

// =============================================================================
// Diff Viewer
// =============================================================================

function DiffViewer({ diffContent }: { diffContent: string }) {
    const lines = diffContent.split("\n");

    return (
        <div className="bg-gray-900 rounded-lg overflow-hidden font-mono text-sm">
            <div className="max-h-64 overflow-y-auto p-4">
                {lines.map((line, i) => {
                    let className = "text-gray-400";
                    if (line.startsWith("+") && !line.startsWith("+++")) {
                        className = "text-green-400 bg-green-500/10";
                    } else if (line.startsWith("-") && !line.startsWith("---")) {
                        className = "text-red-400 bg-red-500/10";
                    } else if (line.startsWith("@@")) {
                        className = "text-blue-400";
                    }
                    return (
                        <div key={i} className={`${className} px-2`}>
                            {line || " "}
                        </div>
                    );
                })}
                {lines.length === 0 && (
                    <div className="text-gray-500 text-center py-4">No changes yet</div>
                )}
            </div>
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

    // State
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Original tool
    const [toolId, setToolId] = useState<string | null>(null);
    const [originalCode, setOriginalCode] = useState("");
    const [codeType, setCodeType] = useState("prompt_template");

    // Fork data
    const [forkCode, setForkCode] = useState("");
    const [forkKey, setForkKey] = useState("");
    const [forkName, setForkName] = useState("");
    const [changelog, setChangelog] = useState("");

    // Diff
    const [diffPreview, setDiffPreview] = useState<DiffPreview | null>(null);
    const [diffLoading, setDiffLoading] = useState(false);

    // Tabs
    const [activeTab, setActiveTab] = useState<"editor" | "diff" | "preview">("editor");

    // Load original tool
    useEffect(() => {
        const loadTool = async () => {
            try {
                // Get tool by key first
                const toolRes = await fetchWithAuth(`${API_BASE_URL}/api/v1/mcp/tools/${toolKey}`);
                setToolId(toolRes.id);

                // Get versions
                const versions = await getToolVersions(toolRes.id);
                const liveVersion = versions.find((v) => v.code_content);

                if (liveVersion) {
                    setOriginalCode(liveVersion.code_content);
                    setForkCode(liveVersion.code_content);
                    setCodeType(liveVersion.code_type);
                }

                setForkKey(toolKey + "_fork");
                setForkName(`Fork of ${toolRes.display_name || toolKey}`);
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load tool");
            } finally {
                setLoading(false);
            }
        };

        loadTool();
    }, [toolKey]);

    // Preview diff when code changes
    useEffect(() => {
        if (!toolId || forkCode === originalCode) {
            setDiffPreview(null);
            return;
        }

        const timer = setTimeout(async () => {
            setDiffLoading(true);
            try {
                const preview = await previewDiff(toolId, forkCode);
                setDiffPreview(preview);
            } catch (err) {
                console.error("Diff preview failed", err);
            } finally {
                setDiffLoading(false);
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [toolId, forkCode, originalCode]);

    // Submit fork
    const handleSubmit = async () => {
        if (!toolId) return;

        setSubmitting(true);
        setError(null);

        try {
            const result = await createFork(toolId, forkKey, forkName, forkCode, changelog);
            router.push(`/tools/${result.tool_key}?forked=true`);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Fork creation failed");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
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
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-3"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back
                    </button>

                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-xl font-bold flex items-center gap-2">
                                <GitFork className="w-5 h-5 text-purple-400" />
                                Fork: {toolKey}
                            </h1>
                            <p className="text-gray-400 text-sm">Edit code and create your version</p>
                        </div>

                        <button
                            onClick={handleSubmit}
                            disabled={submitting || !forkKey || forkCode === originalCode}
                            className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white font-medium rounded-lg disabled:opacity-50"
                        >
                            {submitting ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Save className="w-4 h-4" />
                            )}
                            Create Fork
                        </button>
                    </div>
                </div>
            </div>

            {/* Error */}
            {error && (
                <div className="max-w-7xl mx-auto px-6 pt-4">
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        <p className="text-red-300">{error}</p>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-6 py-6 grid lg:grid-cols-3 gap-6">
                {/* Left: Editor */}
                <div className="lg:col-span-2 space-y-4">
                    {/* Tabs */}
                    <div className="flex gap-2 border-b border-gray-700 pb-2">
                        {[
                            { id: "editor", label: "Code Editor", icon: Code },
                            { id: "diff", label: "Diff View", icon: Diff },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === tab.id
                                        ? "bg-purple-500/20 text-purple-400"
                                        : "text-gray-400 hover:text-white"
                                    }`}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Editor */}
                    {activeTab === "editor" && (
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                            <div className="bg-gray-800 px-4 py-2 flex items-center justify-between border-b border-gray-700">
                                <span className="text-sm text-gray-400">{codeType}</span>
                                <span className="text-xs text-gray-500">
                                    {forkCode.length} characters
                                </span>
                            </div>
                            <textarea
                                value={forkCode}
                                onChange={(e) => setForkCode(e.target.value)}
                                className="w-full h-96 p-4 bg-gray-900 text-gray-100 font-mono text-sm resize-none focus:outline-none"
                                placeholder="Enter your modified code here..."
                                spellCheck={false}
                            />
                        </div>
                    )}

                    {/* Diff View */}
                    {activeTab === "diff" && (
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                            <div className="bg-gray-800 px-4 py-2 flex items-center justify-between border-b border-gray-700">
                                <span className="text-sm text-gray-400">Changes from original</span>
                                {diffLoading && <Loader2 className="w-4 h-4 animate-spin text-purple-400" />}
                            </div>
                            {diffPreview ? (
                                <DiffViewer diffContent={diffPreview.diff_content} />
                            ) : (
                                <div className="p-8 text-center text-gray-500">
                                    No changes detected
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Right: Fork Settings */}
                <div className="space-y-4">
                    {/* Fork Info */}
                    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                        <h3 className="font-semibold mb-4">Fork Details</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Tool Key</label>
                                <input
                                    type="text"
                                    value={forkKey}
                                    onChange={(e) => setForkKey(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
                                    className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                                    placeholder="my_fork_name"
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Display Name</label>
                                <input
                                    type="text"
                                    value={forkName}
                                    onChange={(e) => setForkName(e.target.value)}
                                    className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
                                />
                            </div>

                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Changelog</label>
                                <textarea
                                    value={changelog}
                                    onChange={(e) => setChangelog(e.target.value)}
                                    rows={3}
                                    className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white resize-none"
                                    placeholder="What did you change?"
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
                                    <h4 className="font-medium text-orange-400 mb-1">Sybil Detection</h4>
                                    <p className="text-sm text-gray-300">{diffPreview.sybil_warning}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Stats */}
                    {diffPreview && (
                        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
                            <h4 className="font-semibold mb-3">Change Statistics</h4>
                            <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Lines Added</span>
                                    <span className="text-green-400">+{diffPreview.stats.lines_added}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Lines Removed</span>
                                    <span className="text-red-400">-{diffPreview.stats.lines_removed}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400">Lines Modified</span>
                                    <span className="text-yellow-400">~{diffPreview.stats.lines_modified}</span>
                                </div>
                                <div className="flex justify-between pt-2 border-t border-gray-700">
                                    <span className="text-gray-400">Similarity</span>
                                    <span className="text-purple-400">
                                        {(diffPreview.stats.similarity_ratio * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
