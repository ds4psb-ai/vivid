import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const appDir = path.join(process.cwd(), "src/app");
const componentsDir = path.join(process.cwd(), "src/components");
const stylesDir = path.join(process.cwd(), "src/styles");

const globalsCss = readFileSync(path.join(appDir, "globals.css"), "utf8");
const layout = readFileSync(path.join(appDir, "layout.tsx"), "utf8");
const dnaLabPage = readFileSync(path.join(appDir, "dna-lab/page.tsx"), "utf8");
const storyEnginePage = readFileSync(path.join(appDir, "story-engine/page.tsx"), "utf8");
const productionPage = readFileSync(path.join(appDir, "production/page.tsx"), "utf8");
const academyHome = readFileSync(path.join(appDir, "academy/components/HomeContent.tsx"), "utf8");
const unifiedWorkflowShell = readFileSync(
  path.join(componentsDir, "workflow/UnifiedWorkflowShell.tsx"),
  "utf8",
);
const dnaLabWorkflowShell = readFileSync(
  path.join(componentsDir, "dna-lab/DNALabWorkflowShell.tsx"),
  "utf8",
);
const dnaLabOnboarding = readFileSync(
  path.join(componentsDir, "dna-lab/DNALabOnboarding.tsx"),
  "utf8",
);
const dnaLabOverview = readFileSync(
  path.join(componentsDir, "workflow/DNALabOverview.tsx"),
  "utf8",
);
const megaAppConstants = readFileSync(
  path.join(componentsDir, "mega-app/constants.ts"),
  "utf8",
);
const baseTokens = readFileSync(path.join(stylesDir, "tokens/tokens.base.css"), "utf8");
const semanticTokens = readFileSync(path.join(stylesDir, "tokens/tokens.semantic.css"), "utf8");

describe("theme palette refresh", () => {
  it("uses warm neutral brand tokens instead of neon-red defaults", () => {
    expect(globalsCss).toContain("--color-brand-primary: #C7873A;");
    expect(globalsCss).toContain("--color-brand-secondary: #A66A2D;");
    expect(globalsCss).toContain("--color-brand-accent: #D7A15F;");
    expect(globalsCss).not.toContain("--stitch-primary: #FF003C;");
  });

  it("raises stitch dark surfaces from ultra-black to charcoal", () => {
    expect(globalsCss).toContain("--stitch-bg-dark: #121316;");
    expect(globalsCss).toContain("--stitch-card-dark: #1A1C21;");
    expect(globalsCss).toContain("--stitch-surface-dark: #1F2228;");
  });

  it("syncs browser theme-color meta with the new accent", () => {
    expect(layout).toContain('<meta name="theme-color" content="#c7873a" />');
  });

  it("uses stitch background classes in key full-screen shells", () => {
    expect(dnaLabPage).toContain("bg-stitch-dark");
    expect(storyEnginePage).toContain("bg-stitch-dark");
    expect(productionPage).toContain("bg-stitch-dark");
    expect(unifiedWorkflowShell).toContain("bg-stitch-dark");
    expect(dnaLabWorkflowShell).toContain("bg-stitch-dark");
    expect(dnaLabOnboarding).toContain("bg-stitch-dark");
  });

  it("removes hardcoded neon-red literals from shared style layers", () => {
    expect(globalsCss).not.toContain("rgba(255, 0, 60");
    expect(baseTokens).toContain("--red-500: oklch(62% 0.18 65);");
    expect(baseTokens).not.toContain("--red-500: oklch(62% 0.28 20);");
    expect(semanticTokens).not.toContain("oklch(62% 0.28 20 / 0.3)");
    expect(megaAppConstants).toContain("hue: 65");
    expect(megaAppConstants).toContain("oklch(0.62 0.18 65 / 0.3)");
    expect(academyHome).not.toContain("rgba(255,0,60");
    expect(dnaLabOverview).not.toContain("rgba(255,0,60");
  });
});
