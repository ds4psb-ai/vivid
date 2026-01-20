/**
 * Diff Viewer Component
 * 
 * Displays unified diff with syntax highlighting.
 */

interface DiffViewerProps {
    diffContent: string;
    maxHeight?: string;
    title?: string;
}

export function DiffViewer({
    diffContent,
    maxHeight = "max-h-80",
    title,
}: DiffViewerProps) {
    const lines = diffContent.split("\n");

    return (
        <div className="border border-white/10 bg-[var(--surface-2)]/70 rounded-lg overflow-hidden font-mono text-sm">
            {title && (
                <div className="bg-[var(--surface-3)]/80 px-4 py-2 border-b border-white/10">
                    <span className="text-[var(--fg-subtle)]">{title}</span>
                </div>
            )}
            <div className={`${maxHeight} overflow-y-auto p-4`}>
                {lines.length === 0 || (lines.length === 1 && !lines[0]) ? (
                    <div className="text-[var(--fg-subtle)] text-center py-8">
                        No changes to display
                    </div>
                ) : (
                    lines.map((line, i) => {
                        let className = "text-[var(--fg-muted)]";
                        let bgClass = "";

                        if (line.startsWith("+") && !line.startsWith("+++")) {
                            className = "text-green-400";
                            bgClass = "bg-green-500/10";
                        } else if (line.startsWith("-") && !line.startsWith("---")) {
                            className = "text-red-400";
                            bgClass = "bg-red-500/10";
                        } else if (line.startsWith("@@")) {
                            className = "text-blue-400";
                        } else if (line.startsWith("+++") || line.startsWith("---")) {
                            className = "text-[var(--fg-subtle)]";
                        }

                        return (
                            <div
                                key={i}
                                className={`${className} ${bgClass} px-2 py-0.5 whitespace-pre`}
                            >
                                {line || " "}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default DiffViewer;
