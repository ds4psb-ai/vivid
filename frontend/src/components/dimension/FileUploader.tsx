"use client";

/**
 * FileUploader - Drag & drop file upload component for Dimension panels
 *
 * Features:
 * - Drag & drop + click to upload
 * - File type/size validation
 * - Thumbnail preview
 * - Progress indicator
 * - Theme color support
 */

import { useState, useCallback, useRef, type DragEvent, type ChangeEvent } from "react";
import { Upload, X, Image, Film, FileText, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { type ThemeColor, THEME_COLOR_CLASSES } from "@/lib/dimension-theme";

export interface FileUploaderProps {
    /** Allowed file types (e.g., ["image/*", "video/*"]) */
    accept: string[];
    /** Maximum file size in MB */
    maxSizeMB: number;
    /** Callback when files are uploaded */
    onUpload: (files: File[]) => void;
    /** Allow multiple file selection */
    multiple?: boolean;
    /** Show thumbnail preview */
    preview?: boolean;
    /** Disabled state */
    disabled?: boolean;
    /** Theme color */
    themeColor?: ThemeColor;
    /** Optional label */
    label?: string;
    /** Optional helper text */
    helperText?: string;
}

interface FilePreview {
    file: File;
    url: string;
    type: "image" | "video" | "other";
}

function getFileType(file: File): "image" | "video" | "other" {
    if (file.type.startsWith("image/")) return "image";
    if (file.type.startsWith("video/")) return "video";
    return "other";
}

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUploader({
    accept,
    maxSizeMB,
    onUpload,
    multiple = false,
    preview = true,
    disabled = false,
    themeColor = "emerald",
    label,
    helperText,
}: FileUploaderProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [files, setFiles] = useState<FilePreview[]>([]);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const colors = THEME_COLOR_CLASSES[themeColor];

    const maxSizeBytes = maxSizeMB * 1024 * 1024;

    const validateFile = useCallback(
        (file: File): string | null => {
            // Check file size
            if (file.size > maxSizeBytes) {
                return `파일이 너무 큽니다 (최대 ${maxSizeMB}MB)`;
            }

            // Check file type
            const isAccepted = accept.some((type) => {
                if (type.endsWith("/*")) {
                    const category = type.replace("/*", "");
                    return file.type.startsWith(category);
                }
                return file.type === type;
            });

            if (!isAccepted) {
                return `지원하지 않는 파일 형식입니다`;
            }

            return null;
        },
        [accept, maxSizeBytes, maxSizeMB]
    );

    const handleFiles = useCallback(
        (newFiles: FileList | File[]) => {
            setError(null);
            const fileArray = Array.from(newFiles);

            // Validate all files first
            for (const file of fileArray) {
                const validationError = validateFile(file);
                if (validationError) {
                    setError(validationError);
                    return;
                }
            }

            // Create previews
            const previews: FilePreview[] = fileArray.map((file) => ({
                file,
                url: URL.createObjectURL(file),
                type: getFileType(file),
            }));

            // Update state
            if (multiple) {
                setFiles((prev) => [...prev, ...previews]);
                onUpload([...files.map((f) => f.file), ...fileArray]);
            } else {
                // Revoke old URLs
                files.forEach((f) => URL.revokeObjectURL(f.url));
                setFiles(previews.slice(0, 1));
                onUpload([fileArray[0]]);
            }
        },
        [files, multiple, onUpload, validateFile]
    );

    const handleDragOver = useCallback(
        (e: DragEvent<HTMLDivElement>) => {
            e.preventDefault();
            e.stopPropagation();
            if (!disabled) {
                setIsDragging(true);
            }
        },
        [disabled]
    );

    const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback(
        (e: DragEvent<HTMLDivElement>) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(false);

            if (disabled) return;

            const droppedFiles = e.dataTransfer.files;
            if (droppedFiles.length > 0) {
                handleFiles(droppedFiles);
            }
        },
        [disabled, handleFiles]
    );

    const handleInputChange = useCallback(
        (e: ChangeEvent<HTMLInputElement>) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFiles(e.target.files);
            }
        },
        [handleFiles]
    );

    const handleRemove = useCallback(
        (index: number) => {
            setFiles((prev) => {
                const newFiles = [...prev];
                URL.revokeObjectURL(newFiles[index].url);
                newFiles.splice(index, 1);
                onUpload(newFiles.map((f) => f.file));
                return newFiles;
            });
        },
        [onUpload]
    );

    const handleClick = useCallback(() => {
        if (!disabled) {
            inputRef.current?.click();
        }
    }, [disabled]);

    return (
        <div className="space-y-2">
            {/* Label */}
            {label && (
                <label className="text-[10px] font-bold text-slate-500 dark:text-[var(--fg-muted)] uppercase tracking-widest ml-1">
                    {label}
                </label>
            )}

            {/* Drop Zone */}
            <div
                onClick={handleClick}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`
                    relative w-full min-h-[120px] rounded-xl border-2 border-dashed transition-all cursor-pointer
                    ${disabled ? "opacity-50 cursor-not-allowed" : ""}
                    ${isDragging
                        ? `${colors.border.replace("border-", "border-")} ${colors.bg} scale-[1.02]`
                        : "border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 hover:border-slate-300 dark:hover:border-white/20 hover:bg-slate-50 dark:hover:bg-white/[0.07]"
                    }
                `}
            >
                <input
                    ref={inputRef}
                    type="file"
                    accept={accept.join(",")}
                    multiple={multiple}
                    onChange={handleInputChange}
                    disabled={disabled}
                    className="hidden"
                />

                {/* Empty State */}
                {files.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-8 px-4">
                        <div className={`p-3 rounded-xl ${colors.bg} mb-3`}>
                            <Upload className={`w-6 h-6 ${colors.text}`} />
                        </div>
                        <p className="text-sm font-medium text-slate-700 dark:text-white/80 mb-1">
                            파일을 드래그하거나 클릭하세요
                        </p>
                        <p className="text-xs text-slate-500 dark:text-white/40">
                            {accept.join(", ")} · 최대 {maxSizeMB}MB
                        </p>
                    </div>
                )}

                {/* Previews */}
                {preview && files.length > 0 && (
                    <div className="p-4">
                        <div className="flex flex-wrap gap-3">
                            <AnimatePresence mode="popLayout">
                                {files.map((file, index) => (
                                    <motion.div
                                        key={file.url}
                                        initial={{ opacity: 0, scale: 0.8 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.8 }}
                                        layout
                                        className="relative group"
                                    >
                                        {/* Thumbnail */}
                                        <div className="w-24 h-24 rounded-lg overflow-hidden bg-slate-100 dark:bg-white/10 border border-slate-200 dark:border-white/10">
                                            {file.type === "image" && (
                                                // eslint-disable-next-line @next/next/no-img-element
                                                <img
                                                    src={file.url}
                                                    alt={file.file.name}
                                                    className="w-full h-full object-cover"
                                                />
                                            )}
                                            {file.type === "video" && (
                                                <div className="w-full h-full flex items-center justify-center">
                                                    <Film className="w-8 h-8 text-slate-400 dark:text-white/40" />
                                                </div>
                                            )}
                                            {file.type === "other" && (
                                                <div className="w-full h-full flex items-center justify-center">
                                                    <FileText className="w-8 h-8 text-slate-400 dark:text-white/40" />
                                                </div>
                                            )}
                                        </div>

                                        {/* File Info */}
                                        <div className="mt-1 max-w-24">
                                            <p className="text-xs text-slate-600 dark:text-white/60 truncate">
                                                {file.file.name}
                                            </p>
                                            <p className="text-[10px] text-slate-400 dark:text-white/30">
                                                {formatFileSize(file.file.size)}
                                            </p>
                                        </div>

                                        {/* Remove Button */}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRemove(index);
                                            }}
                                            className="absolute -top-2 -right-2 p-1 rounded-full bg-rose-500 text-white opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    </motion.div>
                                ))}
                            </AnimatePresence>

                            {/* Add More Button (if multiple) */}
                            {multiple && (
                                <div className="w-24 h-24 rounded-lg border-2 border-dashed border-slate-200 dark:border-white/10 flex items-center justify-center hover:border-slate-300 dark:hover:border-white/20 transition-colors">
                                    <Upload className="w-6 h-6 text-slate-300 dark:text-white/20" />
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Error */}
            {error && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-rose-500/10 border border-rose-500/20"
                >
                    <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                    <p className="text-xs text-rose-400">{error}</p>
                </motion.div>
            )}

            {/* Helper Text */}
            {helperText && !error && (
                <p className="text-xs text-slate-500 dark:text-white/40 ml-1">{helperText}</p>
            )}
        </div>
    );
}
