import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ToolPromptTabs } from "./ToolPromptTabs";

describe("ToolPromptTabs", () => {
  const mockPrompts = {
    nanobanana: "Test prompt for NanoBanana",
    midjourney: "Test prompt for Midjourney --ar 16:9 --v 7",
    kling: "Test prompt for Kling video",
    veo: "Test prompt for Veo video",
  };

  const defaultProps = {
    prompts: mockPrompts,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all tool tabs", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    // Check tabs by their icon - there may be multiple due to content area
    expect(screen.getAllByText("NB").length).toBeGreaterThan(0);
    expect(screen.getAllByText("MJ").length).toBeGreaterThan(0);
    expect(screen.getAllByText("KL").length).toBeGreaterThan(0);
    expect(screen.getAllByText("VE").length).toBeGreaterThan(0);
  });

  it("shows first tool (nanobanana) content by default", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getByText("Test prompt for NanoBanana")).toBeInTheDocument();
  });

  it("switches content on tab click", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    // Click MJ tab by finding the first icon (in the tab bar)
    const mjIcons = screen.getAllByText("MJ");
    const mjTab = mjIcons[0].closest("button");
    fireEvent.click(mjTab!);
    expect(screen.getByText(/Test prompt for Midjourney/)).toBeInTheDocument();
  });

  it("shows recommended badge for default tool", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getByText("Recommended")).toBeInTheDocument();
  });

  it("shows recommended badge for specified tool", () => {
    render(<ToolPromptTabs {...defaultProps} recommendedTool="midjourney" />);
    // MJ tab should have the recommended badge
    const mjIcons = screen.getAllByText("MJ");
    const mjTab = mjIcons[0].closest("button");
    expect(mjTab?.textContent).toContain("Recommended");
  });

  it("calls onCopy when copy button clicked", async () => {
    const onCopy = vi.fn();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText },
    });

    render(<ToolPromptTabs {...defaultProps} onCopy={onCopy} />);
    fireEvent.click(screen.getByText(/클립보드에 복사/));

    await waitFor(() => {
      expect(onCopy).toHaveBeenCalledWith("nanobanana");
    });
  });

  it("shows tool format info", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getByText(/Format: Korean/)).toBeInTheDocument();
  });

  it("shows English format for Midjourney", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    const mjIcons = screen.getAllByText("MJ");
    fireEvent.click(mjIcons[0].closest("button")!);
    expect(screen.getByText(/Format: English \+ Parameters/)).toBeInTheDocument();
  });

  it("shows tool tips section", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getByText("NanoBanana Pro Tips:")).toBeInTheDocument();
  });

  it("shows parameter guide section", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getByText("Parameters")).toBeInTheDocument();
  });

  it("shows critical parameter with red styling", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    const noParams = screen.getAllByText("--no");
    // First one should be in the parameter guide
    expect(noParams[0]).toHaveClass("bg-red-500/10");
  });

  it("shows common issues section", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getByText("Common Issues")).toBeInTheDocument();
  });

  it("shows empty state when no prompt for tool", () => {
    render(<ToolPromptTabs prompts={{}} />);
    expect(screen.getByText(/No prompt available/)).toBeInTheDocument();
  });

  it("renders external tool link", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    const openLink = screen.getByText(/Open NanoBanana/);
    expect(openLink).toHaveAttribute("href", "https://nanobanana.ai");
  });

  it("switches to Kling and shows video tips", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    const klIcons = screen.getAllByText("KL");
    fireEvent.click(klIcons[0].closest("button")!);
    expect(screen.getByText(/Test prompt for Kling video/)).toBeInTheDocument();
    expect(screen.getByText(/Kling 2.6 Tips:/)).toBeInTheDocument();
  });

  it("switches to Veo and shows video tips", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    const veIcons = screen.getAllByText("VE");
    fireEvent.click(veIcons[0].closest("button")!);
    expect(screen.getByText(/Test prompt for Veo video/)).toBeInTheDocument();
    expect(screen.getByText(/Veo 3.1 Tips:/)).toBeInTheDocument();
  });

  it("shows tool icon", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    expect(screen.getAllByText("NB").length).toBeGreaterThan(0);
    expect(screen.getAllByText("MJ").length).toBeGreaterThan(0);
    expect(screen.getAllByText("KL").length).toBeGreaterThan(0);
    expect(screen.getAllByText("VE").length).toBeGreaterThan(0);
  });

  it("highlights active tab", () => {
    render(<ToolPromptTabs {...defaultProps} />);
    const nbIcons = screen.getAllByText("NB");
    const nbTab = nbIcons[0].closest("button");
    expect(nbTab).toHaveClass("bg-card");
  });
});
