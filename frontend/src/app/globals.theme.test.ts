import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const cssPath = path.join(process.cwd(), "src/app/globals.css");
const css = readFileSync(cssPath, "utf8");

describe("global theme css", () => {
  it("defines required surface and border aliases", () => {
    expect(css).toContain("--surface-3:");
    expect(css).toContain("--border: var(--border-muted);");
  });

  it("does not include broad light-mode force override selectors", () => {
    expect(css).not.toContain(':root:not(.dark) [class*="text-white"]');
    expect(css).not.toContain(':root:not(.dark) [class*="bg-white/5"]');
  });
});
