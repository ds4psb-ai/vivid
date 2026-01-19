/**
 * Cache Revalidation API Route
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * This endpoint is called by the backend to invalidate cached data when
 * content changes (e.g., IP updates, new presets, etc.)
 *
 * Authentication: Bearer token via REVALIDATE_SECRET env var
 *
 * Usage:
 * POST /api/revalidate
 * Authorization: Bearer ${REVALIDATE_SECRET}
 * Body: { tags?: string[], paths?: string[] }
 */

import { revalidateTag, revalidatePath } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

// Request body schema
interface RevalidateRequest {
  /** Cache tags to invalidate */
  tags?: string[];
  /** Page paths to invalidate */
  paths?: string[];
}

// Response schema
interface RevalidateResponse {
  /** List of invalidated items */
  revalidated: string[];
  /** Timestamp of revalidation */
  timestamp: number;
  /** Error message if any */
  error?: string;
}

/**
 * Handle cache revalidation requests from backend
 */
export async function POST(
  request: NextRequest
): Promise<NextResponse<RevalidateResponse>> {
  // Verify authorization
  const authHeader = request.headers.get("authorization");
  const expectedToken = process.env.REVALIDATE_SECRET;

  if (!expectedToken) {
    console.warn("[revalidate] REVALIDATE_SECRET not configured");
    return NextResponse.json(
      {
        revalidated: [],
        timestamp: Date.now(),
        error: "Revalidation not configured",
      },
      { status: 503 }
    );
  }

  if (authHeader !== `Bearer ${expectedToken}`) {
    return NextResponse.json(
      {
        revalidated: [],
        timestamp: Date.now(),
        error: "Unauthorized",
      },
      { status: 401 }
    );
  }

  // Parse request body
  let body: RevalidateRequest;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      {
        revalidated: [],
        timestamp: Date.now(),
        error: "Invalid JSON body",
      },
      { status: 400 }
    );
  }

  const { tags, paths } = body;
  const revalidated: string[] = [];

  // Validate at least one target is provided
  if ((!tags || tags.length === 0) && (!paths || paths.length === 0)) {
    return NextResponse.json(
      {
        revalidated: [],
        timestamp: Date.now(),
        error: "At least one tag or path is required",
      },
      { status: 400 }
    );
  }

  // Invalidate by tags
  // Next.js 16: revalidateTag requires a profile argument for SWR behavior
  // Using 'max' profile for immediate stale-while-revalidate
  if (tags && Array.isArray(tags)) {
    for (const tag of tags) {
      if (typeof tag === "string" && tag.length > 0) {
        try {
          // Use 'max' profile for longest cache duration with SWR
          revalidateTag(tag, "max");
          revalidated.push(`tag:${tag}`);
        } catch (error) {
          console.error(`[revalidate] Failed to revalidate tag: ${tag}`, error);
        }
      }
    }
  }

  // Invalidate by paths
  if (paths && Array.isArray(paths)) {
    for (const path of paths) {
      if (typeof path === "string" && path.startsWith("/")) {
        try {
          revalidatePath(path);
          revalidated.push(`path:${path}`);
        } catch (error) {
          console.error(
            `[revalidate] Failed to revalidate path: ${path}`,
            error
          );
        }
      }
    }
  }

  console.log(`[revalidate] Invalidated ${revalidated.length} items:`, revalidated);

  return NextResponse.json({
    revalidated,
    timestamp: Date.now(),
  });
}

/**
 * Health check for revalidation endpoint
 */
export async function GET(): Promise<NextResponse> {
  const hasSecret = !!process.env.REVALIDATE_SECRET;

  return NextResponse.json({
    status: hasSecret ? "ready" : "not_configured",
    message: hasSecret
      ? "Revalidation endpoint is ready"
      : "REVALIDATE_SECRET environment variable not set",
  });
}
