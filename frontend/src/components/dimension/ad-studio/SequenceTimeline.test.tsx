import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@/test/test-utils";
import SequenceTimeline from "./SequenceTimeline";
import type { SceneAnalysisResult, EmotionalBeat } from "../ADStudioPanel";

function createScene(sceneNumber: number): SceneAnalysisResult {
  return {
    scene_number: sceneNumber,
    description: `Scene ${sceneNumber}`,
    techniques: {
      composition: [],
      camera_movement: [],
      camera_angle: [],
      lighting: [],
      color: [],
    },
    sequence_context: {
      emotional_position: "도입",
      camera_distance_flow: "MS -> CU",
    },
    prompts: {
      kling_3_0: "",
      seedance_2_0: "",
      veo_3_1: "",
    },
  };
}

describe("SequenceTimeline", () => {
  it("shows continuity score badge when provided", () => {
    const scenes = [createScene(1), createScene(2)];
    const emotionalArc: EmotionalBeat[] = [
      { scene_number: 1, emotion: "불안", intensity: 0.4, description: "도입" },
      { scene_number: 2, emotion: "긴장", intensity: 0.8, description: "상승" },
    ];

    render(
      <SequenceTimeline
        scenes={scenes}
        emotionalArc={emotionalArc}
        continuityScore={0.84}
        onSceneClick={vi.fn()}
      />,
    );

    expect(screen.getByText("연속성 점수 84%")).toBeInTheDocument();
  });

  it("hides continuity score badge when score is not provided", () => {
    const scenes = [createScene(1)];
    const emotionalArc: EmotionalBeat[] = [
      { scene_number: 1, emotion: "평온", intensity: 0.3, description: "시작" },
    ];

    render(
      <SequenceTimeline
        scenes={scenes}
        emotionalArc={emotionalArc}
        onSceneClick={vi.fn()}
      />,
    );

    expect(screen.queryByText(/연속성 점수/)).not.toBeInTheDocument();
  });

  it("uses score band color classes for continuity badge", () => {
    const scenes = [createScene(1), createScene(2)];
    const emotionalArc: EmotionalBeat[] = [
      { scene_number: 1, emotion: "불안", intensity: 0.4, description: "도입" },
      { scene_number: 2, emotion: "긴장", intensity: 0.8, description: "상승" },
    ];

    const { rerender } = render(
      <SequenceTimeline
        scenes={scenes}
        emotionalArc={emotionalArc}
        continuityScore={0.85}
        onSceneClick={vi.fn()}
      />,
    );
    expect(screen.getByText("연속성 점수 85%")).toHaveClass("text-emerald-500");

    rerender(
      <SequenceTimeline
        scenes={scenes}
        emotionalArc={emotionalArc}
        continuityScore={0.65}
        onSceneClick={vi.fn()}
      />,
    );
    expect(screen.getByText("연속성 점수 65%")).toHaveClass("text-amber-500");

    rerender(
      <SequenceTimeline
        scenes={scenes}
        emotionalArc={emotionalArc}
        continuityScore={0.45}
        onSceneClick={vi.fn()}
      />,
    );
    expect(screen.getByText("연속성 점수 45%")).toHaveClass("text-rose-500");
  });
});
