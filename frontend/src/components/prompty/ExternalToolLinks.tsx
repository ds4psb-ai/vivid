"use client";

interface ExternalToolLinksProps {
  toolId: string;
  externalUrl?: string;
  onOpen?: () => void;
}

// 도구 매핑 상수
const TOOL_CONFIG: Record<string, { name: string; icon: string; url: string }> = {
  nanobanana: {
    name: "NanoBanana",
    icon: "🍌",
    url: "https://nanobanana.com",
  },
  kling: {
    name: "Kling AI",
    icon: "🎬",
    url: "https://klingai.com",
  },
  davinci: {
    name: "DaVinci Resolve",
    icon: "🎞️",
    url: "https://www.blackmagicdesign.com/products/davinciresolve",
  },
  suno: {
    name: "Suno AI",
    icon: "🎵",
    url: "https://suno.ai",
  },
  midjourney: {
    name: "Midjourney",
    icon: "🎨",
    url: "https://www.midjourney.com",
  },
  runway: {
    name: "Runway",
    icon: "🎥",
    url: "https://runwayml.com",
  },
  pika: {
    name: "Pika",
    icon: "⚡",
    url: "https://pika.art",
  },
};

/**
 * ExternalToolLinks - 외부 도구 링크 컴포넌트
 *
 * 지원하는 외부 도구에 대한 링크 버튼 표시
 */
export function ExternalToolLinks({
  toolId,
  externalUrl,
  onOpen,
}: ExternalToolLinksProps) {
  const tool = TOOL_CONFIG[toolId];

  if (!tool) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="font-semibold mb-4">외부 도구</h3>
        <span className="text-muted-foreground">
          알 수 없는 도구: {toolId}
        </span>
      </div>
    );
  }

  const finalUrl = externalUrl || tool.url;

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h3 className="font-semibold mb-4">외부 도구</h3>
      <a
        href={finalUrl}
        target="_blank"
        rel="noopener noreferrer"
        onClick={onOpen}
        className="inline-flex items-center gap-2 px-6 py-3 bg-muted rounded-lg hover:bg-muted/80 transition"
      >
        <span className="text-lg">{tool.icon}</span>
        <span className="font-medium">{tool.name} 열기</span>
        <span>→</span>
      </a>
    </div>
  );
}

export default ExternalToolLinks;
