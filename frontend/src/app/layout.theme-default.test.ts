import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const layoutPath = path.join(process.cwd(), "src/app/layout.tsx");
const layout = readFileSync(layoutPath, "utf8");

describe("root layout theme defaults", () => {
  it("uses light as the default theme", () => {
    expect(layout).toContain('defaultTheme="light"');
  });
});
