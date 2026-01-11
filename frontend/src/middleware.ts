import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js Middleware for Route Protection
 * 
 * Checks for `crebit_session` cookie and redirects to /login
 * for protected routes if not authenticated.
 * 
 * @see https://nextjs.org/docs/app/building-your-application/routing/middleware
 */

const PROTECTED_ROUTES = [
    "/settings",
    "/billing",
    "/usage",
    "/teaching",
    "/ainspire",
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

const SESSION_COOKIE_NAME = "crebit_session";

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

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
        "/settings/:path*",
        "/billing/:path*",
        "/usage/:path*",
        "/teaching/:path*",
        "/ainspire/:path*",
    ],
};
