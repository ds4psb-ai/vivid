"use client";

interface MetadataSectionProps {
  title: string;
  isCompact: boolean;
  children: React.ReactNode;
}

/**
 * MetadataSection - DNA Card 메타데이터 섹션 공통 컴포넌트
 *
 * @param title - 섹션 제목
 * @param isCompact - compact 모드 여부 (프리뷰 vs 사이드패널)
 * @param children - 섹션 내용
 */
export function MetadataSection({
  title,
  isCompact,
  children,
}: MetadataSectionProps) {
  return (
    <div className={isCompact ? "" : "space-y-2"}>
      <h5
        className={`font-medium uppercase tracking-wider ${
          isCompact
            ? "text-[10px] text-white/50 mb-1"
            : "text-xs text-[var(--fg-muted)]"
        }`}
      >
        {title}
      </h5>
      {children}
    </div>
  );
}
