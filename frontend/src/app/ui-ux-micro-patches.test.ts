import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const appDir = path.join(process.cwd(), "src/app");
const componentsDir = path.join(process.cwd(), "src/components");

const sheet = readFileSync(path.join(componentsDir, "ui/sheet.tsx"), "utf8");
const versionsModal = readFileSync(path.join(appDir, "_components/VersionsModal.tsx"), "utf8");
const toolDetailPage = readFileSync(path.join(appDir, "tools/[toolKey]/page.tsx"), "utf8");
const forkPage = readFileSync(path.join(appDir, "tools/[toolKey]/fork/page.tsx"), "utf8");
const loginRequiredModal = readFileSync(path.join(componentsDir, "LoginRequiredModal.tsx"), "utf8");
const workflowPreviewModal = readFileSync(path.join(componentsDir, "WorkflowPreviewModal.tsx"), "utf8");
const unifiedChainSidebar = readFileSync(path.join(componentsDir, "workflow/UnifiedChainSidebar.tsx"), "utf8");
const dnaLabChainSummary = readFileSync(path.join(componentsDir, "dna-lab/DNALabChainSummary.tsx"), "utf8");
const quickGenerateButton = readFileSync(path.join(componentsDir, "workflow/QuickGenerateButton.tsx"), "utf8");
const conflictResolutionModal = readFileSync(path.join(componentsDir, "workflow/ConflictResolutionModal.tsx"), "utf8");
const sandboxPage = readFileSync(path.join(appDir, "sandbox/[appId]/page.tsx"), "utf8");
const ipCatalogClient = readFileSync(path.join(appDir, "ip/_components/IPCatalogClient.tsx"), "utf8");
const termsPage = readFileSync(path.join(appDir, "terms/page.tsx"), "utf8");
const crebitTermsPage = readFileSync(path.join(appDir, "crebit/terms/page.tsx"), "utf8");
const sectionHeader = readFileSync(path.join(appDir, "crebit/_components/SectionHeader.tsx"), "utf8");
const pipelineNode = readFileSync(path.join(appDir, "crebit/_components/PipelineNode.tsx"), "utf8");
const statItem = readFileSync(path.join(appDir, "crebit/_components/StatItem.tsx"), "utf8");
const unifiedStepNav = readFileSync(path.join(componentsDir, "workflow/UnifiedStepNav.tsx"), "utf8");
const dnaLabStepNav = readFileSync(path.join(componentsDir, "dna-lab/DNALabStepNav.tsx"), "utf8");
const crebitNavbar = readFileSync(path.join(componentsDir, "home/CrebitNavbar.tsx"), "utf8");
const loginPage = readFileSync(path.join(appDir, "login/page.tsx"), "utf8");
const studioPage = readFileSync(path.join(appDir, "studio/page.tsx"), "utf8");
const studioIntentInput = readFileSync(path.join(componentsDir, "home/StudioIntentInput.tsx"), "utf8");
const studioQuickStart = readFileSync(path.join(componentsDir, "home/StudioQuickStart.tsx"), "utf8");


