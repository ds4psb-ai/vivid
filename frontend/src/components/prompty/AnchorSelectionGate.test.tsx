import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AnchorSelectionGate } from "./AnchorSelectionGate";

describe("AnchorSelectionGate", () => {
  const mockScenes = [
    { id: "scene_1", name: "Scene 1", shotType: "Full shot" },
    { id: "scene_2", name: "Scene 2", shotType: "Close-up" },
    { id: "scene_3", name: "Scene 3", shotType: "Medium shot" },
  ];

  const defaultProps = {
    scenes: mockScenes,
    onSelect: vi.fn(),
    onConfirm: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all scenes", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.getByText("Scene 1")).toBeInTheDocument();
    expect(screen.getByText("Scene 2")).toBeInTheDocument();
    expect(screen.getByText("Scene 3")).toBeInTheDocument();
  });

  it("renders header and description", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.getByText("ANCHOR Selection")).toBeInTheDocument();
    expect(screen.getByText(/Select a reference scene/)).toBeInTheDocument();
  });

  it("shows shot type for each scene", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.getByText("Full shot")).toBeInTheDocument();
    expect(screen.getByText("Close-up")).toBeInTheDocument();
    expect(screen.getByText("Medium shot")).toBeInTheDocument();
  });

  it("shows available scenes count", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.getByText(/Available Scenes \(3\)/)).toBeInTheDocument();
  });

  it("highlights selected scene", () => {
    render(<AnchorSelectionGate {...defaultProps} selectedAnchorId="scene_1" />);
    expect(screen.getByText("Scene 1 selected as ANCHOR")).toBeInTheDocument();
  });

  it("calls onSelect with scene id on click", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    fireEvent.click(screen.getByText("Scene 2"));
    expect(defaultProps.onSelect).toHaveBeenCalledWith("scene_2");
  });

  it("does not show confirm button when no scene selected", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();
  });

  it("shows confirm button when scene selected", () => {
    render(<AnchorSelectionGate {...defaultProps} selectedAnchorId="scene_1" />);
    expect(screen.getByText("Confirm")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button clicked", () => {
    render(<AnchorSelectionGate {...defaultProps} selectedAnchorId="scene_1" />);
    fireEvent.click(screen.getByText("Confirm"));
    expect(defaultProps.onConfirm).toHaveBeenCalled();
  });

  it("shows empty state when no scenes", () => {
    render(<AnchorSelectionGate {...defaultProps} scenes={[]} />);
    expect(screen.getByText("No scenes available.")).toBeInTheDocument();
  });

  it("shows ANCHOR explanation", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.getByText("What is ANCHOR?")).toBeInTheDocument();
    expect(screen.getByText(/reference scene used to maintain character consistency/)).toBeInTheDocument();
  });

  it("shows tip about face clarity", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    expect(screen.getByText(/Select a scene with the clearest face shot/)).toBeInTheDocument();
  });

  it("renders without onConfirm prop", () => {
    const { onConfirm, ...propsWithoutConfirm } = defaultProps;
    render(<AnchorSelectionGate {...propsWithoutConfirm} selectedAnchorId="scene_1" />);
    // Should render without error, no confirm button
    expect(screen.queryByText("Confirm")).not.toBeInTheDocument();
  });

  it("handles scene with thumbnail", () => {
    const scenesWithThumbnail = [
      { id: "scene_1", name: "Scene 1", thumbnail: "/test.jpg" },
    ];
    render(<AnchorSelectionGate {...defaultProps} scenes={scenesWithThumbnail} />);
    const img = screen.getByRole("img", { name: "Scene 1" });
    expect(img).toHaveAttribute("src", "/test.jpg");
  });

  it("shows fallback letter when no thumbnail", () => {
    render(<AnchorSelectionGate {...defaultProps} />);
    // Scene 1 should show "S" as fallback
    expect(screen.getAllByText("S").length).toBeGreaterThan(0);
  });
});
