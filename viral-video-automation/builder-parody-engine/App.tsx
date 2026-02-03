import React, { useState } from 'react';
import { Header } from './components/Header';
import { FileUpload } from './components/FileUpload';
import { ProcessingOverlay } from './components/ProcessingOverlay';
import { ChatInterface } from './components/ResultView';
import { startAnalysisChat, sendUserFeedback } from './services/geminiService';
import { AppStatus, ChatMessage } from './types';
import { ShieldAlert, Sparkles, MessageSquare, Upload } from 'lucide-react';

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [commentsFile, setCommentsFile] = useState<File | null>(null);
  const [status, setStatus] = useState<AppStatus>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  const handleStartAnalysis = async () => {
    if (!file) return;

    setStatus('THINKING');
    setErrorMsg(null);
    setMessages([]);
    setCurrentStep(1);

    try {
      // Start Chat - Step 1 with video (and comments file name if provided)
      const commentsContext = commentsFile ? `\n\n[베스트 댓글 파일: ${commentsFile.name}]` : '';
      const response = await startAnalysisChat(file, 'EXPERT');

      setMessages([
        { role: 'model', text: response, step: 1 }
      ]);
      setStatus('WAITING_USER');

    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "오류가 발생했습니다.");
      setStatus('ERROR');
    }
  };

  const handleUserResponse = async (text: string) => {
    const newMessages = [...messages, { role: 'user' as const, text }];
    setMessages(newMessages);
    setStatus('THINKING');

    try {
      const response = await sendUserFeedback(text);

      let nextStep = currentStep;
      if (currentStep < 6) {
        nextStep = currentStep + 1;
      }
      setCurrentStep(nextStep);

      setMessages([
        ...newMessages,
        { role: 'model', text: response, step: nextStep }
      ]);

      if (nextStep >= 6) {
        setStatus('COMPLETE');
      } else {
        setStatus('WAITING_USER');
      }

    } catch (err: any) {
      console.error(err);
      setErrorMsg(err.message || "메시지 전송 실패");
      setStatus('ERROR');
    }
  };

  const resetApp = () => {
    setFile(null);
    setCommentsFile(null);
    setStatus('IDLE');
    setMessages([]);
    setErrorMsg(null);
    setCurrentStep(1);
  };

  return (
    <div className="min-h-screen font-sans text-gray-100 selection:bg-accent-purple/30">
      <Header />

      <main className="max-w-5xl mx-auto px-6 py-12">
        {/* Status: ERROR */}
        {status === 'ERROR' && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-lg mb-8 flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 flex-shrink-0" />
            <p>{errorMsg}</p>
            <button onClick={() => setStatus('IDLE')} className="ml-auto text-sm underline hover:text-white">다시 시도</button>
          </div>
        )}

        {/* View: INPUT */}
        {status === 'IDLE' && (
          <div className="space-y-8 animate-in fade-in duration-500">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white via-gray-200 to-gray-500 tracking-tight">
                패러디 엔진 V2
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto text-lg leading-relaxed">
                영상의 <span className="text-white font-semibold">바이럴 수학적 로직</span>을 100% 보존하면서<br />
                <span className="text-accent-purple font-semibold">5-20% 문화적 변주</span>로 패러디를 생성합니다.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Left Column: Workflow Info */}
              <div className="md:col-span-1">
                <div className="glass glow-purple p-6 rounded-xl border border-gray-700/50 h-full">
                  <h4 className="text-xs font-bold text-gray-500 uppercase mb-4">6-STEP WORKFLOW</h4>
                  <ul className="text-sm text-gray-400 space-y-3">
                    <li className="flex gap-3 items-start">
                      <span className="text-purple-500 font-bold">1</span>
                      <div>
                        <div className="text-white">영상 분석</div>
                        <div className="text-xs text-gray-500">컷, 구도, 소실점 추출</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <span className="text-purple-500 font-bold">2</span>
                      <div>
                        <div className="text-white">바이럴 로직</div>
                        <div className="text-xs text-gray-500">통제 vs 변주 변수 분류</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <span className="text-purple-500 font-bold">3</span>
                      <div>
                        <div className="text-white">캐릭터 매핑</div>
                        <div className="text-xs text-gray-500">한국인 변환</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <span className="text-purple-500 font-bold">4</span>
                      <div>
                        <div className="text-white">이미지 생성</div>
                        <div className="text-xs text-gray-500">ANCHOR 기반 순차 생성</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <span className="text-purple-500 font-bold">5</span>
                      <div>
                        <div className="text-white">모션 + 변주</div>
                        <div className="text-xs text-gray-500">3개 옵션 + persona.json</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <span className="text-purple-500 font-bold">6</span>
                      <div>
                        <div className="text-white">RAW Export</div>
                        <div className="text-xs text-gray-500">전체 병합 출력</div>
                      </div>
                    </li>
                  </ul>

                  <div className="mt-6 pt-4 border-t border-gray-800">
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>🔒 <span className="text-gray-400">통제 변수</span>: 80-95%</div>
                      <div>🔓 <span className="text-gray-400">변주 가능</span>: 5-20%</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: File Uploads */}
              <div className="md:col-span-2 space-y-6">
                {/* Video Upload */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    영상 파일 <span className="text-red-400">*필수</span>
                  </label>
                  <FileUpload selectedFile={file} onFileSelect={setFile} />
                </div>

                {/* Best Comments Upload (Optional) */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4" />
                    베스트 댓글 <span className="text-gray-600">(선택)</span>
                  </label>
                  <div
                    className={`relative w-full h-24 border-2 border-dashed rounded-xl transition-all cursor-pointer
                      ${commentsFile
                        ? 'border-green-500/50 bg-green-500/5'
                        : 'border-gray-700 hover:border-gray-500 hover:bg-gray-800/50'
                      }`}
                    onClick={() => {
                      const input = document.createElement('input');
                      input.type = 'file';
                      input.accept = '.txt,.md';
                      input.onchange = (e) => {
                        const f = (e.target as HTMLInputElement).files?.[0];
                        if (f) setCommentsFile(f);
                      };
                      input.click();
                    }}
                  >
                    <div className="absolute inset-0 flex items-center justify-center">
                      {commentsFile ? (
                        <div className="text-center">
                          <p className="text-green-400 font-medium">{commentsFile.name}</p>
                          <p className="text-xs text-gray-500">클릭해서 변경</p>
                        </div>
                      ) : (
                        <div className="text-center">
                          <p className="text-gray-400">best_comments.txt 첨부</p>
                          <p className="text-xs text-gray-600">바이럴 포인트 분석에 활용</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleStartAnalysis}
                  disabled={!file}
                  className={`w-full mt-4 py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform active:scale-95
                    ${(!file)
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-accent-purple via-accent-blue to-accent-purple bg-[length:200%_auto] animate-gradient text-white hover:shadow-[0_0_20px_rgba(139,92,246,0.5)]'
                    }`}
                >
                  <Sparkles className="w-5 h-5 animate-float" />
                  분석 시작 (Step 1)
                </button>

                <p className="text-center text-xs text-gray-600">
                  💡 persona.json은 STEP 5 (변주 단계)에서 입력합니다
                </p>
              </div>
            </div>
          </div>
        )}

        {/* View: PROCESSING (Initial) */}
        {status === 'THINKING' && messages.length === 0 && (
          <ProcessingOverlay status={status} />
        )}

        {/* View: CHAT INTERFACE */}
        {(status === 'WAITING_USER' || status === 'COMPLETE' || (status === 'THINKING' && messages.length > 0)) && (
          <ChatInterface
            messages={messages}
            onSendMessage={handleUserResponse}
            isLoading={status === 'THINKING'}
            onReset={resetApp}
            currentStep={currentStep}
          />
        )}
      </main>
    </div>
  );
};

export default App;