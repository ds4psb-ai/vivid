import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TikitakaWorkflow } from "./TikitakaWorkflow";

// Mock API
vi.mock("@/lib/api", () => ({
  api: {
    advancePromptyTikitaka: vi.fn(),
    gotoPromptyTikitakaStep: vi.fn(),
    logPromptyAction: vi.fn(),
  },
}));

describe("TikitakaWorkflow", () => {
  const defaultProps = {
    projectId: "test-project-123",
    initialStep: 1,
    onStepChange: vi.fn(),
    onComplete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders step 1 by default", () => {
    render(<TikitakaWorkflow {...defaultProps} />);
    // Success Brief appears in both header and progress - use getAllByText
    expect(screen.getAllByText("Success Brief").length).toBeGreaterThan(0);
    expect(screen.getByText("1/6")).toBeInTheDocument();
  });

  it("shows Gemini badge for step 1", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={1} />);
    // Role badge shows "G Gemini"
    expect(screen.getByText(/G Gemini/)).toBeInTheDocument();
  });

  it("shows Claude badge for step 2", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={2} />);
    // Role badge shows "C Claude"
    expect(screen.getByText(/C Claude/)).toBeInTheDocument();
  });

  it("shows Gemini badge for step 3", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={3} />);
    // Role badge shows "G Gemini"
    expect(screen.getByText(/G Gemini/)).toBeInTheDocument();
  });

  it("shows Claude badge for step 4", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={4} />);
    // Role badge shows "C Claude"
    expect(screen.getByText(/C Claude/)).toBeInTheDocument();
  });

  it("shows User badge for step 5", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={5} />);
    // Role badge shows "U You"
    expect(screen.getByText(/U You/)).toBeInTheDocument();
  });

  it("shows User badge for step 6", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={6} />);
    // Role badge shows "U You"
    expect(screen.getByText(/U You/)).toBeInTheDocument();
  });

  it("advances to next step on button click", async () => {
    const { api } = await import("@/lib/api");
    (api.advancePromptyTikitaka as ReturnType<typeof vi.fn>).mockResolvedValue({ new_step: 2 });

    render(<TikitakaWorkflow {...defaultProps} />);

    // Check all required attachments first
    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach(cb => fireEvent.click(cb));

    // Click next step
    fireEvent.click(screen.getByText("Next Step"));

    await waitFor(() => {
      expect(api.advancePromptyTikitaka).toHaveBeenCalledWith(
        "test-project-123",
        expect.any(Object)
      );
    });
  });

  it("copies prompt to clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });

    render(<TikitakaWorkflow {...defaultProps} />);

    const copyButton = screen.getByText(/클립보드에 복사/);
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(writeText).toHaveBeenCalled();
    });
  });

  it("displays step progress navigation", () => {
    render(<TikitakaWorkflow {...defaultProps} />);

    // Step names should be present (may have multiple due to header + progress)
    expect(screen.getAllByText("Success Brief").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Draft").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Critique").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Revise").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Generate + Review").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Micro-adjust").length).toBeGreaterThan(0);
  });

  it("shows attachments checklist", () => {
    render(<TikitakaWorkflow {...defaultProps} />);
    expect(screen.getByText("필수 첨부")).toBeInTheDocument();
    expect(screen.getByText("원본 영상")).toBeInTheDocument();
  });

  it("shows tips section", () => {
    render(<TikitakaWorkflow {...defaultProps} />);
    expect(screen.getByText("Tips")).toBeInTheDocument();
  });

  it("shows verdict actions on step 5", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={5} />);
    expect(screen.getByText("Verdict Actions")).toBeInTheDocument();
    // REJECT and PASS appear in both steps context and verdict buttons
    expect(screen.getByText("REJECT - Step 2")).toBeInTheDocument();
    expect(screen.getByText("PASS - 85+")).toBeInTheDocument();
  });

  it("shows verdict actions on step 6", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={6} />);
    expect(screen.getByText("Verdict Actions")).toBeInTheDocument();
    expect(screen.getByText("Retry Step 5")).toBeInTheDocument();
  });

  it("handles goto step", async () => {
    const { api } = await import("@/lib/api");
    (api.gotoPromptyTikitakaStep as ReturnType<typeof vi.fn>).mockResolvedValue({});

    render(<TikitakaWorkflow {...defaultProps} initialStep={5} />);

    // Click REJECT button (goes to step 2)
    fireEvent.click(screen.getByText("REJECT - Step 2"));

    await waitFor(() => {
      expect(api.gotoPromptyTikitakaStep).toHaveBeenCalledWith(
        "test-project-123",
        2,
        "REJECT"
      );
    });
  });

  it("disables next button when required attachments unchecked", () => {
    render(<TikitakaWorkflow {...defaultProps} />);

    const nextButton = screen.getByText("Next Step");
    expect(nextButton).toBeDisabled();
  });

  it("enables next button when all required attachments checked", () => {
    render(<TikitakaWorkflow {...defaultProps} />);

    // Check all checkboxes
    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach(cb => fireEvent.click(cb));

    const nextButton = screen.getByText("Next Step");
    expect(nextButton).not.toBeDisabled();
  });

  it("shows error state for invalid step", () => {
    render(<TikitakaWorkflow {...defaultProps} initialStep={99} />);
    expect(screen.getByText(/Invalid step/)).toBeInTheDocument();
  });

  it("calls onComplete when workflow finishes", async () => {
    const { api } = await import("@/lib/api");
    (api.advancePromptyTikitaka as ReturnType<typeof vi.fn>).mockResolvedValue({ completed: true });

    render(<TikitakaWorkflow {...defaultProps} initialStep={6} />);

    // Check all required attachments
    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach(cb => fireEvent.click(cb));

    fireEvent.click(screen.getByText("Complete"));

    await waitFor(() => {
      expect(defaultProps.onComplete).toHaveBeenCalled();
    });
  });
});
