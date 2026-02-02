"use client";

export interface CritiqueItem {
  id: string;
  label: string;
  description: string;
  weight?: number;
}

interface CritiqueChecklistProps {
  items: CritiqueItem[];
  scores: Record<string, { score: number; notes: string }>;
  onScoreChange: (itemId: string, score: number) => void;
  onNotesChange: (itemId: string, notes: string) => void;
  passingScore?: number;
}

/**
 * CritiqueChecklist - 크리틱 평가 체크리스트
 *
 * 템플릿에서 로드한 critique_config.items를 사용하여
 * 동적으로 평가 항목 표시
 */
export function CritiqueChecklist({
  items,
  scores,
  onScoreChange,
  onNotesChange,
  passingScore = 75,
}: CritiqueChecklistProps) {
  // 현재 총점 계산 (평균 * 10)
  const currentScores = Object.values(scores).filter((s) => s.score > 0);
  const averageScore =
    currentScores.length > 0
      ? currentScores.reduce((sum, s) => sum + s.score, 0) / currentScores.length
      : 0;
  const totalScore = averageScore * 10;
  const isPassing = totalScore >= passingScore;

  return (
    <div className="space-y-6">
      {/* 현재 점수 표시 */}
      <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
        <div>
          <span className="text-sm text-muted-foreground">예상 총점</span>
          <div className={`text-2xl font-bold ${isPassing ? "text-green-500" : "text-red-500"}`}>
            {totalScore.toFixed(0)}점
          </div>
        </div>
        <div className="text-right">
          <span className="text-sm text-muted-foreground">합격 기준</span>
          <div className="text-lg font-medium">{passingScore}점</div>
        </div>
      </div>

      {/* 체크리스트 항목 */}
      {items.map((item) => (
        <div key={item.id} className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">{item.label}</h3>
              <p className="text-sm text-muted-foreground">{item.description}</p>
              {item.weight && (
                <span className="text-xs text-muted-foreground">
                  가중치: {(item.weight * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <span className="text-2xl font-bold text-primary">
              {scores[item.id]?.score || "-"}
            </span>
          </div>

          {/* Score Slider */}
          <div className="flex items-center gap-4">
            <span className="text-xs text-muted-foreground w-4">1</span>
            <input
              type="range"
              min="1"
              max="10"
              value={scores[item.id]?.score || 5}
              onChange={(e) => onScoreChange(item.id, parseInt(e.target.value))}
              className="flex-1 h-2 bg-muted rounded-lg appearance-none cursor-pointer"
            />
            <span className="text-xs text-muted-foreground w-4">10</span>
          </div>

          {/* Notes */}
          <input
            type="text"
            placeholder="메모 (선택)"
            value={scores[item.id]?.notes || ""}
            onChange={(e) => onNotesChange(item.id, e.target.value)}
            className="w-full px-3 py-2 bg-muted rounded-lg text-sm"
          />
        </div>
      ))}
    </div>
  );
}

// 기본 체크리스트 (템플릿이 없을 때 사용)
export const DEFAULT_CRITIQUE_ITEMS: CritiqueItem[] = [
  { id: "composition", label: "구도", description: "시각적 균형과 구성", weight: 0.2 },
  { id: "consistency", label: "일관성", description: "스타일과 캐릭터 일관성", weight: 0.2 },
  { id: "lighting", label: "조명", description: "조명 품질과 분위기", weight: 0.2 },
  { id: "detail", label: "디테일", description: "세부 묘사 품질", weight: 0.2 },
  { id: "emotion", label: "감정", description: "의도한 감정 전달", weight: 0.2 },
];

export default CritiqueChecklist;
