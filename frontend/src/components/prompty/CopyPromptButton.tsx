"use client";

import { useState } from "react";

interface CopyPromptButtonProps {
  promptText: string;
  onCopy?: () => void;
}

/**
 * CopyPromptButton - 프롬프트 복사 버튼
 *
 * 클릭 시 프롬프트를 클립보드에 복사하고 피드백 표시
 */
export function CopyPromptButton({ promptText, onCopy }: CopyPromptButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(promptText);
    setCopied(true);
    onCopy?.();
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={handleCopy}
      className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition text-sm flex items-center gap-2"
    >
      {copied ? (
        <>✓ 복사됨</>
      ) : (
        <>📋 클립보드에 복사</>
      )}
    </button>
  );
}

export default CopyPromptButton;
