import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

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
              : "default-src 'self'; script-src 'self' 'unsafe-inline' https://vercel.live https://*.sentry.io; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' data: https: blob:; media-src 'self' https: blob:; connect-src 'self' https: wss://vercel.live https://*.ingest.sentry.io; font-src 'self' data: https://fonts.gstatic.com; frame-src 'self' https://vercel.live; frame-ancestors 'none'; upgrade-insecure-requests;",
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
    // Phase 5: Legacy dimension routes → Mega App redirects
    // Preserves backward compatibility while directing users to unified experience
    return [
      // ===== DNA Lab redirects =====
      {
        source: "/dimension/aesthetic",
        destination: "/dna-lab?step=ad",
        permanent: false, // 307 - allows changing later
      },
      {
        source: "/dimension/abyss",
        destination: "/dna-lab?step=mirror",
        permanent: false,
      },
      {
        source: "/dimension/quality-check",
        destination: "/dna-lab?step=qc",
        permanent: false,
      },
      {
        source: "/dimension/reference-decoder",
        destination: "/dna-lab?step=vpe",
        permanent: false,
      },

      // ===== Story Engine redirects =====
      {
        source: "/dimension/story-architect",
        destination: "/story-engine?step=story",
        permanent: false,
      },
      {
        source: "/dimension/prompt",
        destination: "/story-engine?step=prompt",
        permanent: false,
      },

      // ===== Production Bridge redirects =====
      {
        source: "/dimension/video-maker",
        destination: "/production?step=veo",
        permanent: false,
      },
      {
        source: "/dimension/kling",
        destination: "/production?step=kling",
        permanent: false,
      },
      {
        source: "/dimension/suno",
        destination: "/production?step=suno",
        permanent: false,
      },

      // ===== Future: Additional redirects =====
      // Uncomment when these are integrated into mega apps:
      // { source: "/dimension/storyboard", destination: "/story-engine?step=storyboard", permanent: false },
      // { source: "/dimension/visual-realizer", destination: "/production?step=visual", permanent: false },
      // { source: "/dimension/sound-crafter", destination: "/production?step=sound", permanent: false },
    ];
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

// Wrap with Sentry configuration
export default withSentryConfig(nextConfig, {
  // For all available options, see:
  // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,

  // Only print logs in CI
  silent: !process.env.CI,

  // Upload source maps for better error stack traces
  // Requires SENTRY_AUTH_TOKEN environment variable
  sourcemaps: {
    deleteSourcemapsAfterUpload: true,
  },

  // Disable Sentry telemetry
  telemetry: false,

  // Automatically tree-shake Sentry logger statements
  widenClientFileUpload: true,

  // Route browser requests to Sentry through a Next.js rewrite to avoid ad-blockers
  tunnelRoute: "/monitoring",
});
