import type { NextConfig } from "next";

const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

const nextConfig: NextConfig = {
  // React Compiler - 2026 Best Practice for automatic memoization
  // Requires babel-plugin-react-compiler (installed)
  compiler: {
    // Note: React Compiler is automatically enabled in Next.js 16 with React 19
  },
  // Cache Components (formerly PPR) - disabled for now due to Suspense boundary requirements
  // Enable incrementally per-route once all pages are updated
  // cacheComponents: true,
  experimental: {
    // React 19 View Transitions API
    viewTransition: true,
  },
  async headers() {
    // Security headers based on OWASP and Next.js best practices
    // https://nextjs.org/docs/app/api-reference/config/next-config-js/headers
    const isDev = process.env.NODE_ENV === "development";

    return [
      {
        source: "/:path*",
        headers: [
          // Content Security Policy
          // Development: more permissive for HMR
          // Production: strict policy
          {
            key: "Content-Security-Policy",
            value: isDev
              ? "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; connect-src 'self' ws: wss: http: https:; font-src 'self' data:; frame-ancestors 'none';"
              : "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: blob:; connect-src 'self' https:; font-src 'self' data:; frame-ancestors 'none'; upgrade-insecure-requests;",
          },
          // HSTS - enforce HTTPS (production only effective)
          {
            key: "Strict-Transport-Security",
            value: "max-age=31536000; includeSubDomains; preload",
          },
          // Prevent clickjacking
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          // Prevent MIME type sniffing
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          // Control referrer information
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          // Restrict browser features
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=(), interest-cohort=()",
          },
        ],
      },
    ];
  },
  async redirects() {
    // Removed: / -> /dimension redirect (unified home now handles this)
    return [];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
  outputFileTracingIncludes: {
    "/*": ["./secure-assets/**"],
  },
};

export default nextConfig;
