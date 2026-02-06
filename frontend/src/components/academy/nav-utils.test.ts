import { describe, expect, it } from "vitest";
import {
  extractAcademyTabFromHref,
  isAcademyTabActive,
} from "./nav-utils";

describe("academy nav utils", () => {
  it("extracts tab query param", () => {
    expect(extractAcademyTabFromHref("/?tab=upload")).toBe("upload");
    expect(extractAcademyTabFromHref("/?tab=admin")).toBe("admin");
  });

  it("falls back to home tab", () => {
    expect(extractAcademyTabFromHref("/")).toBe("home");
    expect(extractAcademyTabFromHref("not-a-valid-url")).toBe("home");
  });

  it("computes active state from href", () => {
    expect(isAcademyTabActive("upload", "/?tab=upload")).toBe(true);
    expect(isAcademyTabActive("home", "/")).toBe(true);
    expect(isAcademyTabActive("tools", "/?tab=parse")).toBe(false);
  });
});
