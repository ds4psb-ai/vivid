/**
 * App Migration Console
 * 
 * 내부 직원용 앱 마이그레이션 툴
 * - Google AI Studio URL 붙여넣기
 * - 코드 ZIP 업로드
 * - crebit.json 검증
 * - 원클릭 배포 (난독화 → SDK 주입 → 샌드박스 등록)
 */
"use client";

import { useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
    Upload, Link as LinkIcon, CheckCircle, AlertCircle, Loader2,
    FileCode, Package, Rocket, Eye, Settings,
    ChevronRight, X, Copy, List
} from "lucide-react";
import {
    registerAppWithFile,
    buildApp,
    type AppManifest
} from "@/lib/admin-api";

// ============================================
// Types
// ============================================

interface CrebitManifest {
    name: string;
    version: string;
    entry: string;
    description?: string;
    author?: string;
    dimension?: {
        theme?: string;
        primaryColor?: string;
        accentColor?: string;
        borderStyle?: string;
    };
    permissions?: string[];
    credits?: {
        perRun?: number;
        perSave?: number;
    };
    icon?: string;
    tags?: string[];
}

interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
    manifest?: CrebitManifest;
}

interface MigrationStep {
    id: string;
    label: string;
    status: "pending" | "running" | "success" | "error";
    error?: string;
}

type UploadMethod = "url" | "file" | null;

// ============================================
// Validation
// ============================================

function validateManifest(manifest: unknown): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!manifest || typeof manifest !== 'object') {
        return { valid: false, errors: ['crebit.json이 유효한 JSON이 아닙니다'], warnings };
    }

    const m = manifest as Record<string, unknown>;

    // Required fields
    if (!m.name || typeof m.name !== 'string') {
        errors.push('name 필드가 필요합니다');
    } else if (m.name.length > 100) {
        errors.push('name은 100자 이하여야 합니다');
    }

    if (!m.version || typeof m.version !== 'string') {
        errors.push('version 필드가 필요합니다');
    } else if (!/^\d+\.\d+\.\d+$/.test(m.version)) {
        errors.push('version은 semver 형식이어야 합니다 (예: 1.0.0)');
    }

    if (!m.entry || typeof m.entry !== 'string') {
        errors.push('entry 필드가 필요합니다');
    }

    // Optional but recommended
    if (!m.description) {
        warnings.push('description 추가를 권장합니다');
    }

    if (!m.dimension) {
        warnings.push('dimension 설정이 없으면 기본 테마가 적용됩니다');
    }

    // Dimension validation
    if (m.dimension && typeof m.dimension === 'object') {
        const dim = m.dimension as Record<string, unknown>;
        if (dim.primaryColor && typeof dim.primaryColor === 'string') {
            if (!/^#[0-9a-fA-F]{6}$/.test(dim.primaryColor)) {
                errors.push('primaryColor는 #RRGGBB 형식이어야 합니다');
            }
        }
        if (dim.accentColor && typeof dim.accentColor === 'string') {
            if (!/^#[0-9a-fA-F]{6}$/.test(dim.accentColor)) {
                errors.push('accentColor는 #RRGGBB 형식이어야 합니다');
            }
        }
    }

    // Permissions validation
    const validPermissions = [
        'credits.read', 'credits.deduct', 'storage.local', 'storage.cloud',
        'user.profile', 'clipboard.read', 'clipboard.write'
    ];
    if (m.permissions && Array.isArray(m.permissions)) {
        for (const perm of m.permissions) {
            if (!validPermissions.includes(perm)) {
                warnings.push(`알 수 없는 권한: ${perm}`);
            }
        }
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings,
        manifest: errors.length === 0 ? m as unknown as CrebitManifest : undefined,
    };
}

// ============================================
// Components
// ============================================

interface AppMigrationConsoleProps {
    onDeploy?: (manifest: CrebitManifest, appId: string) => Promise<void>;
}

