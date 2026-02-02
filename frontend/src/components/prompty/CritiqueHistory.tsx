"use client";

import { useMemo } from "react";

export interface CritiqueIteration {
  iteration: number;
  score: number;
  verdict: "PASS" | "REVISE" | "REJECT";
  createdAt: string;
  notes?: string;
}

interface CritiqueHistoryProps {
  iterations: CritiqueIteration[];
  targetScore?: number;
  stepId?: string;
}

/**
 * CritiqueHistory - 티키타카 반복 이력 시각화
 *
 * 점수 변화 그래프와 통계를 표시
 * 목표 점수(85)까지의 진행 상황을 보여줌
 */
export function CritiqueHistory({
  iterations,
  targetScore = 85,
  stepId,
}: CritiqueHistoryProps) {
  // 통계 계산
  const stats = useMemo(() => {
    if (iterations.length === 0) {
      return {
        avgScore: 0,
        minScore: 0,
        maxScore: 0,
        totalIterations: 0,
        passedAt: null as number | null,
        isComplete: false,
      };
    }

    const scores = iterations.map((i) => i.score);
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    const passedIteration = iterations.find((i) => i.verdict === "PASS");

    return {
      avgScore: Math.round(avgScore * 10) / 10,
      minScore: Math.min(...scores),
      maxScore: Math.max(...scores),
      totalIterations: iterations.length,
      passedAt: passedIteration?.iteration || null,
      isComplete: !!passedIteration,
    };
  }, [iterations]);

  // 차트 데이터 준비 (최대 10개 반복 표시)
  const chartData = useMemo(() => {
    const displayIterations = iterations.slice(-10);
    return displayIterations;
  }, [iterations]);

  // SVG 차트 렌더링
  function renderChart() {
    if (chartData.length === 0) {
      return (
        <div className="h-40 flex items-center justify-center text-muted-foreground">
          아직 기록이 없습니다
        </div>
      );
    }

    const width = 280;
    const height = 120;
    const padding = { top: 20, right: 20, bottom: 25, left: 35 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Scale functions
    const xScale = (i: number) =>
      padding.left + (i / Math.max(chartData.length - 1, 1)) * chartWidth;
    const yScale = (score: number) =>
      height - padding.bottom - (score / 100) * chartHeight;

    // Create path
    const linePath = chartData
      .map((d, i) => `${i === 0 ? "M" : "L"} ${xScale(i)} ${yScale(d.score)}`)
      .join(" ");

    // Target line y position
    const targetY = yScale(targetScore);

    return (
      <svg width={width} height={height} className="w-full">
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((tick) => (
          <g key={tick}>
            <line
              x1={padding.left}
              y1={yScale(tick)}
              x2={width - padding.right}
              y2={yScale(tick)}
              stroke="currentColor"
              strokeOpacity={0.1}
            />
            <text
              x={padding.left - 5}
              y={yScale(tick)}
              textAnchor="end"
              alignmentBaseline="middle"
              className="text-[10px] fill-muted-foreground"
            >
              {tick}
            </text>
          </g>
        ))}

        {/* Target line */}
        <line
          x1={padding.left}
          y1={targetY}
          x2={width - padding.right}
          y2={targetY}
          stroke="#22c55e"
          strokeWidth={1.5}
          strokeDasharray="4 2"
        />
        <text
          x={width - padding.right + 2}
          y={targetY}
          alignmentBaseline="middle"
          className="text-[9px] fill-green-500"
        >
          목표
        </text>

        {/* Line */}
        <path
          d={linePath}
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          className="text-primary"
        />

        {/* Points */}
        {chartData.map((d, i) => (
          <g key={i}>
            <circle
              cx={xScale(i)}
              cy={yScale(d.score)}
              r={4}
              className={
                d.verdict === "PASS"
                  ? "fill-green-500"
                  : d.verdict === "REVISE"
                  ? "fill-yellow-500"
                  : "fill-red-500"
              }
            />
            {/* X-axis labels */}
            <text
              x={xScale(i)}
              y={height - 8}
              textAnchor="middle"
              className="text-[10px] fill-muted-foreground"
            >
              #{d.iteration}
            </text>
          </g>
        ))}
      </svg>
    );
  }

  const verdictBadge = (verdict: "PASS" | "REVISE" | "REJECT") => {
    const styles = {
      PASS: "bg-green-500/20 text-green-500",
      REVISE: "bg-yellow-500/20 text-yellow-500",
      REJECT: "bg-red-500/20 text-red-500",
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[verdict]}`}>
        {verdict}
      </span>
    );
  };

  return (
    <div className="rounded-xl border border-border bg-card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold flex items-center gap-2">
          <span className="text-xl">📈</span>
          티키타카 이력
          {stepId && <span className="text-muted-foreground font-normal">({stepId})</span>}
        </h3>
        {stats.isComplete && (
          <span className="px-3 py-1 bg-green-500/20 text-green-500 rounded-full text-sm font-medium">
            완료
          </span>
        )}
      </div>

      {/* Chart */}
      <div className="bg-muted/50 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground">목표: {targetScore}점</span>
          {stats.passedAt && (
            <span className="text-xs text-green-500">
              #{stats.passedAt}에서 PASS
            </span>
          )}
        </div>
        {renderChart()}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center p-3 bg-muted rounded-lg">
          <div className="text-xl font-bold text-primary">
            {stats.totalIterations}
          </div>
          <div className="text-xs text-muted-foreground">총 반복</div>
        </div>
        <div className="text-center p-3 bg-muted rounded-lg">
          <div className="text-xl font-bold">
            {stats.avgScore.toFixed(1)}
          </div>
          <div className="text-xs text-muted-foreground">평균 점수</div>
        </div>
        <div className="text-center p-3 bg-muted rounded-lg">
          <div className="text-xl font-bold text-green-500">
            {stats.maxScore}
          </div>
          <div className="text-xs text-muted-foreground">최고 점수</div>
        </div>
      </div>

      {/* Recent Iterations */}
      {iterations.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground">최근 기록</h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {[...iterations].reverse().slice(0, 5).map((iter) => (
              <div
                key={iter.iteration}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">#{iter.iteration}</span>
                  {verdictBadge(iter.verdict)}
                </div>
                <div className="flex items-center gap-3">
                  <span className="font-bold">{iter.score}점</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(iter.createdAt).toLocaleDateString("ko-KR")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Average iterations hint */}
      {stats.isComplete && (
        <p className="text-sm text-muted-foreground text-center">
          {stats.passedAt}회 반복 후 목표 달성 🎉
        </p>
      )}
    </div>
  );
}

export default CritiqueHistory;
