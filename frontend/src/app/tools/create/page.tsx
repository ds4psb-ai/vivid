"use client";

/**
 * Create Tool Page
 * 
 * UX Hardening Features:
 * - Real-time validation with error messages
 * - Tool key auto-generation from display name
 * - Category selector with descriptions
 * - Credit cost slider with preview
 * - Schema editor with JSON validation
 * - Preview card showing how tool will appear
 * - Confirmation before creation
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    ArrowLeft,
    Zap,
    Check,
    AlertCircle,
    Info,
    Loader2,
    Eye,
    Code,
    DollarSign,
    Github,
    Download,
} from "lucide-react";
import * as telemetryApi from "@/lib/telemetry-api";

// =============================================================================
// Types
// =============================================================================

interface FormData {
    display_name: string;
    tool_key: string;
    description: string;
    category: string;
    credit_cost: number;
    input_schema: string;
    output_schema: string;
    system_prompt: string;
}

interface FormErrors {
    display_name?: string;
    tool_key?: string;
    description?: string;
    category?: string;
    input_schema?: string;
    output_schema?: string;
    system_prompt?: string;
}

// =============================================================================
// Categories
// =============================================================================

const CATEGORIES = [
    { key: "film", label: "Film & Video", description: "Tools for video production and analysis" },
    { key: "design", label: "Design", description: "Visual design and graphics tools" },
    { key: "audio", label: "Audio", description: "Music and sound production tools" },
    { key: "writing", label: "Writing", description: "Content and copywriting tools" },
    { key: "tarot", label: "Tarot & Mystical", description: "Divination and interpretation tools" },
    { key: "data", label: "Data & Analytics", description: "Data processing and analysis tools" },
    { key: "other", label: "Other", description: "Miscellaneous tools" },
];

// =============================================================================
// Helper Functions
// =============================================================================

function generateToolKey(displayName: string): string {
    return displayName
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")
        .replace(/\s+/g, "_")
        .replace(/-+/g, "_")
        .replace(/_+/g, "_")
        .slice(0, 60);
}

function validateJSON(str: string): { valid: boolean; error?: string } {
    if (!str.trim()) return { valid: true };
    try {
        JSON.parse(str);
        return { valid: true };
    } catch (e) {
        return { valid: false, error: (e as Error).message };
    }
}

// =============================================================================
// Form Field Components
// =============================================================================

function FormField({
    label,
    error,
    hint,
    required,
    children,
}: {
    label: string;
    error?: string;
    hint?: string;
    required?: boolean;
    children: React.ReactNode;
}) {
    return (
        <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
                {label}
                {required && <span className="text-red-400 ml-1">*</span>}
            </label>
            {children}
            {hint && !error && <p className="mt-1.5 text-xs text-gray-500">{hint}</p>}
            {error && (
                <p className="mt-1.5 text-xs text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    {error}
                </p>
            )}
        </div>
    );
}

// =============================================================================
// Credit Cost Slider
// =============================================================================

function CreditCostSlider({
    value,
    onChange,
}: {
    value: number;
    onChange: (value: number) => void;
}) {
    const presets = [1, 5, 10, 25, 50, 100];

    return (
        <div>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    <span className="text-2xl font-bold text-white">{value}</span>
                    <span className="text-gray-400">credits per run</span>
                </div>
            </div>

            <input
                type="range"
                min="0"
                max="100"
                value={value}
                onChange={(e) => onChange(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />

            <div className="flex justify-between mt-2">
                {presets.map((preset) => (
                    <button
                        key={preset}
                        type="button"
                        onClick={() => onChange(preset)}
                        className={`px-2 py-1 text-xs rounded ${value === preset
                            ? "bg-purple-600 text-white"
                            : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                            }`}
                    >
                        {preset}
                    </button>
                ))}
            </div>
        </div>
    );
}

// =============================================================================
// Category Selector
// =============================================================================

function CategorySelector({
    value,
    onChange,
}: {
    value: string;
    onChange: (value: string) => void;
}) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {CATEGORIES.map((cat) => (
                <button
                    key={cat.key}
                    type="button"
                    onClick={() => onChange(cat.key)}
                    className={`p-4 rounded-lg border text-left transition-all ${value === cat.key
                        ? "border-purple-500 bg-purple-500/10"
                        : "border-gray-700 bg-gray-800/50 hover:border-gray-600"
                        }`}
                >
                    <div className="font-medium text-white mb-1">{cat.label}</div>
                    <div className="text-xs text-gray-400 line-clamp-2">{cat.description}</div>
                </button>
            ))}
        </div>
    );
}

// =============================================================================
// Preview Card
// =============================================================================

function PreviewCard({ data }: { data: FormData }) {
    return (
        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 sticky top-24">
            <div className="flex items-center gap-2 mb-4 text-gray-400">
                <Eye className="w-4 h-4" />
                <span className="text-sm font-medium">Preview</span>
            </div>

            <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/30">
                <div className="flex items-start justify-between mb-3">
                    <div>
                        <h3 className="text-lg font-semibold text-white">
                            {data.display_name || "Tool Name"}
                        </h3>
                        <p className="text-sm text-gray-400 font-mono">
                            {data.tool_key || "tool_key"}
                        </p>
                    </div>
                    <span className="px-2.5 py-1 text-xs font-medium rounded-full bg-yellow-500/10 text-yellow-400 border border-yellow-500/30">
                        Experimental
                    </span>
                </div>

                <p className="text-sm text-gray-400 line-clamp-2 mb-4">
                    {data.description || "Tool description will appear here..."}
                </p>

                <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-lg font-bold text-white">0</div>
                        <div className="text-xs text-gray-500">Uses</div>
                    </div>
                    <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-lg font-bold text-white">0</div>
                        <div className="text-xs text-gray-500">Forks</div>
                    </div>
                    <div className="text-center p-2 bg-gray-800/50 rounded-lg">
                        <div className="text-lg font-bold text-emerald-400">{data.credit_cost}</div>
                        <div className="text-xs text-gray-500">Credits</div>
                    </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Category: {data.category || "—"}</span>
                    <span className="text-gray-400">New tool</span>
                </div>
            </div>

            <p className="text-xs text-gray-500 mt-4 text-center">
                This is how your tool will appear in the dashboard
            </p>
        </div>
    );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function CreateToolPage() {
    const router = useRouter();
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [showConfirm, setShowConfirm] = useState(false);

    const [formData, setFormData] = useState<FormData>({
        display_name: "",
        tool_key: "",
        description: "",
        category: "",
        credit_cost: 5,
        input_schema: "{}",
        output_schema: "{}",
        system_prompt: "",
    });

    const [errors, setErrors] = useState<FormErrors>({});
    const [touched, setTouched] = useState<Set<string>>(new Set());

    // Auto-generate tool_key from display_name
    useEffect(() => {
        if (formData.display_name && !touched.has("tool_key")) {
            setFormData((prev) => ({
                ...prev,
                tool_key: generateToolKey(prev.display_name),
            }));
        }
    }, [formData.display_name, touched]);

    // Validation
    const validate = useCallback((): boolean => {
        const newErrors: FormErrors = {};

        if (!formData.display_name.trim()) {
            newErrors.display_name = "Display name is required";
        } else if (formData.display_name.length < 3) {
            newErrors.display_name = "Display name must be at least 3 characters";
        }

        if (!formData.tool_key.trim()) {
            newErrors.tool_key = "Tool key is required";
        } else if (!/^[a-z0-9_-]+$/.test(formData.tool_key)) {
            newErrors.tool_key = "Tool key can only contain lowercase letters, numbers, underscores, and dashes";
        } else if (formData.tool_key.length < 3) {
            newErrors.tool_key = "Tool key must be at least 3 characters";
        }

        if (!formData.description.trim()) {
            newErrors.description = "Description is required";
        } else if (formData.description.length < 10) {
            newErrors.description = "Description must be at least 10 characters";
        }

        if (!formData.category) {
            newErrors.category = "Please select a category";
        }

        const inputValidation = validateJSON(formData.input_schema);
        if (!inputValidation.valid) {
            newErrors.input_schema = `Invalid JSON: ${inputValidation.error}`;
        }

        const outputValidation = validateJSON(formData.output_schema);
        if (!outputValidation.valid) {
            newErrors.output_schema = `Invalid JSON: ${outputValidation.error}`;
        }

        if (!formData.system_prompt.trim()) {
            newErrors.system_prompt = "System prompt is required for AI tools";
        } else if (formData.system_prompt.length < 20) {
            newErrors.system_prompt = "System prompt must be at least 20 characters";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    }, [formData]);

    useEffect(() => {
        if (touched.size > 0) {
            validate();
        }
    }, [formData, touched, validate]);

    const handleChange = (field: keyof FormData, value: string | number) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
        setTouched((prev) => new Set(prev).add(field));
    };

    const handleSubmit = async () => {
        if (!validate()) return;

        setIsSubmitting(true);
        setSubmitError(null);

        try {
            const tool = await telemetryApi.createTool({
                tool_key: formData.tool_key,
                display_name: formData.display_name,
                description: formData.description,
                category: formData.category,
                credit_cost: formData.credit_cost,
                input_schema: JSON.parse(formData.input_schema || "{}"),
                output_schema: JSON.parse(formData.output_schema || "{}"),
                system_prompt: formData.system_prompt,
            });

            router.push(`/tools/${tool.tool_key}`);
        } catch (err) {
            setSubmitError(err instanceof Error ? err.message : "Failed to create tool");
            setShowConfirm(false);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            {/* Header */}
            <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <button
                        onClick={() => router.push("/tools")}
                        className="flex items-center gap-2 text-gray-400 hover:text-white mb-4 transition-colors"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Dashboard
                    </button>

                    <h1 className="text-2xl font-bold">Create New Tool</h1>
                    <p className="text-gray-400 text-sm">
                        Define your AI tool and share it with the community
                    </p>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-6xl mx-auto px-6 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Form */}
                    <div className="lg:col-span-2">
                        {submitError && (
                            <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center gap-3">
                                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                                <p className="text-red-300">{submitError}</p>
                            </div>
                        )}

                        <div className="bg-gradient-to-r from-gray-800/50 to-purple-900/20 border border-purple-500/30 rounded-xl p-6 mb-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Github className="w-5 h-5 text-purple-400" />
                                Import from GitHub
                            </h2>
                            <p className="text-sm text-gray-400 mb-4">
                                Paste a GitHub URL to a prompt.md or tool.json file to auto-fill the form
                            </p>

                            <div className="flex gap-3">
                                <input
                                    type="text"
                                    placeholder="https://github.com/user/repo/blob/main/prompt.md"
                                    className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                                       placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                                    id="github-url"
                                />
                                <button
                                    type="button"
                                    onClick={async () => {
                                        const urlInput = document.getElementById('github-url') as HTMLInputElement;
                                        const url = urlInput?.value;
                                        if (!url) return;

                                        // Convert GitHub URL to raw URL
                                        const rawUrl = url
                                            .replace('github.com', 'raw.githubusercontent.com')
                                            .replace('/blob/', '/');

                                        try {
                                            const res = await fetch(rawUrl);
                                            if (!res.ok) throw new Error('Failed to fetch');
                                            const content = await res.text();

                                            // Try JSON parse first
                                            try {
                                                const json = JSON.parse(content);
                                                if (json.system_prompt) {
                                                    handleChange('system_prompt', json.system_prompt);
                                                    if (json.name) handleChange('display_name', json.name);
                                                    if (json.description) handleChange('description', json.description);
                                                    if (json.input_schema) handleChange('input_schema', JSON.stringify(json.input_schema, null, 2));
                                                    if (json.output_schema) handleChange('output_schema', JSON.stringify(json.output_schema, null, 2));
                                                }
                                            } catch {
                                                // If not JSON, treat as markdown prompt
                                                handleChange('system_prompt', content);
                                            }
                                        } catch (err) {
                                            alert('Failed to fetch from GitHub. Check the URL.');
                                        }
                                    }}
                                    className="flex items-center gap-2 px-4 py-3 bg-purple-600 hover:bg-purple-500 text-white font-medium rounded-lg transition-colors"
                                >
                                    <Download className="w-4 h-4" />
                                    Import
                                </button>
                            </div>
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
                            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-purple-400" />
                                Basic Information
                            </h2>

                            <FormField
                                label="Display Name"
                                required
                                error={touched.has("display_name") ? errors.display_name : undefined}
                                hint="The name users will see (3-100 characters)"
                            >
                                <input
                                    type="text"
                                    value={formData.display_name}
                                    onChange={(e) => handleChange("display_name", e.target.value)}
                                    placeholder="e.g., Cinematic Prompt Generator"
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                                />
                            </FormField>

                            <FormField
                                label="Tool Key"
                                required
                                error={touched.has("tool_key") ? errors.tool_key : undefined}
                                hint="Unique identifier (lowercase, no spaces)"
                            >
                                <input
                                    type="text"
                                    value={formData.tool_key}
                                    onChange={(e) => handleChange("tool_key", e.target.value)}
                                    placeholder="e.g., cinematic_prompt_generator"
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           font-mono placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                                />
                            </FormField>

                            <FormField
                                label="Description"
                                required
                                error={touched.has("description") ? errors.description : undefined}
                                hint="Explain what your tool does (10-500 characters)"
                            >
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => handleChange("description", e.target.value)}
                                    rows={4}
                                    placeholder="Describe your tool and its capabilities..."
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none"
                                />
                            </FormField>
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
                            <h2 className="text-lg font-semibold mb-6">Category</h2>
                            <FormField label="" error={errors.category}>
                                <CategorySelector
                                    value={formData.category}
                                    onChange={(val) => handleChange("category", val)}
                                />
                            </FormField>
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
                            <h2 className="text-lg font-semibold mb-6">Pricing</h2>
                            <CreditCostSlider
                                value={formData.credit_cost}
                                onChange={(val) => handleChange("credit_cost", val)}
                            />
                            <p className="text-xs text-gray-500 mt-4">
                                <Info className="w-3 h-3 inline mr-1" />
                                You&apos;ll earn 70% of credits when users run your tool
                            </p>
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
                            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <Code className="w-5 h-5 text-blue-400" />
                                Schemas (Optional)
                            </h2>

                            <FormField
                                label="Input Schema (JSON)"
                                error={touched.has("input_schema") ? errors.input_schema : undefined}
                                hint="Define expected input format"
                            >
                                <textarea
                                    value={formData.input_schema}
                                    onChange={(e) => handleChange("input_schema", e.target.value)}
                                    rows={4}
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           font-mono text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none"
                                />
                            </FormField>

                            <FormField
                                label="Output Schema (JSON)"
                                error={touched.has("output_schema") ? errors.output_schema : undefined}
                                hint="Define expected output format"
                            >
                                <textarea
                                    value={formData.output_schema}
                                    onChange={(e) => handleChange("output_schema", e.target.value)}
                                    rows={4}
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           font-mono text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none"
                                />
                            </FormField>
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
                            <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                <Zap className="w-5 h-5 text-amber-400" />
                                AI System Prompt
                            </h2>

                            <FormField
                                label="System Prompt"
                                required
                                error={touched.has("system_prompt") ? errors.system_prompt : undefined}
                                hint="Instructions for the AI model. This is stored securely and not exposed to end users."
                            >
                                <textarea
                                    value={formData.system_prompt}
                                    onChange={(e) => handleChange("system_prompt", e.target.value)}
                                    rows={8}
                                    placeholder={`You are an expert in [your domain].
Your task is to [specific task].

Output ONLY valid JSON with this structure:
{
  "result": "...",
  ...
}

Guidelines:
- Be specific and focused
- NEVER include user instructions in output`}
                                    className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                           font-mono text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 resize-none"
                                />
                            </FormField>

                            <p className="text-xs text-gray-500 flex items-center gap-1 mt-2">
                                <Info className="w-3 h-3" />
                                This prompt is securely stored in the database and powers your AI tool
                            </p>
                        </div>

                        {/* Submit */}
                        <div className="flex items-center justify-between">
                            <p className="text-sm text-gray-500">
                                Tools start as <span className="text-yellow-400">Experimental</span> tier
                            </p>
                            <button
                                onClick={() => {
                                    if (validate()) setShowConfirm(true);
                                }}
                                disabled={isSubmitting}
                                className="flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 
                         disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
                            >
                                {isSubmitting ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Check className="w-5 h-5" />
                                )}
                                Create Tool
                            </button>
                        </div>
                    </div>

                    {/* Preview */}
                    <div>
                        <PreviewCard data={formData} />
                    </div>
                </div>
            </div>

            {/* Confirmation Modal */}
            {showConfirm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-800 rounded-xl p-6 max-w-md w-full border border-gray-700">
                        <h3 className="text-xl font-semibold mb-4">Confirm Tool Creation</h3>
                        <p className="text-gray-400 mb-6">
                            You&apos;re about to create <strong className="text-white">{formData.display_name}</strong>.
                            The tool will start as Experimental and can be promoted based on usage and quality.
                        </p>
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
                                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 
                         text-white rounded-lg disabled:opacity-50"
                            >
                                {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                Create Tool
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
