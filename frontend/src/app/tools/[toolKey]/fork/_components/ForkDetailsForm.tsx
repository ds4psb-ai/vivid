"use client";

/**
 * Fork Details Form
 * Input fields for fork key, display name, and changelog
 */

import { Zap } from "lucide-react";

interface ForkDetailsFormProps {
    forkKey: string;
    forkName: string;
    changelog: string;
    onForkKeyChange: (value: string) => void;
    onForkNameChange: (value: string) => void;
    onChangelogChange: (value: string) => void;
}

export function ForkDetailsForm({
    forkKey,
    forkName,
    changelog,
    onForkKeyChange,
    onForkNameChange,
    onChangelogChange,
}: ForkDetailsFormProps) {
    return (
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
                        onChange={(e) => onForkKeyChange(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
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
                        onChange={(e) => onForkNameChange(e.target.value)}
                        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                    />
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1.5">Changelog</label>
                    <textarea
                        value={changelog}
                        onChange={(e) => onChangelogChange(e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white resize-none focus:outline-none focus:border-purple-500"
                        placeholder="What did you change? (optional)"
                    />
                </div>
            </div>
        </div>
    );
}
