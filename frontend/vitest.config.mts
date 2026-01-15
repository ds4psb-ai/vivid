import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [tsconfigPaths(), react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    exclude: [
      "node_modules",
      "src/app/_deprecated/**",
      "src/components/_deprecated/**",
      "src/hooks/_deprecated/**",
      "src/lib/_deprecated/**",
      "e2e/**",
    ],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.{test,spec}.{ts,tsx}",
        "src/test/**",
        "src/**/_deprecated/**",
        "src/types/**",
      ],
    },
    testTimeout: 10000,
    hookTimeout: 10000,
    server: {
      deps: {
        inline: ["zod"],
      },
    },
  },
});
