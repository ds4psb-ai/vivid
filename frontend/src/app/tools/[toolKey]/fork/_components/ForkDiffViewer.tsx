"use client";

/**
 * Code Diff Viewer
 * Displays code differences with syntax highlighting
 */

interface ForkDiffViewerProps {
    diffContent: string;
}

export function ForkDiffViewer({ diffContent }: ForkDiffViewerProps) {
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
