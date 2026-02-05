import React, { useState, useEffect, useRef } from 'react';
import { Copy, Check, Terminal, Play, RefreshCw, Download } from 'lucide-react';
import { ChatMessage } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
  onReset: () => void;
  currentStep: number;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading,
  onReset,
  currentStep
}) => {
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 오마쥬 워크플로우 다운로드 (STEP 4)
  const handleDownloadHomage = () => {
    // STEP 4 메시지에서 통합 워크플로우 찾기
    const step4Message = messages.find(
      (msg) => msg.role === 'model' && msg.step === 4
    );

    if (!step4Message) {
      alert('오마쥬 워크플로우가 아직 생성되지 않았습니다.');
      return;
    }

    let rawContent = `# 🎬 오마쥬 워크플로우\n\n`;
    rawContent += `> Generated: ${new Date().toLocaleString()}\n`;
    rawContent += `> Builder Version: v8.1\n`;
    rawContent += `> Type: IMAGE + MOTION 통합 워크플로우\n\n`;
    rawContent += `---\n\n`;
    rawContent += step4Message.text;

    const blob = new Blob([rawContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `HOMAGE_WORKFLOW_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 변주 워크플로우 다운로드 (STEP 5)
  const handleDownloadVariation = () => {
    // STEP 5 메시지에서 변주 워크플로우 찾기
    const step5Message = messages.find(
      (msg) => msg.role === 'model' && msg.step === 5
    );

    if (!step5Message) {
      alert('변주 워크플로우가 아직 생성되지 않았습니다.');
      return;
    }

    let rawContent = `# 🎬 변주 워크플로우\n\n`;
    rawContent += `> Generated: ${new Date().toLocaleString()}\n`;
    rawContent += `> Builder Version: v8.1\n`;
    rawContent += `> Type: 변주 (Variation) 워크플로우\n\n`;
    rawContent += `---\n\n`;
    rawContent += step5Message.text;

    const blob = new Blob([rawContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `VARIATION_WORKFLOW_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // STEP 5 완료 여부 확인
  const hasVariationWorkflow = messages.some(
    (msg) => msg.role === 'model' && msg.step === 5
  );

  return (
    <div className="w-full h-[80vh] flex flex-col bg-[#0c0c0c] border border-gray-800 rounded-xl overflow-hidden shadow-2xl relative">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-gray-900 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50"></div>
          </div>
          <span className="text-sm font-bold text-gray-200 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-green-500" />
            오마쥬 빌더 (Step {currentStep}/5)
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* 오마쥬 워크플로우 다운로드 (STEP 4+) */}
          {currentStep >= 4 && (
            <button
              onClick={handleDownloadHomage}
              className="text-xs px-3 py-1.5 bg-accent-blue/10 text-accent-blue border border-accent-blue/30 rounded-md hover:bg-accent-blue/20 flex items-center gap-2 transition-all font-medium"
            >
              <Download className="w-3 h-3" />
              오마쥬 (.md)
            </button>
          )}
          {/* 변주 워크플로우 다운로드 (STEP 5) */}
          {hasVariationWorkflow && (
            <button
              onClick={handleDownloadVariation}
              className="text-xs px-3 py-1.5 bg-accent-purple/10 text-accent-purple border border-accent-purple/30 rounded-md hover:bg-accent-purple/20 flex items-center gap-2 transition-all font-medium"
            >
              <Download className="w-3 h-3" />
              변주 (.md)
            </button>
          )}
          <button
            onClick={onReset}
            className="text-xs text-gray-500 hover:text-white flex items-center gap-1 transition-colors px-2 py-1"
          >
            <RefreshCw className="w-3 h-3" /> 처음으로
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1 bg-gray-800">
        <div
          className="h-full bg-gradient-to-r from-accent-blue via-accent-purple to-accent-cyan transition-all duration-500 ease-out"
          style={{ width: `${(currentStep / 5) * 100}%` }}
        />
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6" ref={scrollRef}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} animate-in fade-in slide-in-from-bottom-2`}
          >
            <div className={`
              max-w-[95%] rounded-2xl p-4 shadow-lg border
              ${msg.role === 'user'
                ? 'bg-accent-blue/10 border-accent-blue/30 text-gray-100 rounded-tr-sm'
                : 'bg-gray-900 border-gray-700 text-gray-300 rounded-tl-sm'
              }
            `}>
              <pre className="font-mono text-sm whitespace-pre-wrap leading-relaxed font-sans">
                {msg.text}
              </pre>
            </div>

            {msg.role === 'model' && (
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => handleCopy(msg.text)}
                  className="text-xs flex items-center gap-1 text-gray-500 hover:text-accent-blue transition-colors"
                >
                  {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                  복사하기
                </button>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex flex-col items-start animate-pulse">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl rounded-tl-sm p-4 w-64 h-24 flex items-center justify-center">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-75"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-150"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gray-900 border-t border-gray-800">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* STEP 1-5: 텍스트 입력 + 다음 버튼 */}
          {currentStep <= 5 && !isLoading && (
            <>
              {/* 텍스트 입력 */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder={currentStep === 1
                    ? "오마쥬 스타일 입력 (예: 한국인 20대, 일본 스타일...) 기본값: 한국인"
                    : "피드백이나 수정 요청을 입력하세요..."
                  }
                  className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      onSendMessage(e.currentTarget.value.trim());
                      e.currentTarget.value = '';
                    }
                  }}
                />
                <button
                  onClick={(e) => {
                    const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                    if (input.value.trim()) {
                      onSendMessage(input.value.trim());
                      input.value = '';
                    }
                  }}
                  className="px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-400 hover:text-white hover:border-accent-blue transition-colors"
                >
                  전송
                </button>
              </div>

              {/* 다음 단계 버튼 */}
              <button
                onClick={() => onSendMessage("네, 좋습니다. 다음 단계로 진행해주세요.")}
                className="w-full py-4 px-6 rounded-xl font-bold text-lg bg-gradient-to-r from-accent-blue to-accent-purple text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] active:scale-95 transition-all flex items-center justify-center gap-2"
              >
                <Play className="w-5 h-5" />
                {currentStep === 1 ? "기본값(한국인)으로 진행" :
                 currentStep === 4 ? "통합 워크플로우 생성" :
                 currentStep === 5 ? "변주 생성 (선택)" : "다음 단계"}
              </button>

              {currentStep === 1 && (
                <p className="text-center text-xs text-gray-500">
                  💡 오마쥬 스타일을 자유롭게 입력하거나, 기본값(한국인)으로 진행하세요
                </p>
              )}

              {currentStep >= 4 && (
                <p className="text-center text-xs text-gray-500">
                  💡 수정이 필요하면 위 입력창에 피드백을 작성하세요
                </p>
              )}
            </>
          )}

          {isLoading && (
            <div className="text-center text-gray-400 py-4">
              <div className="inline-flex items-center gap-2">
                <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce delay-75"></div>
                <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce delay-150"></div>
                <span className="ml-2">AI 처리 중...</span>
              </div>
            </div>
          )}

          {currentStep > 5 && (
            <p className="text-center text-xs text-green-500 font-bold animate-pulse">
              🎉 모든 작업이 완료되었습니다. 우측 상단의 [오마쥬] / [변주] 버튼으로 각각 다운로드하세요.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};