import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Middleware for Route Protection and Legacy Redirects
 *
 * Features:
 * 1. Route protection: Checks for `crebit_session` cookie
 * 2. Legacy redirects: Redirects old dimension URLs to mega app hubs
 *
 * P1 Hardening: Added /admin/* and /humancloud/* protection
 * 2026 Mega Apps: Added legacy URL redirects for backward compatibility
 *
 * @see https://nextjs.org/docs/app/building-your-application/routing/middleware
 */

const PROTECTED_ROUTES = [
    "/settings",
    "/billing",
    "/usage",
    "/teaching",
    "/ainspire",
    "/admin",       // P1: Admin routes require authentication
    "/humancloud",  // P1: Human Cloud routes require authentication
    "/creator",     // P1: Creator dashboard requires authentication
    "/settlements", // P1: Settlement routes require authentication
    // Note: "/" (Academy) is not protected here - EnrollmentRequired handles access control
];

const PUBLIC_ROUTES = [
    "/",
    "/login",
    "/api",
    "/_next",
    "/images",
    "/assets",
    "/favicon",
];

const PRIVATE_MEDIA_ROUTES = ["/teaching", "/ainspire"];

/**
 * Legacy URL redirects for 2026 Mega Apps
 *
 * Old dimension URLs → New mega app hubs
 * These redirects ensure backward compatibility for bookmarks and links.
 */
const LEGACY_REDIRECTS: Record<string, string> = {
    "/dimension/aesthetic": "/dna-lab?tab=ad",
    "/dimension/abyss": "/dna-lab?tab=mirror",
    "/dimension/quality-check": "/dna-lab?tab=qc",
    "/dimension/story-architect": "/story-engine?tab=story",
    "/dimension/prompt": "/story-engine?tab=prompt",
    "/dimension/video-maker": "/production?provider=veo",
    "/dimension/kling": "/production?provider=kling",
    "/dimension/suno": "/production?provider=suno",
};

const SESSION_COOKIE_NAME = "crebit_session";

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Auth is now enabled - protected routes require authentication

    // Check for legacy redirects first (2026 Mega Apps)
    const redirectTarget = LEGACY_REDIRECTS[pathname];
    if (redirectTarget) {
        const redirectUrl = new URL(redirectTarget, request.url);
        return NextResponse.redirect(redirectUrl, { status: 301 }); // Permanent redirect
    }

    // Skip public routes (exact match for "/" , prefix match for others)
    const isPublic = PUBLIC_ROUTES.some((route) => {
        if (route === "/") return pathname === "/";
        return pathname.startsWith(route);
    });

    if (isPublic) {
        return NextResponse.next();
    }

    // Check if route is protected
    const isProtected = PROTECTED_ROUTES.some((route) => pathname.startsWith(route));

    if (!isProtected) {
        return NextResponse.next();
    }

    // Check for session cookie
    const sessionCookie = request.cookies.get(SESSION_COOKIE_NAME);

    if (!sessionCookie?.value) {
        // Redirect to login with return URL
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("returnTo", pathname);
        return NextResponse.redirect(loginUrl);
    }

    // Allow request to continue
    const response = NextResponse.next();

    if (PRIVATE_MEDIA_ROUTES.some((route) => pathname.startsWith(route))) {
        response.headers.set("Cache-Control", "private, no-store, max-age=0");
        response.headers.set("X-Robots-Tag", "noindex, nofollow");
    }

    return response;
}

export const config = {
    matcher: [
        // Protected routes
        "/settings/:path*",
        "/billing/:path*",
        "/usage/:path*",
        "/teaching/:path*",
        "/ainspire/:path*",
        "/admin/:path*",       // P1: Admin routes
        "/humancloud/:path*",  // P1: Human Cloud routes
        "/creator/:path*",     // P1: Creator routes
        "/settlements/:path*", // P1: Settlement routes
        // Legacy dimension redirects (2026 Mega Apps)
        "/dimension/aesthetic",
        "/dimension/abyss",
        "/dimension/quality-check",
        "/dimension/story-architect",
        "/dimension/prompt",
        "/dimension/video-maker",
        "/dimension/kling",
        "/dimension/suno",
    ],
};
