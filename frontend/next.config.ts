import type { NextConfig } from "next";

const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

const nextConfig: NextConfig = {
  // External image domains for demo
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "picsum.photos",
      },
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
    ],
  },
  // React Compiler - 2026 Best Practice for automatic memoization
  // Requires babel-plugin-react-compiler (installed)
  compiler: {
    // Note: React Compiler is automatically enabled in Next.js 16 with React 19
  },
  // Phase 6: Cache Components (formerly PPR)
  // Enable for "use cache" directive support
  // Note: Requires Suspense boundaries around dynamic content
  // TEMPORARILY DISABLED: Other pages (e.g., /humancloud/requests/[id]) need
  // Suspense boundaries first. Enable incrementally once all pages are validated.
  // cacheComponents: true,
  experimental: {
    // React 19 View Transitions API
    viewTransition: true,
    // Phase 6: Enable dynamicIO for explicit caching control
    // When enabled, all data fetching is dynamic by default
    // Use "use cache" to opt specific functions/components into caching
    // dynamicIO: true,  // Enable in Phase 6.1 after ISR validation
  },
  // Phase 6: Custom cache life profiles for IP-First UX
  // These profiles can be referenced with cacheLife('profile-name')
  cacheLife: {
    // IP metadata (1 hour stale, 15 minutes revalidate, 1 day expire)
    // Use for: IP catalog, IP details, presets
    ip: {
      stale: 3600, // 1 hour - client can show stale data
      revalidate: 900, // 15 minutes - server revalidates in background
      expire: 86400, // 1 day - hard expiration
    },
    // Editorial content (long-lived, slow-changing)
    // Use for: Genre lists, static content, help pages
    editorial: {
      stale: 86400, // 1 day
      revalidate: 3600, // 1 hour
      expire: 604800, // 1 week
    },
    // Real-time data (short-lived, frequently updated)
    // Use for: User activity, live stats, notifications
    realtime: {
      stale: 60, // 1 minute
      revalidate: 30, // 30 seconds
      expire: 300, // 5 minutes
    },
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
              ? "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: blob:; media-src 'self' https: blob:; connect-src 'self' ws: wss: http: https:; font-src 'self' data: https://fonts.gstatic.com; frame-src 'self'; frame-ancestors 'none';"
              : "default-src 'self'; script-src 'self' 'unsafe-inline' https://vercel.live; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: blob:; media-src 'self' https: blob:; connect-src 'self' https: wss://vercel.live; font-src 'self' data: https://fonts.gstatic.com; frame-src 'self' https://vercel.live; frame-ancestors 'none'; upgrade-insecure-requests;",
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
