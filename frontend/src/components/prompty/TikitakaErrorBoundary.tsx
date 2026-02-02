"use client";

import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  projectId?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * TikitakaErrorBoundary - Error boundary for TikitakaWorkflow
 *
 * Catches errors in the Tikitaka workflow and displays a user-friendly error UI.
 * Optionally reports to Sentry if available.
 */
export class TikitakaErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("TikitakaWorkflow Error:", error, errorInfo);

    // Report to Sentry if available
    if (typeof window !== "undefined" && (window as unknown as { Sentry?: { captureException: (e: Error, opts: object) => void } }).Sentry) {
      (window as unknown as { Sentry: { captureException: (e: Error, opts: object) => void } }).Sentry.captureException(error, {
        extra: {
          projectId: this.props.projectId,
          componentStack: errorInfo.componentStack,
        },
      });
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold mb-2">워크플로우 로드 실패</h2>
          <p className="text-muted-foreground mb-6">
            {this.state.error?.message || "알 수 없는 오류가 발생했습니다."}
          </p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition"
            >
              새로고침
            </button>
            <button
              onClick={this.handleReset}
              className="px-4 py-2 border border-border rounded-lg hover:bg-accent transition"
            >
              다시 시도
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default TikitakaErrorBoundary;
