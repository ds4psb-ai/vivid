"use client";

/**
 * Sybil Warning Alert
 */

import { Shield } from "lucide-react";

interface SybilWarningProps {
    warning: string;
}

export function SybilWarning({ warning }: SybilWarningProps) {
    return (
        <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
            <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                <div>
                    <h4 className="font-medium text-orange-400 mb-1">Low Originality</h4>
                    <p className="text-sm text-gray-300">{warning}</p>
                </div>
            </div>
        </div>
    );
}
