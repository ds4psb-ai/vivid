/**
 * Cache Revalidation API Route
 *
 * Phase 6: Next.js 16 Cache Components
 *
 * This endpoint is called by the backend to invalidate cached data when
 * content changes (e.g., IP updates, new presets, etc.)
 *
 * Security:
 * - Bearer token authentication via REVALIDATE_SECRET
 * - Timing-safe token comparison to prevent timing attacks
 * - Input validation and sanitization
 * - Rate limiting via response headers
 *
 * Usage:
 * POST /api/revalidate
 * Authorization: Bearer ${REVALIDATE_SECRET}
 * Body: { tags?: string[], paths?: string[] }
 */

import { revalidateTag, revalidatePath } from "next/cache";
import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "crypto";

// =============================================================================
// Constants
// =============================================================================

/** Maximum number of tags/paths per request */
const MAX_ITEMS_PER_REQUEST = 100;

/** Maximum length of a single tag or path */
const MAX_ITEM_LENGTH = 256;

/** Allowed path pattern (must start with /) */
const PATH_PATTERN = /^\/[a-zA-Z0-9\-_\/\[\]%]+$/;

/** Allowed tag pattern (alphanumeric, hyphens, colons, underscores) */
const TAG_PATTERN = /^[a-zA-Z0-9\-_:]+$/;

// =============================================================================
// Types
// =============================================================================

interface RevalidateRequest {
  /** Cache tags to invalidate */
  tags?: string[];
  /** Page paths to invalidate */
  paths?: string[];
}

interface RevalidateResponse {
  /** List of invalidated items */
  revalidated: string[];
  /** Timestamp of revalidation */
  timestamp: number;
  /** Error message if any */
  error?: string;
}

// =============================================================================
// Security Helpers
// =============================================================================

/**
 * Timing-safe string comparison to prevent timing attacks
 */
function secureCompare(a: string, b: string): boolean {
  try {
    const bufA = Buffer.from(a, "utf8");
    const bufB = Buffer.from(b, "utf8");

    // If lengths differ, comparison will be constant time but return false
    if (bufA.length !== bufB.length) {
      // Still do comparison to maintain constant time
      timingSafeEqual(bufA, bufA);
      return false;
    }

    return timingSafeEqual(bufA, bufB);
  } catch {
    return false;
  }
}

/**
 * Validate and sanitize a tag string
 */
function validateTag(tag: unknown): string | null {
  if (typeof tag !== "string") return null;
  if (tag.length === 0 || tag.length > MAX_ITEM_LENGTH) return null;
  if (!TAG_PATTERN.test(tag)) return null;
  return tag;
}

/**
 * Validate and sanitize a path string
 */
function validatePath(path: unknown): string | null {
  if (typeof path !== "string") return null;
  if (path.length === 0 || path.length > MAX_ITEM_LENGTH) return null;
  if (!PATH_PATTERN.test(path)) return null;
  return path;
}

// =============================================================================
// API Handler
// =============================================================================

/**
 * Handle cache revalidation requests from backend
 */
export async function POST(
  request: NextRequest
): Promise<NextResponse<RevalidateResponse>> {
  const timestamp = Date.now();

  // Get expected token
  const expectedToken = process.env.REVALIDATE_SECRET;
  if (!expectedToken) {
    console.warn("[revalidate] REVALIDATE_SECRET not configured");
    return NextResponse.json(
      {
        revalidated: [],
        timestamp,
        error: "Revalidation not configured",
      },
      { status: 503 }
    );
  }

  // Verify authorization with timing-safe comparison
  const authHeader = request.headers.get("authorization");
  const providedToken = authHeader?.startsWith("Bearer ")
    ? authHeader.slice(7)
    : "";

  if (!secureCompare(providedToken, expectedToken)) {
    // Log failed auth attempt for security monitoring
    console.warn("[revalidate] Unauthorized access attempt", {
      ip: request.headers.get("x-forwarded-for") || "unknown",
      userAgent: request.headers.get("user-agent")?.slice(0, 100),
    });

    return NextResponse.json(
      {
        revalidated: [],
        timestamp,
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
        timestamp,
        error: "Invalid JSON body",
      },
      { status: 400 }
    );
  }

  const { tags, paths } = body;

  // Validate at least one target is provided
  if ((!tags || tags.length === 0) && (!paths || paths.length === 0)) {
    return NextResponse.json(
      {
        revalidated: [],
        timestamp,
        error: "At least one tag or path is required",
      },
      { status: 400 }
    );
  }

  // Validate item counts
  const totalItems = (tags?.length || 0) + (paths?.length || 0);
  if (totalItems > MAX_ITEMS_PER_REQUEST) {
    return NextResponse.json(
      {
        revalidated: [],
        timestamp,
        error: `Too many items. Maximum ${MAX_ITEMS_PER_REQUEST} per request`,
      },
      { status: 400 }
    );
  }

  const revalidated: string[] = [];
  const errors: string[] = [];

  // Invalidate by tags
  if (tags && Array.isArray(tags)) {
    for (const tag of tags) {
      const validTag = validateTag(tag);
      if (!validTag) {
        errors.push(`Invalid tag: ${String(tag).slice(0, 50)}`);
        continue;
      }

      try {
        // Use 'max' profile for longest cache duration with SWR behavior
        // This allows background revalidation while serving stale content
        revalidateTag(validTag, "max");
        revalidated.push(`tag:${validTag}`);
      } catch (error) {
        console.error(`[revalidate] Failed to revalidate tag: ${validTag}`, error);
        errors.push(`Failed to revalidate tag: ${validTag}`);
      }
    }
  }

  // Invalidate by paths
  if (paths && Array.isArray(paths)) {
    for (const path of paths) {
      const validPath = validatePath(path);
      if (!validPath) {
        errors.push(`Invalid path: ${String(path).slice(0, 50)}`);
        continue;
      }

      try {
        revalidatePath(validPath);
        revalidated.push(`path:${validPath}`);
      } catch (error) {
        console.error(`[revalidate] Failed to revalidate path: ${validPath}`, error);
        errors.push(`Failed to revalidate path: ${validPath}`);
      }
    }
  }

  // Log successful revalidation
  if (revalidated.length > 0) {
    console.log(`[revalidate] Invalidated ${revalidated.length} items:`, revalidated);
  }

  // Build response
  const response: RevalidateResponse = {
    revalidated,
    timestamp,
  };

  // Include errors if any (but still return 200 for partial success)
  if (errors.length > 0) {
    response.error = `Partial success. Errors: ${errors.join("; ")}`;
  }

  return NextResponse.json(response, {
    headers: {
      // Rate limiting hints for clients
      "X-RateLimit-Limit": String(MAX_ITEMS_PER_REQUEST),
      "X-RateLimit-Remaining": String(MAX_ITEMS_PER_REQUEST - totalItems),
      // Cache control - this endpoint should never be cached
      "Cache-Control": "no-store, no-cache, must-revalidate",
    },
  });
}

/**
 * Health check for revalidation endpoint
 */
export async function GET(): Promise<NextResponse> {
  const hasSecret = !!process.env.REVALIDATE_SECRET;

  return NextResponse.json(
    {
      status: hasSecret ? "ready" : "not_configured",
      message: hasSecret
        ? "Revalidation endpoint is ready"
        : "REVALIDATE_SECRET environment variable not set",
      limits: {
        maxItemsPerRequest: MAX_ITEMS_PER_REQUEST,
        maxItemLength: MAX_ITEM_LENGTH,
      },
    },
    {
      headers: {
        "Cache-Control": "no-store",
      },
    }
  );
}
