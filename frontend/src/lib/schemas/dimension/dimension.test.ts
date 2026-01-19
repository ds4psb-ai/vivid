/**
 * Dimension Schema Tests
 *
 * Phase -1: F2 API Contract Implementation
 */
import { describe, test, expect } from "vitest";

// 1D
import {
  Generate1DRequestSchema,
  Generate1DResponseSchema,
  type Generate1DRequest,
} from "./1d.schema";

// 2D
import {
  Create2DRequestSchema,
  type Create2DRequest,
} from "./2d.schema";

// 3D
import {
  Generate3DRequestSchema,
  type Generate3DRequest,
} from "./3d.schema";

// 4D
import {
  Analyze4DRequestSchema,
} from "./4d.schema";

// VEO
import {
  GenerateVeoRequestSchema,
  GenerateVeoResponseSchema,
} from "./veo.schema";

// Quality
import {
  QualityCheckRequestSchema,
  CreativeEditorRequestSchema,
  QualityCheckResponseSchema,
} from "./quality.schema";

describe("1D - Prompt Generator Schema", () => {
  describe("Generate1DRequestSchema", () => {
    test("validates correct request", () => {
      const input: Generate1DRequest = {
        topic: "A cinematic scene of sunset",
        style: "cinematic",
        mood: "dramatic",
        duration: "15 seconds",
        language: "ko",
        model: "gemini-3-flash-preview",
        use_rag: true,
      };

      const result = Generate1DRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("applies defaults", () => {
      const input = { topic: "Test topic" };
      const result = Generate1DRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.style).toBe("cinematic");
        expect(result.data.mood).toBe("neutral");
        expect(result.data.language).toBe("ko");
        expect(result.data.use_rag).toBe(true);
      }
    });

    test("rejects empty topic", () => {
      const input = { topic: "" };
      const result = Generate1DRequestSchema.safeParse(input);

      expect(result.success).toBe(false);
    });

    test("rejects topic over 500 chars", () => {
      const input = { topic: "a".repeat(501) };
      const result = Generate1DRequestSchema.safeParse(input);

      expect(result.success).toBe(false);
    });

    test("trims whitespace from topic", () => {
      const input = { topic: "  Test topic  " };
      const result = Generate1DRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.topic).toBe("Test topic");
      }
    });
  });

  describe("Generate1DResponseSchema", () => {
    test("validates success response", () => {
      const response = {
        success: true,
        output: {
          prompt: "Generated prompt",
          negative_prompt: "blurry, low quality",
          style: {
            cinematography: "wide angle",
          },
        },
      };

      const result = Generate1DResponseSchema.safeParse(response);
      expect(result.success).toBe(true);
    });

    test("validates error response", () => {
      const response = {
        success: false,
        error: "Generation failed",
      };

      const result = Generate1DResponseSchema.safeParse(response);
      expect(result.success).toBe(true);
    });
  });
});

describe("2D - Storyboard Schema", () => {
  describe("Create2DRequestSchema", () => {
    test("validates correct request", () => {
      const input: Create2DRequest = {
        concept: "A story about a hero",
        scene_count: 5,
        language: "ko",
        model: "gemini-3-flash-preview",
        style: "Cinematic",
      };

      const result = Create2DRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("applies default scene_count", () => {
      const input = { concept: "Test concept" };
      const result = Create2DRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.scene_count).toBe(5);
      }
    });

    test("rejects scene_count over 30", () => {
      const input = { concept: "Test", scene_count: 50 };
      const result = Create2DRequestSchema.safeParse(input);

      expect(result.success).toBe(false);
    });
  });
});

describe("3D - Visual Realizer Schema", () => {
  describe("Generate3DRequestSchema", () => {
    test("validates correct request", () => {
      const input: Generate3DRequest = {
        description: "A beautiful landscape",
        style: "photorealistic",
        aspect_ratio: "16:9",
        model: "gemini-3-flash-preview",
      };

      const result = Generate3DRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("applies defaults", () => {
      const input = { description: "Test" };
      const result = Generate3DRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.style).toBe("photorealistic");
        expect(result.data.aspect_ratio).toBe("16:9");
      }
    });
  });
});

