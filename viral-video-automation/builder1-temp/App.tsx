import React, { useState } from 'react';
import { Header } from './components/Header';
import { FileUpload } from './components/FileUpload';
import { ProcessingOverlay } from './components/ProcessingOverlay';
import { ChatInterface } from './components/ResultView';
import { startAnalysisChat, sendUserFeedback } from './services/geminiService';
import { AppStatus, OutputMode, ChatMessage } from './types';
import { ShieldAlert, Sparkles, Settings2 } from 'lucide-react';

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<OutputMode>('MINIMAL');
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
      // Start Chat - Step 1
      const response = await startAnalysisChat(file, mode);
      
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
                AI 영상 복제 프롬프트
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto text-lg leading-relaxed">
                원본 영상의 구도와 조명을 <span className="text-white font-semibold">100% 유지</span>하면서<br/>
                등장인물만 <span className="text-accent-blue font-semibold">한국인(Korean)</span>으로 완벽하게 변환합니다.
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
                    <div>
                      <label className="block text-sm text-gray-400 mb-2">출력 모드 (Output Mode)</label>
                      <div className="space-y-2">
                        {(['MINIMAL', 'EXPERT', 'BOTH'] as OutputMode[]).map((m) => (
                          <button
                            key={m}
                            onClick={() => setMode(m)}
                            className={`w-full text-left px-4 py-2 rounded-lg text-sm border transition-all
                              ${mode === m 
                                ? 'bg-accent-blue/10 border-accent-blue text-white' 
                                : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:bg-gray-800'
                              }`}
                          >
                            {m === 'MINIMAL' ? '간편 모드 (Minimal)' : 
                             m === 'EXPERT' ? '전문가 모드 (Expert)' : '둘 다 (Both)'}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-800">
                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">V7.0 RAW EXPORT</h4>
                    <ul className="text-xs text-gray-400 space-y-2">
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

              {/* Right Column: Upload */}
              <div className="md:col-span-2">
                <FileUpload selectedFile={file} onFileSelect={setFile} />
                
                <button
                  onClick={handleStartAnalysis}
                  disabled={!file}
                  className={`w-full mt-6 py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform active:scale-95
                    ${(!file)
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