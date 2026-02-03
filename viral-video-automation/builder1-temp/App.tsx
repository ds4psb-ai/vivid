import React, { useState } from 'react';
import { Header } from './components/Header';
import { FileUpload } from './components/FileUpload';
import { ProcessingOverlay } from './components/ProcessingOverlay';
import { ChatInterface } from './components/ResultView';
import { startAnalysisChat, sendUserFeedback } from './services/geminiService';
import { AppStatus, ChatMessage } from './types';
import { ShieldAlert, Sparkles, Settings2, Clock, Copy, Check } from 'lucide-react';

const FFMPEG_PROMPT = `영상 프로젝트 폴더에 넣고, 첫 프레임 + 씬 전환 프레임 추출해줘 (threshold 0.18). 타임스탬프는 0.01초로 올림해서 복붙 가능하게 따로 알려줘.`;

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [timestamps, setTimestamps] = useState<string>('');
  const [promptCopied, setPromptCopied] = useState(false);
  // mode 상태 삭제됨 - 항상 MINIMAL 모드 사용
  const [status, setStatus] = useState<AppStatus>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(FFMPEG_PROMPT);
    setPromptCopied(true);
    setTimeout(() => setPromptCopied(false), 2000);
  };

  const handleStartAnalysis = async () => {
    if (!file || !timestamps.trim()) return;

    setStatus('THINKING');
    setErrorMsg(null);
    setMessages([]);
    setCurrentStep(1);

    try {
      // Start Chat - Step 1 with timestamps
      const response = await startAnalysisChat(file, timestamps.trim());

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
      if (currentStep < 4) {
        nextStep = currentStep + 1;
      }
      setCurrentStep(nextStep);

      setMessages([
        ...newMessages,
        { role: 'model', text: response, step: nextStep }
      ]);

      if (nextStep >= 4) {
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
    setTimestamps('');
    setStatus('IDLE');
    setMessages([]);
    setErrorMsg(null);
    setCurrentStep(1);
  };

  return (
    <div className="min-h-screen font-sans text-gray-100 selection:bg-accent-blue/30">
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

        {/* View: INPUT & CONFIG */}
        {status === 'IDLE' && (
          <div className="space-y-8 animate-in fade-in duration-500">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white via-gray-200 to-gray-500 tracking-tight">
                AI 이미지 프롬프트 생성기
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto text-lg leading-relaxed">
                원본 영상을 분석하여 <span className="text-white font-semibold">씬별 이미지 프롬프트</span>를 생성합니다.<br />
                NanoBanana Pro / Midjourney V7 에서 바로 사용 가능!
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Left Column: Config */}
              <div className="md:col-span-1 space-y-6">
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800 h-full">
                  <div className="flex items-center gap-2 mb-4 text-accent-cyan">
                    <Settings2 className="w-5 h-5" />
                    <h3 className="font-semibold">설정 (Settings)</h3>
                  </div>

                  <div className="space-y-4">
                    <p className="text-sm text-gray-400">Builder 1은 영상을 분석하여 각 씬별 이미지 프롬프트를 생성합니다.</p>
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-800">
                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">V7.4 Features</h4>
                    <ul className="text-xs text-gray-400 space-y-2">
                      <li className="flex gap-2">
                        <span className="text-yellow-500">★</span>
                        <b className="text-yellow-400">FFmpeg 타임스탬프 기반 분석</b>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        타임코드 정밀도 (밀리초)
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        듀얼 레퍼런스 라벨
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        MJ V7 파라미터 (--v 7)
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        구도 분석 (소실점/삼분할)
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Right Column: Upload + Timestamps */}
              <div className="md:col-span-2 space-y-6">
                <FileUpload selectedFile={file} onFileSelect={setFile} />

                {/* FFmpeg Timestamps Input */}
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 text-accent-cyan">
                      <Clock className="w-5 h-5" />
                      <h3 className="font-semibold">FFmpeg 타임스탬프</h3>
                    </div>
                    <span className="text-xs text-gray-500">필수</span>
                  </div>

                  {/* Antigravity 프롬프트 복사 영역 */}
                  <div className="mb-4 p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-xs text-gray-400 leading-relaxed flex-1">
                        <span className="text-yellow-400 font-medium">1단계:</span> 아래 프롬프트를 Antigravity에 영상과 함께 전송하세요
                      </p>
                      <button
                        onClick={handleCopyPrompt}
                        className="flex-shrink-0 text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded flex items-center gap-1 transition-colors"
                      >
                        {promptCopied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                        {promptCopied ? '복사됨' : '복사'}
                      </button>
                    </div>
                    <p className="mt-2 text-xs text-gray-300 font-mono bg-gray-900/50 p-2 rounded border border-gray-600">
                      {FFMPEG_PROMPT}
                    </p>
                  </div>

                  {/* 타임스탬프 입력 */}
                  <div>
                    <p className="text-xs text-gray-400 mb-2">
                      <span className="text-yellow-400 font-medium">2단계:</span> Antigravity가 알려준 타임스탬프 그대로 붙여넣기
                    </p>
                    <textarea
                      value={timestamps}
                      onChange={(e) => setTimestamps(e.target.value)}
                      placeholder="Antigravity가 알려준 타임스탬프 복붙 (형식 상관없음)"
                      className="w-full h-24 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50 resize-none font-mono"
                    />
                    <p className="mt-2 text-xs text-gray-500">
                      쉼표, 줄바꿈, 공백 다 OK - 그냥 복붙하세요
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleStartAnalysis}
                  disabled={!file || !timestamps.trim()}
                  className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform active:scale-95
                    ${(!file || !timestamps.trim())
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-accent-blue via-accent-purple to-accent-blue bg-[length:200%_auto] animate-gradient text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.5)]'
                    }`}
                >
                  <Sparkles className="w-5 h-5" />
                  분석 시작 (Step 1)
                </button>
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