describe("4D - Reference Decoder Schema", () => {
  describe("Analyze4DRequestSchema", () => {
    test("validates request with URL", () => {
      const input = {
        reference_url: "https://example.com/video.mp4",
        analysis_depth: "standard" as const,
        language: "ko" as const,
        model: "gemini-3-flash-preview" as const,
      };

      const result = Analyze4DRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("validates request with text", () => {
      const input = {
        reference_text: "This is a reference text to analyze",
        analysis_depth: "deep" as const,
        language: "en" as const,
        model: "gemini-3-pro-preview" as const,
      };

      const result = Analyze4DRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("rejects request without URL or text", () => {
      const input = {
        analysis_depth: "standard" as const,
        language: "ko" as const,
        model: "gemini-3-flash-preview" as const,
      };

      const result = Analyze4DRequestSchema.safeParse(input);
      expect(result.success).toBe(false);
    });

    test("rejects invalid URL", () => {
      const input = {
        reference_url: "not-a-valid-url",
        analysis_depth: "standard" as const,
        language: "ko" as const,
        model: "gemini-3-flash-preview" as const,
      };

      const result = Analyze4DRequestSchema.safeParse(input);
      expect(result.success).toBe(false);
    });
  });
});

describe("VEO - Video Generation Schema", () => {
  describe("GenerateVeoRequestSchema", () => {
    test("validates correct request", () => {
      const input = {
        prompt: "A beautiful sunset",
        style: "cinematic" as const,
        duration: "15 seconds" as const,
        aspect_ratio: "16:9" as const,
        model: "gemini-3-flash-preview" as const,
      };

      const result = GenerateVeoRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("applies defaults", () => {
      const input = { prompt: "Test prompt" };
      const result = GenerateVeoRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.style).toBe("cinematic");
        expect(result.data.duration).toBe("15 seconds");
      }
    });

    test("validates optional reference_image_url", () => {
      const input = {
        prompt: "Test",
        reference_image_url: "https://example.com/image.jpg",
      };

      const result = GenerateVeoRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });
  });

  describe("GenerateVeoResponseSchema", () => {
    test("validates success response", () => {
      const response = {
        success: true,
        output: {
          video_url: "https://storage.example.com/video.mp4",
          duration_seconds: 15,
        },
      };

      const result = GenerateVeoResponseSchema.safeParse(response);
      expect(result.success).toBe(true);
    });
  });
});

describe("Quality Schema", () => {
  describe("QualityCheckRequestSchema", () => {
    test("validates correct request", () => {
      const input = {
        content: "This is content to check",
        content_type: "prompt" as const,
        model: "gemini-3-flash-preview" as const,
      };

      const result = QualityCheckRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("applies defaults", () => {
      const input = { content: "Test content" };
      const result = QualityCheckRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.content_type).toBe("prompt");
        expect(result.data.strict_mode).toBe(false);
      }
    });
  });

  describe("CreativeEditorRequestSchema", () => {
    test("validates correct request", () => {
      const input = {
        content: "Content to edit",
        context: "SF 영화 시나리오",
        persona: "Senior Editor" as const,
        model: "gemini-3-flash-preview" as const,
      };

      const result = CreativeEditorRequestSchema.safeParse(input);
      expect(result.success).toBe(true);
    });

    test("applies default persona", () => {
      const input = { content: "Test" };
      const result = CreativeEditorRequestSchema.safeParse(input);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.persona).toBe("Senior Editor");
      }
    });

    test("validates all persona options", () => {
      const personas = [
        "Senior Editor",
        "Ruthless Critic",
        "Commercial Producer",
        "Artistic Director",
      ] as const;

      for (const persona of personas) {
        const input = { content: "Test", persona };
        const result = CreativeEditorRequestSchema.safeParse(input);
        expect(result.success).toBe(true);
      }
    });
  });

  describe("QualityCheckResponseSchema", () => {
    test("validates success response", () => {
      const response = {
        success: true,
        output: {
          score: {
            overall: 85,
            clarity: 90,
            specificity: 80,
          },
          issues: [
            {
              severity: "warning",
              category: "clarity",
              message: "Consider being more specific",
            },
          ],
          summary: "Good quality overall",
        },
      };

      const result = QualityCheckResponseSchema.safeParse(response);
      expect(result.success).toBe(true);
    });
  });
});

describe("Type Inference", () => {
  test("infers correct types from schemas", () => {
    // This test verifies TypeScript compilation
    // If types are wrong, this won't compile
    const request: Generate1DRequest = {
      topic: "Test",
      style: "cinematic",
      mood: "dramatic",
      duration: "15 seconds",
      language: "ko",
      model: "gemini-3-flash-preview",
      use_rag: true,
    };

    expect(request.topic).toBe("Test");
    expect(typeof request.use_rag).toBe("boolean");
  });
});
