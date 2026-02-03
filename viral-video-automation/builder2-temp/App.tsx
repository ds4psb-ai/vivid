import React, { useState } from 'react';
import { Header } from './components/Header';
import { FileUpload } from './components/FileUpload';
import { ProcessingOverlay } from './components/ProcessingOverlay';
import { ChatInterface } from './components/ResultView';
import { startAnalysisChat, sendUserFeedback } from './services/geminiService';
import { AppStatus, ChatMessage } from './types';
import { ShieldAlert, Sparkles, MessageSquare, Upload, X, Plus, FileText, UserCircle2, FileUp } from 'lucide-react';

const App: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [builder1Output, setBuilder1Output] = useState('');
  const [personaJson, setPersonaJson] = useState('');
  const [bestComments, setBestComments] = useState<string[]>([]);
  const [newComment, setNewComment] = useState('');
  const [status, setStatus] = useState<AppStatus>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);

  const addComment = () => {
    if (newComment.trim() && bestComments.length < 5) {
      setBestComments([...bestComments, newComment.trim()]);
      setNewComment('');
    }
  };

  const removeComment = (index: number) => {
    setBestComments(bestComments.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newComment.trim()) {
      e.preventDefault();
      addComment();
    }
  };

  // File drop handlers for text inputs
  const handleFileDrop = async (e: React.DragEvent, setter: (value: string) => void) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.md') || file.name.endsWith('.txt') || file.name.endsWith('.json'))) {
      const text = await file.text();
      setter(text);
    } else {
      alert('지원되는 파일 형식: .md, .txt, .json');
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>, setter: (value: string) => void) => {
    const file = e.target.files?.[0];
    if (file) {
      const text = await file.text();
      setter(text);
    }
  };

  const handleStartAnalysis = async () => {
    if (!file) return;
    // Builder 1 is REQUIRED for quality validation
    if (!builder1Output.trim()) {
      alert("Builder 1 (이미지 프롬프트) 결과물은 필수 입력사항입니다. 텍스트 재현성 검증을 위해 필요합니다.");
      return;
    }

    setStatus('THINKING');
    setErrorMsg(null);
    setMessages([]);
    setCurrentStep(1);

    try {
      const response = await startAnalysisChat(
        file,
        builder1Output,
        bestComments,
        personaJson,
        'EXPERT'
      );

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
    setBuilder1Output('');
    setPersonaJson('');
    setBestComments([]);
    setNewComment('');
    setStatus('IDLE');
    setMessages([]);
    setErrorMsg(null);
    setCurrentStep(1);
  };

  return (
    <div className="min-h-screen font-sans text-gray-100 selection:bg-accent-purple/30">
      <Header />

      <main className="max-w-6xl mx-auto px-6 py-12">
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
                <span className="text-accent-blue font-semibold">Builder 1</span>의 분석 결과를 바탕으로<br />
                <span className="text-accent-purple font-semibold">바이럴 모션</span>과 <span className="text-accent-purple font-semibold">페르소나 변주</span>를 결합합니다.
              </p>
            </div>

            <div className="grid md:grid-cols-12 gap-8">
              {/* Left Column: Inputs (8 cols) */}
              <div className="md:col-span-8 space-y-6">

                {/* 1. Video Upload */}
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                  <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                    <Upload className="w-4 h-4 text-accent-blue" />
                    <span className="text-white font-bold">1. 영상 파일</span> <span className="text-red-400 text-xs">*필수</span>
                  </label>
                  <FileUpload selectedFile={file} onFileSelect={setFile} />
                </div>

                {/* 2. Builder 1 Input */}
                <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                  <label className="block text-sm text-gray-400 mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-accent-blue" />
                      <span className="text-white font-bold">2. Builder 1 결과물 (Markdown)</span> <span className="text-red-400 text-xs">*필수</span>
                    </div>
                    <label className="flex items-center gap-1 text-xs text-accent-blue cursor-pointer hover:text-blue-400">
                      <FileUp className="w-3 h-3" />
                      <span>파일 선택</span>
                      <input
                        type="file"
                        accept=".md,.txt"
                        className="hidden"
                        onChange={(e) => handleFileSelect(e, setBuilder1Output)}
                      />
                    </label>
                  </label>
                  <div
                    className="relative"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => handleFileDrop(e, setBuilder1Output)}
                  >
                    <textarea
                      value={builder1Output}
                      onChange={(e) => setBuilder1Output(e.target.value)}
                      placeholder="📂 .md 파일을 드래그하거나 붙여넣기..."
                      className="w-full h-40 bg-black border border-gray-700 rounded-lg p-4 text-sm font-mono text-gray-300 focus:ring-2 focus:ring-accent-purple focus:border-transparent outline-none resize-none custom-scrollbar"
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  {/* 3. Persona Input */}
                  <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                    <label className="block text-sm text-gray-400 mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <UserCircle2 className="w-4 h-4 text-accent-purple" />
                        <span className="text-white font-bold">3. Persona JSON</span> <span className="text-gray-600 text-xs">(선택)</span>
                      </div>
                      <label className="flex items-center gap-1 text-xs text-accent-purple cursor-pointer hover:text-purple-400">
                        <FileUp className="w-3 h-3" />
                        <span>파일</span>
                        <input
                          type="file"
                          accept=".json"
                          className="hidden"
                          onChange={(e) => handleFileSelect(e, setPersonaJson)}
                        />
                      </label>
                    </label>
                    <div
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={(e) => handleFileDrop(e, setPersonaJson)}
                    >
                      <textarea
                        value={personaJson}
                        onChange={(e) => setPersonaJson(e.target.value)}
                        placeholder='📂 .json 파일을 드래그하거나 붙여넣기...'
                        className="w-full h-32 bg-black border border-gray-700 rounded-lg p-4 text-sm font-mono text-gray-300 focus:ring-2 focus:ring-accent-purple focus:border-transparent outline-none resize-none custom-scrollbar"
                      />
                    </div>
                  </div>

                  {/* 4. Best Comments */}
                  <div className="bg-gray-900/50 p-6 rounded-xl border border-gray-800">
                    <label className="block text-sm text-gray-400 mb-2 flex items-center gap-2">
                      <MessageSquare className="w-4 h-4 text-accent-purple" />
                      <span className="text-white font-bold">4. 베스트 댓글</span> <span className="text-gray-600 text-xs">(선택)</span>
                    </label>

                    {/* Added Comments */}
                    <div className="h-20 overflow-y-auto custom-scrollbar mb-2 space-y-1">
                      {bestComments.map((comment, idx) => (
                        <div key={idx} className="flex gap-2 items-center bg-purple-500/10 border border-purple-500/30 rounded px-2 py-1 group">
                          <span className="flex-1 text-xs text-white truncate">{comment}</span>
                          <button onClick={() => removeComment(idx)} className="text-gray-500 hover:text-red-400">
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                      {bestComments.length === 0 && (
                        <p className="text-xs text-gray-600 text-center py-4">댓글을 입력하여 바이럴 포인트를 분석하세요</p>
                      )}
                    </div>

                    {/* Input */}
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={bestComments.length >= 5}
                        placeholder="댓글 입력..."
                        className="flex-1 bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white focus:border-purple-500 outline-none"
                      />
                      <button
                        onClick={addComment}
                        disabled={!newComment.trim() || bestComments.length >= 5}
                        className="px-3 py-1 bg-gray-800 text-gray-400 rounded hover:bg-gray-700 disabled:opacity-50 text-xs"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleStartAnalysis}
                  disabled={!file || !builder1Output}
                  className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all transform active:scale-95
                    ${(!file || !builder1Output)
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-accent-purple via-accent-blue to-accent-purple bg-[length:200%_auto] animate-gradient text-white hover:shadow-[0_0_20px_rgba(139,92,246,0.5)]'
                    }`}
                >
                  <Sparkles className="w-5 h-5 animate-float" />
                  패러디 분석 시작 (Step 1)
                </button>
              </div>

              {/* Right Column: Workflow Info (4 cols) */}
              <div className="md:col-span-4">
                <div className="glass glow-purple p-6 rounded-xl border border-gray-700/50 h-full sticky top-24">
                  <h4 className="text-xs font-bold text-gray-500 uppercase mb-6">4-STEP COPY-PASTE</h4>
                  <ul className="text-sm text-gray-400 space-y-4">
                    <li className="flex gap-3 items-start">
                      <div className="flex flex-col items-center gap-1">
                        <span className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-bold border border-purple-500/30">1</span>
                        <div className="h-full w-px bg-gray-800 my-1"></div>
                      </div>
                      <div>
                        <div className="text-white font-medium">검증 + 바이럴 로직</div>
                        <div className="text-xs text-gray-500">영상 vs Builder 1 + Hook 분석</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <div className="flex flex-col items-center gap-1">
                        <span className="w-6 h-6 rounded-full bg-gray-800 text-gray-500 flex items-center justify-center text-xs font-bold border border-gray-700">2</span>
                        <div className="h-full w-px bg-gray-800 my-1"></div>
                      </div>
                      <div>
                        <div className="text-gray-300">캐릭터 + MOTION</div>
                        <div className="text-xs text-gray-500">Kling 3.0 / Veo 3.1 프롬프트</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <div className="flex flex-col items-center gap-1">
                        <span className="w-6 h-6 rounded-full bg-gray-800 text-gray-500 flex items-center justify-center text-xs font-bold border border-gray-700">3</span>
                        <div className="h-full w-px bg-gray-800 my-1"></div>
                      </div>
                      <div>
                        <div className="text-gray-300">변주 옵션</div>
                        <div className="text-xs text-gray-500">A/B/C 선택</div>
                      </div>
                    </li>
                    <li className="flex gap-3 items-start">
                      <div className="flex flex-col items-center gap-1">
                        <span className="w-6 h-6 rounded-full bg-gray-800 text-gray-500 flex items-center justify-center text-xs font-bold border border-gray-700">4</span>
                      </div>
                      <div>
                        <div className="text-gray-300">Final Export</div>
                        <div className="text-xs text-gray-500">4개 파일 다운로드</div>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* View: PROCESSING */}
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