export function AppMigrationConsole({ onDeploy }: AppMigrationConsoleProps) {
    const [uploadMethod, setUploadMethod] = useState<UploadMethod>(null);
    const [url, setUrl] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [validation, setValidation] = useState<ValidationResult | null>(null);
    const [deploySteps, setDeploySteps] = useState<MigrationStep[]>([]);
    const [isDeploying, setIsDeploying] = useState(false);
    const [deployedAppId, setDeployedAppId] = useState<string | null>(null);
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);

    const fileInputRef = useRef<HTMLInputElement>(null);

    // Handle URL paste
    const handleUrlSubmit = useCallback(async () => {
        if (!url.trim()) return;

        setIsLoading(true);
        setValidation(null);

        try {
            // In production: fetch and parse the URL content
            // For now: simulate validation
            await new Promise(r => setTimeout(r, 1000));

            // Mock manifest for demo
            const mockManifest: CrebitManifest = {
                name: "AI Studio App",
                version: "1.0.0",
                entry: "index.html",
                description: "Google AI Studio에서 생성된 앱",
                dimension: {
                    theme: "default",
                    primaryColor: "#84cc16",
                },
                permissions: ["credits.deduct"],
                credits: { perRun: 10 },
            };

            setValidation(validateManifest(mockManifest));
        } catch {
            setValidation({
                valid: false,
                errors: ["URL을 불러올 수 없습니다"],
                warnings: [],
            });
        } finally {
            setIsLoading(false);
        }
    }, [url]);

    // Handle file upload
    const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsLoading(true);
        setValidation(null);

        try {
            // In production: unzip and find crebit.json
            // For now: read as JSON if it's a JSON file
            if (file.name === "crebit.json") {
                const text = await file.text();
                const manifest = JSON.parse(text);
                setValidation(validateManifest(manifest));
            } else if (file.name.endsWith(".zip")) {
                // Save file for deployment
                setUploadedFile(file);
                // For ZIP: use filename as app name
                setValidation({
                    valid: true,
                    errors: [],
                    warnings: ["ZIP 파일이 준비되었습니다. 배포 시 crebit.json이 자동 생성됩니다."],
                    manifest: {
                        name: file.name.replace(".zip", ""),
                        version: "1.0.0",
                        entry: "index.html",
                    },
                });
            } else {
                setValidation({
                    valid: false,
                    errors: ["지원하지 않는 파일 형식입니다. ZIP 또는 crebit.json을 업로드하세요"],
                    warnings: [],
                });
            }
        } catch {
            setValidation({
                valid: false,
                errors: ["파일을 읽을 수 없습니다"],
                warnings: [],
            });
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Deploy app
    const handleDeploy = useCallback(async () => {
        if (!validation?.manifest) return;

        setIsDeploying(true);
        setDeployedAppId(null);

        const steps: MigrationStep[] = [
            { id: "validate", label: "매니페스트 검증", status: "pending" },
            { id: "bundle", label: "코드 번들링", status: "pending" },
            { id: "obfuscate", label: "난독화 처리", status: "pending" },
            { id: "inject", label: "SDK 주입", status: "pending" },
            { id: "register", label: "샌드박스 등록", status: "pending" },
        ];

        setDeploySteps(steps);

        try {
            // Step 1: Validate
            setDeploySteps(prev => prev.map((s, idx) => idx === 0 ? { ...s, status: "running" } : s));
            await new Promise(r => setTimeout(r, 300));
            setDeploySteps(prev => prev.map((s, idx) => idx === 0 ? { ...s, status: "success" } : s));

            // Step 2-4: Register app with file (backend handles bundling, obfuscation, SDK injection)
            setDeploySteps(prev => prev.map((s, idx) => idx === 1 ? { ...s, status: "running" } : s));

            let appId: string | undefined;

            if (uploadedFile) {
                // Real API call with file
                const result = await registerAppWithFile(validation.manifest as AppManifest, uploadedFile);

                if (!result.success) {
                    throw new Error(result.error || "등록 실패");
                }
                appId = result.appId;
            } else {
                // Mock for URL-based (future implementation)
                await new Promise(r => setTimeout(r, 500));
                appId = `app_${Date.now().toString(36)}`;
            }

            // Mark steps 2-4 as success
            for (let i = 1; i <= 3; i++) {
                setDeploySteps(prev => prev.map((s, idx) => idx === i ? { ...s, status: "success" } : s));
                await new Promise(r => setTimeout(r, 200));
            }

            // Step 5: Build (obfuscate + SDK inject)
            setDeploySteps(prev => prev.map((s, idx) => idx === 4 ? { ...s, status: "running" } : s));

            if (appId) {
                const buildResult = await buildApp(appId);
                if (!buildResult.success) {
                    throw new Error(buildResult.error || "빌드 실패");
                }
            }

            setDeploySteps(prev => prev.map((s, idx) => idx === 4 ? { ...s, status: "success" } : s));

            setDeployedAppId(appId || null);

            // Call onDeploy callback
            if (appId) {
                await onDeploy?.(validation.manifest, appId);
            }

        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : "배포 중 오류 발생";
            setDeploySteps(prev => prev.map(s =>
                s.status === "running"
                    ? { ...s, status: "error", error: errorMsg }
                    : s
            ));
        } finally {
            setIsDeploying(false);
        }
    }, [validation, uploadedFile, onDeploy]);

    // Reset
    const handleReset = () => {
        setUploadMethod(null);
        setUrl("");
        setValidation(null);
        setDeploySteps([]);
        setDeployedAppId(null);
        setUploadedFile(null);
    };

    return (
        <div className="min-h-screen bg-[#0a0a0b] text-white p-8">
            <div className="max-w-3xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl font-bold mb-2">앱 마이그레이션 콘솔</h1>
                        <p className="text-zinc-400 text-sm">
                            외부 앱을 Crebit 플랫폼에 안전하게 등록합니다
                        </p>
                    </div>
                    <Link
                        href="/admin/apps"
                        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm font-medium transition-colors"
                    >
                        <List className="w-4 h-4" />
                        앱 목록
                    </Link>
                </div>

                {/* Method Selection */}
                {!uploadMethod && !validation && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="grid grid-cols-2 gap-4"
                    >
                        <button
                            onClick={() => setUploadMethod("url")}
                            className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 hover:border-lime-500/50 transition-colors group"
                        >
                            <LinkIcon className="w-8 h-8 text-lime-400 mb-4 group-hover:scale-110 transition-transform" />
                            <h3 className="font-bold mb-2">URL 붙여넣기</h3>
                            <p className="text-sm text-zinc-500">
                                Google AI Studio 공유 링크를 붙여넣으세요
                            </p>
                        </button>

                        <button
                            onClick={() => setUploadMethod("file")}
                            className="p-6 rounded-2xl bg-zinc-900 border border-zinc-800 hover:border-lime-500/50 transition-colors group"
                        >
                            <Upload className="w-8 h-8 text-lime-400 mb-4 group-hover:scale-110 transition-transform" />
                            <h3 className="font-bold mb-2">파일 업로드</h3>
                            <p className="text-sm text-zinc-500">
                                ZIP 파일 또는 crebit.json을 업로드하세요
                            </p>
                        </button>
                    </motion.div>
                )}

                {/* URL Input */}
                {uploadMethod === "url" && !validation && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        <button
                            onClick={() => setUploadMethod(null)}
                            className="flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors"
                        >
                            <ChevronRight className="w-4 h-4 rotate-180" />
                            뒤로
                        </button>

                        <div className="flex gap-3">
                            <input
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="https://aistudio.google.com/app/..."
                                className="flex-1 px-4 py-3 rounded-xl bg-zinc-900 border border-zinc-800 focus:border-lime-500/50 focus:outline-none transition-colors"
                            />
                            <button
                                onClick={handleUrlSubmit}
                                disabled={!url.trim() || isLoading}
                                className="px-6 py-3 rounded-xl bg-lime-500 hover:bg-lime-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold transition-colors"
                            >
                                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : "불러오기"}
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* File Upload */}
                {uploadMethod === "file" && !validation && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        <button
                            onClick={() => setUploadMethod(null)}
                            className="flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors"
                        >
                            <ChevronRight className="w-4 h-4 rotate-180" />
                            뒤로
                        </button>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".zip,.json"
                            onChange={handleFileUpload}
                            className="hidden"
                        />

                        <button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={isLoading}
                            className="w-full p-12 rounded-2xl border-2 border-dashed border-zinc-700 hover:border-lime-500/50 transition-colors flex flex-col items-center gap-4"
                        >
                            {isLoading ? (
                                <Loader2 className="w-12 h-12 text-lime-400 animate-spin" />
                            ) : (
                                <>
                                    <Package className="w-12 h-12 text-zinc-500" />
                                    <div className="text-center">
                                        <p className="font-medium mb-1">파일을 드래그하거나 클릭하세요</p>
                                        <p className="text-sm text-zinc-500">ZIP 또는 crebit.json</p>
                                    </div>
                                </>
                            )}
                        </button>
                    </motion.div>
                )}

                {/* Validation Result */}
                {validation && !deployedAppId && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        <button
                            onClick={handleReset}
                            className="flex items-center gap-2 text-sm text-zinc-500 hover:text-white transition-colors"
                        >
                            <ChevronRight className="w-4 h-4 rotate-180" />
                            다시 시작
                        </button>

                        {/* Validation Status */}
                        <div className={`p-4 rounded-xl border ${validation.valid
                            ? "bg-green-500/10 border-green-500/30"
                            : "bg-red-500/10 border-red-500/30"
                            }`}>
                            <div className="flex items-center gap-3">
                                {validation.valid ? (
                                    <CheckCircle className="w-6 h-6 text-green-400" />
                                ) : (
                                    <AlertCircle className="w-6 h-6 text-red-400" />
                                )}
                                <div>
                                    <p className="font-bold">
                                        {validation.valid ? "검증 통과" : "검증 실패"}
                                    </p>
                                    <p className="text-sm text-zinc-400">
                                        {validation.valid
                                            ? "배포 준비가 완료되었습니다"
                                            : "아래 오류를 수정하세요"}
                                    </p>
                                </div>
                            </div>

                            {validation.errors.length > 0 && (
                                <ul className="mt-4 space-y-1">
                                    {validation.errors.map((err, i) => (
                                        <li key={i} className="text-sm text-red-400 flex items-start gap-2">
                                            <X className="w-4 h-4 shrink-0 mt-0.5" />
                                            {err}
                                        </li>
                                    ))}
                                </ul>
                            )}

                            {validation.warnings.length > 0 && (
                                <ul className="mt-4 space-y-1">
                                    {validation.warnings.map((warn, i) => (
                                        <li key={i} className="text-sm text-yellow-400 flex items-start gap-2">
                                            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                            {warn}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>

                        {/* Manifest Preview */}
                        {validation.manifest && (
                            <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800">
                                <h3 className="font-bold mb-4 flex items-center gap-2">
                                    <FileCode className="w-5 h-5 text-lime-400" />
                                    앱 정보
                                </h3>
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <p className="text-zinc-500">이름</p>
                                        <p className="font-medium">{validation.manifest.name}</p>
                                    </div>
                                    <div>
                                        <p className="text-zinc-500">버전</p>
                                        <p className="font-medium">{validation.manifest.version}</p>
                                    </div>
                                    <div>
                                        <p className="text-zinc-500">진입점</p>
                                        <p className="font-medium">{validation.manifest.entry}</p>
                                    </div>
                                    <div>
                                        <p className="text-zinc-500">크레딧/실행</p>
                                        <p className="font-medium">{validation.manifest.credits?.perRun ?? 0}</p>
                                    </div>
                                    {validation.manifest.dimension?.theme && (
                                        <div>
                                            <p className="text-zinc-500">차원 테마</p>
                                            <p className="font-medium">{validation.manifest.dimension.theme}</p>
                                        </div>
                                    )}
                                    {validation.manifest.dimension?.primaryColor && (
                                        <div>
                                            <p className="text-zinc-500">주 색상</p>
                                            <div className="flex items-center gap-2">
                                                <div
                                                    className="w-4 h-4 rounded"
                                                    style={{ backgroundColor: validation.manifest.dimension.primaryColor }}
                                                />
                                                <p className="font-medium">{validation.manifest.dimension.primaryColor}</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Deploy Steps */}
                        {deploySteps.length > 0 && (
                            <div className="p-4 rounded-xl bg-zinc-900 border border-zinc-800">
                                <h3 className="font-bold mb-4 flex items-center gap-2">
                                    <Settings className="w-5 h-5 text-lime-400" />
                                    배포 진행
                                </h3>
                                <div className="space-y-3">
                                    {deploySteps.map((step) => (
                                        <div key={step.id} className="flex items-center gap-3">
                                            {step.status === "pending" && (
                                                <div className="w-5 h-5 rounded-full border-2 border-zinc-600" />
                                            )}
                                            {step.status === "running" && (
                                                <Loader2 className="w-5 h-5 text-lime-400 animate-spin" />
                                            )}
                                            {step.status === "success" && (
                                                <CheckCircle className="w-5 h-5 text-green-400" />
                                            )}
                                            {step.status === "error" && (
                                                <AlertCircle className="w-5 h-5 text-red-400" />
                                            )}
                                            <span className={
                                                step.status === "success" ? "text-green-400" :
                                                    step.status === "error" ? "text-red-400" :
                                                        step.status === "running" ? "text-lime-400" :
                                                            "text-zinc-500"
                                            }>
                                                {step.label}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Deploy Button */}
                        {validation.valid && !isDeploying && deploySteps.length === 0 && (
                            <button
                                onClick={handleDeploy}
                                className="w-full py-4 rounded-xl bg-lime-500 hover:bg-lime-400 text-black font-bold text-lg transition-colors flex items-center justify-center gap-2"
                            >
                                <Rocket className="w-5 h-5" />
                                원클릭 배포
                            </button>
                        )}
                    </motion.div>
                )}

                {/* Deploy Success */}
                {deployedAppId && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-8 rounded-2xl bg-gradient-to-br from-lime-500/20 to-emerald-500/20 border border-lime-500/30 text-center"
                    >
                        <CheckCircle className="w-16 h-16 text-lime-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold mb-2">배포 완료!</h2>
                        <p className="text-zinc-400 mb-6">
                            앱이 성공적으로 등록되었습니다
                        </p>

                        <div className="p-4 rounded-xl bg-black/30 mb-6">
                            <p className="text-sm text-zinc-500 mb-2">App ID</p>
                            <div className="flex items-center justify-center gap-2">
                                <code className="text-lg font-mono text-lime-400">{deployedAppId}</code>
                                <button
                                    onClick={() => navigator.clipboard.writeText(deployedAppId)}
                                    className="p-1.5 rounded-lg hover:bg-white/10 transition-colors"
                                >
                                    <Copy className="w-4 h-4 text-zinc-400" />
                                </button>
                            </div>
                        </div>

                        <div className="flex gap-3 justify-center">
                            <button
                                onClick={handleReset}
                                className="px-6 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 font-medium transition-colors"
                            >
                                새 앱 등록
                            </button>
                            <Link
                                href={`/sandbox/${deployedAppId}`}
                                className="px-6 py-3 rounded-xl bg-lime-500 hover:bg-lime-400 text-black font-bold transition-colors flex items-center gap-2"
                            >
                                <Eye className="w-4 h-4" />
                                미리보기
                            </Link>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
}

export default AppMigrationConsole;