describe("ui ux micro patches", () => {
  it("ensures sheet buttons are explicit non-submit buttons", () => {
    const typedButtonMatches =
      sheet.match(/<button type=\"button\" onClick=\{handleClick\} \{\.\.\.props\}>/g) ?? [];
    expect(typedButtonMatches.length).toBeGreaterThanOrEqual(2);
  });

  it("adds accessible labels to icon-only close/copy controls", () => {
    expect(versionsModal).toContain('aria-label="버전 히스토리 닫기"');
    expect(toolDetailPage).toContain('aria-label={labels.copyToolKey}');
    expect(forkPage).toContain('aria-label="에러 배너 닫기"');
    expect(loginRequiredModal).toContain('aria-label={t("close") || "Close"}');
    expect(workflowPreviewModal).toContain('aria-label={ko ? "추천 워크플로우 닫기" : "Close recommended workflow"}');
    expect(unifiedChainSidebar).toContain('aria-label="체인 데이터 닫기"');
    expect(unifiedChainSidebar).toContain('aria-label="단계 편집"');
    expect(dnaLabChainSummary).toContain('aria-label="체인 데이터 닫기"');
    expect(quickGenerateButton).toContain('aria-label="퀵 생성 모달 닫기"');
    expect(conflictResolutionModal).toContain('aria-label="충돌 해결 모달 닫기"');
  });

  it("replaces full reload recovery with local retry patterns", () => {
    expect(sandboxPage).not.toContain("window.location.reload()");
    expect(ipCatalogClient).not.toContain("window.location.reload()");
    expect(sandboxPage).toContain("router.refresh()");
    expect(ipCatalogClient).toContain("onClick={fetchCatalog}");
  });

  it("removes legacy hard-coded crebit palette entries from terms and hero components", () => {
    expect(termsPage).not.toContain("#FF0045");
    expect(termsPage).not.toContain("#0F0F1A");
    expect(crebitTermsPage).not.toContain("#FF0045");
    expect(crebitTermsPage).not.toContain("#0F0F1A");
    expect(sectionHeader).not.toContain("#4200FF");
    expect(pipelineNode).not.toContain("#4200FF");
    expect(statItem).not.toContain("#FF0045");
  });

  it("increases compact workflow nav touch targets to 44px", () => {
    expect(unifiedStepNav).toContain('"h-11 w-11 rounded-lg transition-colors"');
    expect(dnaLabStepNav).toContain('"h-11 w-11 rounded-lg transition-colors"');
  });

  it("adds visible mobile menu labels and stronger touch target affordance", () => {
    expect(crebitNavbar).toContain("aria-label=\"메뉴 열기\"");
    expect(crebitNavbar).toContain("inline-flex items-center gap-1.5");
    expect(crebitNavbar).toContain(">메뉴<");
  });

  it("adds login-context guidance for first-time users", () => {
    expect(loginPage).toContain("로그인 후 바로 할 수 있는 작업");
    expect(loginPage).toContain("워크플로우 시작");
    expect(loginPage).toContain("크레딧/상태 확인");
  });

  it("adds explicit quick-start block to studio entry", () => {
    expect(studioPage).toContain("StudioQuickStart");
  });

  it("adds intent input bar to studio entry with explicit CTA", () => {
    expect(studioPage).toContain("StudioIntentInput");
    expect(studioIntentInput).toContain("무엇을 만들고 싶나요?");
    expect(studioIntentInput).toContain("DNA Lab에서 시작");
    expect(studioIntentInput).toContain("Enter로 실행");
    expect(studioIntentInput).toContain("Shift + Enter");
    expect(studioIntentInput).toContain("Story Engine");
  });

  it("adds animated border-beam style frame to studio intent input", () => {
    expect(studioIntentInput).toContain("animate-gradient-x");
    expect(studioIntentInput).toContain("bg-gradient-to-r");
    expect(studioIntentInput).toContain("rounded-[20px]");
    expect(studioIntentInput).toContain("isSubmitting");
    expect(studioIntentInput).toContain("이동 중...");
  });

  it("switches studio intent CTA copy based on target destination", () => {
    expect(studioIntentInput).toContain("Flow에서 시작");
    expect(studioIntentInput).toContain("Story Engine에서 시작");
    expect(studioIntentInput).toContain("buttonLabel");
  });

  it("uses Mobbin-style primary and secondary CTA hierarchy in quick-start", () => {
    expect(studioQuickStart).toContain("지금 바로 시작");
    expect(studioQuickStart).toContain("워크플로우 둘러보기");
    expect(studioQuickStart).toContain("Primary CTA");
    expect(studioQuickStart).toContain("Secondary CTA");
  });

  it("migrates navbar logos to next/image for better LCP handling", () => {
    expect(crebitNavbar).toContain("import Image from \"next/image\"");
    expect(crebitNavbar).not.toContain("<img");
  });
});
