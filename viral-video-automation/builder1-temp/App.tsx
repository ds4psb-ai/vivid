import React, { useState } from 'react';
import { Header } from './components/Header';
import { FileUpload } from './components/FileUpload';
import { ProcessingOverlay } from './components/ProcessingOverlay';
import { ChatInterface } from './components/ResultView';
import { startAnalysisChat, sendUserFeedback } from './services/geminiService';
import { AppStatus, ChatMessage, VariationData, VariationOption } from './types';
import { ShieldAlert, Sparkles, Settings2, TableProperties, ExternalLink } from 'lucide-react';

const ACADEMY_UPLOAD_URL = "https://www.prompty.co.kr/academy?tab=upload";

const TOTAL_STEPS = 5; // V8.1: 6단계 → 5단계 축소

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [sceneTable, setSceneTable] = useState<string>('');
  const [status, setStatus] = useState<AppStatus>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [variationData, setVariationData] = useState<VariationData>({
    personaJson: null,
    personaContent: null,
    bestComment: '',
    variationOption: null,
  });

  const handleStartGeneration = async () => {
    if (!file || !sceneTable.trim()) return;

    setStatus('THINKING');
    setErrorMsg(null);
    setMessages([]);
    setCurrentStep(1);

    try {
      const response = await startAnalysisChat(file, sceneTable.trim());

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

      // "다음" 관련 명령어 감지
      const isNextCommand = /다음|계속|진행|next|좋습니다/i.test(text);

      // 통합 워크플로우 감지 (STEP 4 완료 신호)
      const hasIntegratedWorkflow = response.includes('🎬 오마주 워크플로우') ||
                                     response.includes('## ⭐ 앵커 이미지');

      // 변주 워크플로우 감지 (STEP 5 완료 신호)
      const hasVariationWorkflow = response.includes('🎬 변주 워크플로우');

      let nextStep = currentStep;

      if (hasVariationWorkflow) {
        nextStep = 5; // 변주 워크플로우 = STEP 5
      } else if (hasIntegratedWorkflow) {
        nextStep = 4; // 통합 워크플로우 = STEP 4
      } else if (isNextCommand && currentStep < TOTAL_STEPS) {
        // "다음" 명령어 입력 시에만 Step 증가
        nextStep = currentStep + 1;
      }
      // else: currentStep 유지 (피드백/오마주 스타일 입력 중)

      setCurrentStep(nextStep);

      setMessages([
        ...newMessages,
        { role: 'model', text: response, step: nextStep }
      ]);

      if (nextStep >= TOTAL_STEPS) {
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
    setSceneTable('');
    setStatus('IDLE');
    setMessages([]);
    setErrorMsg(null);
    setCurrentStep(1);
    setVariationData({
      personaJson: null,
      personaContent: null,
      bestComment: '',
      variationOption: null,
    });
  };

  // 변주 메시지 생성 함수
  const generateVariationMessage = (data: VariationData): string => {
    let message = `[STEP 5: 변주 생성]을 시작합니다.\n\n`;

    const optionLabels: Record<VariationOption, string> = {
      'A': '🅰️ 안정형 (8%) - 소품 디테일만 변경',
      'B': '🅱️ 밸런스형 (15%) - 의상/소품 + 조명 톤',
      'AB': '🆎 과감형 (18%) - 문화권/스타일 전환',
    };
    message += `## 선택한 변주 옵션\n${optionLabels[data.variationOption!]}\n\n`;

    if (data.personaContent) {
      message += `## persona.json 내용\n\`\`\`json\n${JSON.stringify(data.personaContent, null, 2)}\n\`\`\`\n\n`;
    }

    if (data.bestComment.trim()) {
      message += `## 베스트 댓글\n\`\`\`\n${data.bestComment.trim()}\n\`\`\`\n\n`;
    }

    message += `위 옵션으로 변주 워크플로우를 생성해주세요.`;
    return message;
  };

  const handleGenerateVariation = async () => {
    const message = generateVariationMessage(variationData);
    await handleUserResponse(message);
  };

  const handleSkipVariation = () => {
    setStatus('COMPLETE');
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
                오마주 공방
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto text-lg leading-relaxed">
                <a href={ACADEMY_UPLOAD_URL} target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:text-accent-blue underline underline-offset-2 transition-colors">
                  아카데미
                </a>에서 추출한 씬 테이블 기반 <span className="text-white font-semibold">IMAGE + MOTION 프롬프트</span> 생성<br />
                NanoBanana / Midjourney V7 / Kling 3.0 / Veo 3.1 지원!
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {/* Left Column: Config */}
              <div className="md:col-span-1 space-y-6">
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800 h-full">
                  <div className="flex items-center gap-2 mb-4 text-accent-cyan">
                    <Settings2 className="w-5 h-5" />
                    <h3 className="font-semibold">워크플로우</h3>
                  </div>

                  <div className="space-y-3 text-sm text-gray-400">
                    <p>
                      <span className="text-accent-blue font-medium">1.</span>{" "}
                      <a href={ACADEMY_UPLOAD_URL} target="_blank" rel="noopener noreferrer" className="text-accent-cyan hover:text-white underline underline-offset-2 transition-colors inline-flex items-center gap-1">
                        Academy 영상 업로드 <ExternalLink className="w-3 h-3" />
                      </a>
                    </p>
                    <p><span className="text-accent-blue font-medium">2.</span> 타임스탬프 복사</p>
                    <p><span className="text-accent-blue font-medium">3.</span> 여기에 영상 + 타임스탬프 입력</p>
                    <p><span className="text-accent-blue font-medium">4.</span> 5-STEP 프롬프트 생성</p>
                  </div>

                  <div className="mt-8 pt-6 border-t border-gray-800">
                    <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Features</h4>
                    <ul className="text-xs text-gray-400 space-y-2">
                      <li className="flex gap-2">
                        <span className="text-yellow-500">★</span>
                        <b className="text-yellow-400">오마주 스타일 자유 입력</b>
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        IMAGE + MOTION 통합
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        Kling 3.0 + Veo 3.1
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        MJ V7 (--cref, --cw)
                      </li>
                      <li className="flex gap-2">
                        <span className="text-green-500">✓</span>
                        변주 생성 (선택)
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Right Column: Upload + Scene Table */}
              <div className="md:col-span-2 space-y-6">
                <FileUpload selectedFile={file} onFileSelect={setFile} />

                {/* Timestamp Input */}
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 text-accent-cyan">
                      <TableProperties className="w-5 h-5" />
                      <h3 className="font-semibold">타임스탬프</h3>
                    </div>
                    <a href={ACADEMY_UPLOAD_URL} target="_blank" rel="noopener noreferrer" className="text-xs text-accent-cyan hover:text-white underline underline-offset-2 transition-colors inline-flex items-center gap-1">
                      Academy에서 복사 <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div>
                    <p className="text-xs text-gray-400 mb-2">
                      <a href={ACADEMY_UPLOAD_URL} target="_blank" rel="noopener noreferrer" className="text-accent-blue font-medium hover:text-white underline underline-offset-2 transition-colors">Academy</a>에서 추출한 타임스탬프를 붙여넣으세요
                    </p>
                    <textarea
                      value={sceneTable}
                      onChange={(e) => setSceneTable(e.target.value)}
                      placeholder={`Scene | Timecode | Description | Anchor
01 | 00:00.00~00:01.67 | Wide shot, house exterior |
02 | 00:01.67~00:04.56 | Close-up, man's face | ⭐ (Man)
...`}
                      className="w-full h-32 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50 resize-none font-mono"
                    />
                    <p className="mt-2 text-xs text-gray-500">
                      테이블 형식, 쉼표, 줄바꿈 모두 OK
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleStartGeneration}
                  disabled={!file || !sceneTable.trim()}
                  className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform active:scale-95
                    ${(!file || !sceneTable.trim())
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-accent-blue via-accent-purple to-accent-blue bg-[length:200%_auto] animate-gradient text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.5)]'
                    }`}
                >
                  <Sparkles className="w-5 h-5" />
                  프롬프트 생성 시작
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
            variationData={variationData}
            onVariationDataChange={setVariationData}
            onGenerateVariation={handleGenerateVariation}
            onSkipVariation={handleSkipVariation}
          />
        )}
      </main>
    </div>
  );
};

export default App;
