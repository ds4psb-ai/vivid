"use client";

import { useState, useRef } from "react";
import {
    Play,
    CheckCircle,
    Upload,
    DollarSign,
    Loader2,
    FileVideo,
    X,
} from "lucide-react";
import { api } from "@/lib/api";

interface ActionConsoleProps {
    status: string;
    role: "client" | "creator" | "guest";
    onAction: (action: string, data?: unknown) => Promise<void>;
    assignmentId?: string;
    budget: number;
}

export default function ActionConsole({ status, role, onAction, budget }: ActionConsoleProps) {
    const [loading, setLoading] = useState(false);

    // Form states
    const [rating, setRating] = useState(5);
    const [feedback, setFeedback] = useState("");
    const [deliveryNotes, setDeliveryNotes] = useState("");

    // File upload states
    const [uploadedFiles, setUploadedFiles] = useState<{ uri: string; name: string }[]>([]);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setUploading(true);
        setUploadProgress(0);

        try {
            const uploadedList: { uri: string; name: string }[] = [];

            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                setUploadProgress(Math.floor(((i + 0.5) / files.length) * 100));

                const result = await api.uploadFile(file);
                uploadedList.push({ uri: result.file_uri, name: result.display_name || file.name });

                setUploadProgress(Math.floor(((i + 1) / files.length) * 100));
            }

            setUploadedFiles((prev) => [...prev, ...uploadedList]);
        } catch (error) {
            console.error("File upload failed:", error);
        } finally {
            setUploading(false);
            setUploadProgress(0);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    const removeFile = (index: number) => {
        setUploadedFiles((prev) => prev.filter((_, i) => i !== index));
    };

    const handleAction = async (action: string, data?: unknown) => {
        setLoading(true);
        try {
            await onAction(action, data);
        } finally {
            setLoading(false);
        }
    };

    // -------------------------------------------------------------------------
    // Renders based on Status + Role Matrix
    // -------------------------------------------------------------------------

    // 1. OPEN (Client: Cancel / Creator: None - Apply is separate)
    if (status === "open") {
        if (role === "client") {
            return (
                <div className="flex gap-2">
                    <button
                        onClick={() => handleAction("cancel")}
                        disabled={loading}
                        className="btn-secondary text-red-400 hover:text-red-300"
                    >
                        Cancel Request
                    </button>
                </div>
            );
        }
        return null; // Creators just browse
    }

    // 2. ASSIGNED (Client: Cancel / Creator: Accept/Reject)
    if (status === "assigned" && role === "creator") {
        return (
            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
                <h3 className="text-blue-400 font-medium mb-2">You have been assigned!</h3>
                <p className="text-sm text-[var(--fg-muted)] mb-4">
                    Review the budget of <span className="text-emerald-400">{budget} CR</span>.
                    Accepting starts the contract.
                </p>
                <div className="flex gap-3">
                    <button
                        onClick={() => handleAction("accept")}
                        disabled={loading}
                        className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                        Accept Assignment
                    </button>
                    <button
                        onClick={() => handleAction("reject")}
                        disabled={loading}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                    >
                        Reject
                    </button>
                </div>
            </div>
        );
    }

    // 3. PENDING (Internal state, treat as ASSIGNED)
    if (status === "pending" && role === "creator") {
        return (
            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                <h3 className="text-yellow-400 font-medium mb-2">Assignment Pending</h3>
                <p className="text-sm text-[var(--fg-muted)] mb-4">
                    Waiting for your acceptance.
                </p>
                <button
                    onClick={() => handleAction("accept")}
                    disabled={loading}
                    className="w-full bg-yellow-600 hover:bg-yellow-500 text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                    Accept & Start
                </button>
            </div>
        );
    }

    // 4. ACCEPTED / ACTIVE (Creator: Start Work / Deliver)
    if ((status === "accepted" || status === "active" || status === "in_progress") && role === "creator") {
        const isActive = status === "active" || status === "in_progress";

        return (
            <div className="space-y-4">
                {/* Stage Indicator */}
                <div className="flex items-center gap-2 text-sm text-[var(--fg-muted)]">
                    <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-slate-600'}`} />
                    Status: {isActive ? 'Work in Progress' : 'Ready to Start'}
                </div>

                {!isActive && (
                    <button
                        onClick={() => handleAction("start")}
                        disabled={loading}
                        className="w-full bg-violet-600 hover:bg-violet-500 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        Start Working
                    </button>
                )}

                {isActive && (
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
                        <h4 className="font-medium text-[var(--fg-0)] mb-3">Submit Delivery</h4>

                        {/* File Upload Section */}
                        <div className="mb-4">
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                accept="video/*,image/*,.pdf,.zip"
                                onChange={handleFileUpload}
                                className="hidden"
                                id="delivery-file-input"
                            />
                            <label
                                htmlFor="delivery-file-input"
                                className={`flex items-center justify-center gap-2 w-full py-3 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                                    uploading
                                        ? "border-violet-500/50 bg-violet-500/5"
                                        : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/50"
                                }`}
                            >
                                {uploading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin text-violet-400" />
                                        <span className="text-sm text-violet-400">Uploading... {uploadProgress}%</span>
                                    </>
                                ) : (
                                    <>
                                        <Upload className="w-4 h-4 text-slate-400" />
                                        <span className="text-sm text-slate-400">Click to upload files</span>
                                    </>
                                )}
                            </label>

                            {/* Uploaded Files List */}
                            {uploadedFiles.length > 0 && (
                                <div className="mt-3 space-y-2">
                                    {uploadedFiles.map((file, index) => (
                                        <div
                                            key={index}
                                            className="flex items-center justify-between p-2 bg-slate-950 rounded-lg border border-slate-800"
                                        >
                                            <div className="flex items-center gap-2 min-w-0">
                                                <FileVideo className="w-4 h-4 text-emerald-400 shrink-0" />
                                                <span className="text-sm text-slate-300 truncate">{file.name}</span>
                                            </div>
                                            <button
                                                onClick={() => removeFile(index)}
                                                className="p-1 hover:bg-slate-800 rounded transition-colors"
                                            >
                                                <X className="w-3 h-3 text-slate-500" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <textarea
                            value={deliveryNotes}
                            onChange={(e) => setDeliveryNotes(e.target.value)}
                            placeholder="Add notes about your work..."
                            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm mb-3 min-h-[80px]"
                        />
                        <button
                            onClick={() => handleAction("deliver", {
                                notes: deliveryNotes,
                                files: uploadedFiles.map((f) => f.uri)
                            })}
                            disabled={loading || uploadedFiles.length === 0}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2"
                        >
                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                            Submit Delivery ({uploadedFiles.length} file{uploadedFiles.length !== 1 ? 's' : ''})
                        </button>
                    </div>
                )}
            </div>
        );
    }

    // 5. REVIEW (Client: Approve / Requst Revisions)
    if (status === "review" && role === "client") {
        const creatorShare = Math.floor(budget * 0.75);
        const platformShare = Math.ceil(budget * 0.25);

        return (
            <div className="p-5 card-glass border-emerald-500/30">
                <div className="flex items-center gap-2 mb-4">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    <h3 className="text-lg font-bold text-[var(--fg-0)]">Ready for Review</h3>
                </div>

                <div className="mb-6 space-y-3">
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <div className="text-sm font-medium text-slate-400 mb-1">Settlement Preview</div>
                        <div className="flex justify-between items-center text-sm">
                            <span>Creator (75%)</span>
                            <span className="text-emerald-400 font-bold">{creatorShare} CR</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <span>Platform Fee (25%)</span>
                            <span className="text-slate-500">{platformShare} CR</span>
                        </div>
                        <div className="border-t border-slate-800 my-2 pt-2 flex justify-between items-center font-bold">
                            <span>Total Released</span>
                            <span className="text-[var(--fg-0)]">{budget} CR</span>
                        </div>
                    </div>

                    <div>
                        <label className="text-sm text-[var(--fg-muted)] mb-1 block">Rating</label>
                        <div className="flex gap-1 mb-2">
                            {[1, 2, 3, 4, 5].map((s) => (
                                <button
                                    key={s}
                                    onClick={() => setRating(s)}
                                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${rating >= s ? "bg-yellow-500/20 text-yellow-400" : "bg-slate-800 text-slate-600"
                                        }`}
                                >
                                    ★
                                </button>
                            ))}
                        </div>
                    </div>

                    <textarea
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        placeholder="Leave feedback for the creator..."
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm min-h-[60px]"
                    />
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <button
                        onClick={() => handleAction("approve", { rating, feedback })}
                        disabled={loading}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2"
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />}
                        Approve & Pay
                    </button>
                    <button
                        className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium py-2 rounded-lg"
                    >
                        Request Changes
                    </button>
                </div>
            </div>
        );
    }

    // 6. COMPLETED
    if (status === "completed") {
        return (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-center">
                <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                <h3 className="text-emerald-400 font-bold mb-1">Contract Completed</h3>
                <p className="text-sm text-[var(--fg-muted)]">
                    Funds have been released and the request is closed.
                </p>
            </div>
        );
    }

    // Default Fallback
    return (
        <div className="text-sm text-slate-500 text-center py-2">
            Status: {status} • Access: {role}
        </div>
    );
}
