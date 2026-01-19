"use client";

/**
 * Warning when tool has no live version
 */

import { AlertTriangle } from "lucide-react";

interface Tool {
    id: string;
    tool_key: string;
    display_name: string;
    description: string;
}

interface NoLiveVersionWarningProps {
    tool: Tool;
    onCreatePlaceholder: () => void;
}

export function NoLiveVersionWarning({ tool: _tool, onCreatePlaceholder }: NoLiveVersionWarningProps) {
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
