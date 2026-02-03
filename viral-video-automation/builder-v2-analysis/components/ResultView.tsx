import React, { useState, useEffect, useRef } from 'react';
import { Copy, Check, Terminal, Send, Play, RefreshCw, AlertCircle, Download } from 'lucide-react';
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
  const [inputText, setInputText] = useState("네, 분석 결과가 정확합니다. 다음 단계로 진행해주세요.");
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

  const handleDownload = () => {
    // 사용자 요청 반영: "채팅 내용 Raw 파일"로 저장
    // 마지막 메시지(Step 5)만 저장하는 것이 아니라, 전체 히스토리를 병합하여 
    // AI의 요약으로 인한 데이터 손실을 원천 차단함.
    
    let rawContent = `# 🎬 AI VIDEO REPLICATION - RAW CHAT LOG\n\n`;
    rawContent += `> Generated: ${new Date().toLocaleString()}\n`;
    rawContent += `> System Version: v6.0 (Raw Export)\n`;
    rawContent += `> Note: 이 파일은 채팅의 모든 단계를 원본 그대로 병합한 기록입니다.\n\n`;

    messages.forEach((msg) => {
      if (msg.role === 'model') {
        rawContent += `\n---\n\n## 📍 STEP ${msg.step || 'Unknown'}\n\n`;
        rawContent += msg.text;
        rawContent += `\n`;
      }
    });

    const blob = new Blob([rawContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `VIDEO_PROMPTS_FULL_RAW_${new Date().toISOString().slice(0,10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleSend = () => {
    if (!inputText.trim()) return;
    onSendMessage(inputText);
    
    // Smart suggestions for next step
    if (currentStep === 4) {
      setInputText("완벽합니다. 최종 리포트(마크다운)를 생성해주세요.");
    } else if (currentStep < 5) {
      setInputText("네, 좋습니다. 다음 단계로 진행해주세요.");
    } else {
      setInputText("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

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
            AI 프롬프트 생성기 (Step {currentStep}/5)
          </span>
        </div>
        <div className="flex items-center gap-3">
            {currentStep >= 5 && (
                <button
                    onClick={handleDownload}
                    className="text-xs px-3 py-1.5 bg-accent-blue/10 text-accent-blue border border-accent-blue/30 rounded-md hover:bg-accent-blue/20 flex items-center gap-2 transition-all font-medium"
                >
                    <Download className="w-3 h-3" />
                    채팅 원본(Raw) 다운로드 (.md)
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
        <div className="relative flex items-end gap-2 max-w-4xl mx-auto">
          <div className="relative flex-1">
            <textarea 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="피드백을 입력하거나 '다음 단계'를 입력하세요..."
              className="w-full bg-black border border-gray-700 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-accent-blue focus:border-transparent outline-none transition-all resize-none min-h-[50px] max-h-[120px]"
              disabled={isLoading || currentStep > 5}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={isLoading || !inputText.trim() || currentStep > 5}
            className={`h-[50px] px-6 rounded-xl font-bold flex items-center gap-2 transition-all
              ${(isLoading || !inputText.trim() || currentStep > 5)
                ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                : 'bg-accent-blue text-white hover:bg-blue-600 hover:shadow-lg active:scale-95'
              }`}
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">전송</span>
          </button>
        </div>
        {currentStep <= 5 && (
             <p className="text-center text-xs text-gray-500 mt-2">
               💡 팁: AI 분석이 정확하다면 <b>"전송"</b> 버튼을 눌러 다음 단계로 넘어가세요.
             </p>
        )}
        {currentStep > 5 && (
            <p className="text-center text-xs text-green-500 mt-2 font-bold animate-pulse">
               🎉 모든 작업이 완료되었습니다. 우측 상단의 [채팅 원본 다운로드] 버튼을 눌러 저장하세요.
            </p>
        )}
      </div>
    </div>
  );
};