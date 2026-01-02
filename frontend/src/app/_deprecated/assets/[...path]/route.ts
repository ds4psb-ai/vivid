import { NextResponse } from "next/server";
import { promises as fs, existsSync } from "fs";
import path from "path";

export const runtime = "nodejs";

const BASE_DIR = (() => {
    const candidates = [
        path.join(process.cwd(), "secure-assets", "assets"),
        path.join(process.cwd(), "frontend", "secure-assets", "assets"),
        path.join(process.cwd(), "..", "frontend", "secure-assets", "assets"),
    ];
    const found = candidates.find((candidate) => existsSync(candidate));
    return found || candidates[0];
})();

const MIME_TYPES: Record<string, string> = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".map": "application/json; charset=utf-8",
};

function resolveSafePath(segments: string[]) {
    const safeSegments = segments.length === 0 || !path.extname(segments[segments.length - 1])
        ? [...segments, "index.html"]
        : segments;
    const resolvedPath = path.resolve(BASE_DIR, ...safeSegments);
    if (!resolvedPath.startsWith(BASE_DIR + path.sep) && resolvedPath !== BASE_DIR) {
        return null;
    }
    return resolvedPath;
}

function getContentType(filePath: string) {
    const ext = path.extname(filePath).toLowerCase();
    return MIME_TYPES[ext] || "application/octet-stream";
}

export async function GET(
    _request: Request,
    { params }: { params: Promise<{ path?: string[] }> }
) {
    const { path: pathSegments } = await params;
    const segments = pathSegments ?? [];
    const resolvedPath = resolveSafePath(segments);
    if (!resolvedPath) {
        return NextResponse.json({ error: "Not found" }, { status: 404 });
    }

    try {
        const data = await fs.readFile(resolvedPath);
        return new NextResponse(data, {
            headers: {
                "Content-Type": getContentType(resolvedPath),
            },
        });
    } catch (error) {
        if (error instanceof Error && "code" in error && error.code === "ENOENT") {
            return NextResponse.json({ error: "Not found" }, { status: 404 });
        }
        throw error;
    }
}
