import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const mdInputPath = path.join(
  process.cwd(),
  "src/app/academy/components/parse/MDInput.tsx",
);
const parseContentPath = path.join(
  process.cwd(),
  "src/app/academy/components/parse/ParseContent.tsx",
);

const mdInputSource = readFileSync(mdInputPath, "utf8");
const parseContentSource = readFileSync(parseContentPath, "utf8");

describe("academy parse copy", () => {
  it("mentions paste or drag-and-drop in MD input placeholder", () => {
    expect(mdInputSource).toContain(
      'placeholder="MD 붙여넣기 또는 드래그 앤 드롭"',
    );
  });

  it("avoids duplicate helper copy outside the input area", () => {
    expect(parseContentSource).not.toContain(
      "MD를 붙여넣거나 드래그 앤 드롭하면 파싱 결과가 여기에 표시됩니다.",
    );
    expect(parseContentSource).toContain('sub="파싱 결과 복사"');
  });
});
