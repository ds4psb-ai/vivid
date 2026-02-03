

import React, { useState, useEffect, useRef } from 'react';
import ControlPanel from './components/ControlPanel';
import ChatInterface from './components/ChatInterface';
import JsonProfilePanel from './components/JsonProfilePanel';
import { Message, UserProfile, AnalysisMode, DepthStage } from './types';
import {
  initializeChat,
  sendMessageToGemini,
  generateDigitalTwin,
  getCurrentDepthStage
} from './services/gemini';
import { GET_GREETING_TRIGGER, getDepthStage } from './constants';
import { Sparkles, BrainCircuit, RefreshCcw, PanelRightOpen, PanelRightClose } from 'lucide-react';

const App: React.FC = () => {
  // State
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    birthDate: '',
    calendarType: 'solar',
    birthTime: '',
    birthPlace: '',
    bloodType: '',
    mbti: '',
    gender: 'other',
    residence: '',
    faceImage: '',
    faceFeatures: '',
    partner: {
      name: '',
      birthDate: '',
      calendarType: 'solar',
      birthTime: '',
      birthPlace: '',
      bloodType: '',
      mbti: '',
      gender: 'other'
    }
  });

  const [mode, setMode] = useState<AnalysisMode>('integrated');
  const [depthScore, setDepthScore] = useState(0);
  const [currentStage, setCurrentStage] = useState<DepthStage>('exploration');
  const [turnCount, setTurnCount] = useState(0);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSessionActive, setIsSessionActive] = useState(false);

  // Digital Twin States
  const [isExtracting, setIsExtracting] = useState(false);
  const [digitalTwinData, setDigitalTwinData] = useState<string | null>(null);

  // Model & Panel States
  const [currentModel, setCurrentModel] = useState<'flash' | 'pro'>('flash');
  const [isJsonPanelVisible, setIsJsonPanelVisible] = useState(false);

  // Track previous mode to detect changes
  const prevModeRef = useRef<AnalysisMode>('integrated');
  const prevStageRef = useRef<DepthStage>('exploration');

  // Track model tier (useRef로 중복 방지, Google AI Builder 패턴)
  const isProModelActiveRef = useRef(false);

  // Ref to track current messages for use in useEffect
  const messagesRef = useRef<Message[]>([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // 심도 점수 변경 시 단계 업데이트 및 모델 전환 (Google AI Builder 패턴 적용)
  useEffect(() => {
    const newStage = getDepthStage(depthScore);
    const shouldBePro = depthScore >= 50;

    // 단계 또는 모델 티어 변경 확인
    const stageChanged = newStage !== currentStage;
    const modelTierChanged = shouldBePro !== isProModelActiveRef.current;

    if (stageChanged || (modelTierChanged && isSessionActive)) {
      if (stageChanged) {
        console.log(`[App] Stage transition: ${currentStage} -> ${newStage} (depth: ${depthScore})`);
        setCurrentStage(newStage);
      }

      if (modelTierChanged) {
        console.log(`[App] Model tier switching: ${isProModelActiveRef.current ? 'Pro' : 'Flash'} -> ${shouldBePro ? 'Pro' : 'Flash'}`);
        isProModelActiveRef.current = shouldBePro;
        setCurrentModel(shouldBePro ? 'pro' : 'flash');

        // 50% 도달 시 JSON 패널 자동 표시
        if (shouldBePro) {
          setIsJsonPanelVisible(true);
        }
      }

      // 단계 전환 또는 모델 업그레이드 시 채팅 세션 재초기화
      // initializeChat 함수 내부에서 depthScore >= 50 여부를 확인하여 모델 선택
      if (isSessionActive) {
        initializeChat(mode, profile, messagesRef.current, depthScore);
      }
    }
  }, [depthScore, currentStage, isSessionActive, mode, profile]);

  // Handle Session Start (Triggered from ControlPanel)
  const handleStartSession = async () => {
    setIsLoading(true);
    setIsSessionActive(true);
    setDepthScore(10);
    setCurrentStage('exploration');
    setTurnCount(0);
    setMessages([]);
    messagesRef.current = [];
    setDigitalTwinData(null);
    setCurrentModel('flash');
    isProModelActiveRef.current = false; // 모델 티어 추적 리셋

    try {
      // 1. Initialize Chat with current profile
      initializeChat(mode, profile, [], 10);

      // 2. Generate Initial Dynamic Greeting based on the profile data
      const triggerPrompt = GET_GREETING_TRIGGER(mode);
      const response = await sendMessageToGemini(triggerPrompt, 10, 0);

      if (response.text) {
        setMessages([{
          id: `init-greeting-${Date.now()}`,
          role: 'model',
          text: response.text,
          timestamp: new Date(),
        }]);
        // 응답에서 받은 심도 적용
        if (response.depth) {
          setDepthScore(response.depth);
        }
      }
    } catch (error) {
      console.error("Failed to start session", error);
      setMessages([{
        id: 'error-init',
        role: 'model',
        text: "기가 흐트러져서 목소리가 안 나오는구나... 다시 시도해주겠나?",
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // 모드 변경 처리
  const handleModeSelect = (newMode: AnalysisMode) => {
    if (newMode === mode) return;
    setMode(newMode);
  };

  // Effect: Handle Mode Changes (Only when session is active)
  useEffect(() => {
    const switchMode = async () => {
      if (!isSessionActive) return;

      // Re-initialize chat with CURRENT messages history and depth
      initializeChat(mode, profile, messagesRef.current, depthScore);

      // If this is a mode switch, generate greeting
      if (prevModeRef.current !== mode) {
        setIsLoading(true);
        try {
          const triggerPrompt = GET_GREETING_TRIGGER(mode);
          const response = await sendMessageToGemini(triggerPrompt, depthScore, turnCount);

          if (response.text) {
            setMessages(prev => [...prev, {
              id: `mode-greeting-${Date.now()}`,
              role: 'model',
              text: response.text,
              timestamp: new Date(),
            }]);
          }
        } catch (error) {
          console.error("Failed to generate mode greeting", error);
        } finally {
          setIsLoading(false);
        }
        prevModeRef.current = mode;
      }
    };

    switchMode();
  }, [mode, isSessionActive, profile.name, profile.faceFeatures, profile.partner, depthScore, turnCount]);

  // Reset function
  const handleReset = () => {
    setIsSessionActive(false);
    setMessages([]);
    messagesRef.current = [];
    setDepthScore(0);
    setCurrentStage('exploration');
    setTurnCount(0);
    setDigitalTwinData(null);
    setCurrentModel('flash');
    setIsJsonPanelVisible(false);
    prevModeRef.current = 'integrated';
    prevStageRef.current = 'exploration';
    isProModelActiveRef.current = false; // 모델 티어 추적 리셋
  };

  // Handle Digital Twin Extraction
  const handleExtractEssence = async () => {
    if (depthScore < 50) return;
    setIsExtracting(true);
    try {
      const jsonString = await generateDigitalTwin(profile, messagesRef.current);
      setDigitalTwinData(jsonString);
    } catch (error) {
      console.error("Extraction failed", error);
      alert("영혼 추출에 실패했습니다. 아직 분석 데이터가 부족할 수 있습니다.");
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSendMessage = async (text: string) => {
    const newUserMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newUserMsg]);
    setIsLoading(true);
    const newTurnCount = turnCount + 1;
    setTurnCount(newTurnCount);

    try {
      if (!isSessionActive) {
        // If user types without clicking start, we auto-start
        initializeChat(mode, profile, messagesRef.current, depthScore);
        setIsSessionActive(true);
      }

      // 현재 심도와 턴 카운트 전달
      const response = await sendMessageToGemini(text, depthScore, newTurnCount);

      // 심도 업데이트
      setDepthScore(response.depth);

      // 단계 변경 시 로그
      if (response.stageChanged) {
        console.log(`[App] Stage changed after message. New stage: ${getCurrentDepthStage()}`);
      }

      const newModelMsg: Message = {
        id: `model-${Date.now()}`,
        role: 'model',
        text: response.text,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, newModelMsg]);
    } catch (error) {
      console.error("Error in chat flow", error);
      setMessages((prev) => [...prev, {
        id: `error-${Date.now()}`,
        role: 'model',
        text: "통신 상태가 불안정합니다. 잠시 후 다시 시도해주세요.",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // 심도 단계에 따른 UI 색상 (6단계)
  const getStageColor = (stage: DepthStage): string => {
    switch (stage) {
      case 'exploration': return 'text-blue-400';
      case 'development': return 'text-yellow-400';
      case 'subconscious': return 'text-violet-400';
      case 'unconscious': return 'text-indigo-400';
      case 'archetypal': return 'text-purple-400';
      case 'resolution': return 'text-emerald-400';
      default: return 'text-gold-400';
    }
  };

  const getStageName = (stage: DepthStage): string => {
    switch (stage) {
      case 'exploration': return '탐색';
      case 'development': return '전개';
      case 'subconscious': return '잠재의식';
      case 'unconscious': return '무의식';
      case 'archetypal': return '원형';
      case 'resolution': return '합성';
      default: return '탐색';
    }
  };

  // 심도에 따른 배경 테마
  const getBackgroundTheme = (depth: number) => {
    if (depth < 50) {
      // 기본 다크 테마
      return {
        topLeft: 'bg-violet-900/10',
        bottomRight: 'bg-gold-600/5',
        accent: 'bg-indigo-900/10',
      };
    } else if (depth < 85) {
      // 무의식 레벨: 바이올렛/인디고
      return {
        topLeft: 'bg-violet-600/20',
        bottomRight: 'bg-indigo-600/15',
        accent: 'bg-purple-900/15',
      };
    } else {
      // 해결 단계: 에메랄드/틸
      return {
        topLeft: 'bg-emerald-500/10',
        bottomRight: 'bg-teal-950/30',
        accent: 'bg-cyan-900/10',
      };
    }
  };

  const bgTheme = getBackgroundTheme(depthScore);

  return (
    <div className="flex h-screen w-full bg-void-950 text-gray-100 overflow-hidden font-sans relative">
      {/* Global Background Ambience - 심도에 따라 동적 변경 */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden transition-all duration-1000">
        <div className={`absolute top-[-10%] left-[-10%] w-[40%] h-[40%] ${bgTheme.topLeft} rounded-full blur-[120px] transition-all duration-1000`}></div>
        <div className={`absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] ${bgTheme.bottomRight} rounded-full blur-[100px] transition-all duration-1000`}></div>
        <div className={`absolute top-[20%] right-[20%] w-[20%] h-[20%] ${bgTheme.accent} rounded-full blur-[80px] transition-all duration-1000 ${depthScore >= 50 ? 'animate-pulse-slow' : ''}`}></div>
      </div>

      {/* Sidebar / Control Panel */}
      <ControlPanel
        profile={profile}
        setProfile={setProfile}
        mode={mode}
        onModeChange={handleModeSelect}
        onStartSession={handleStartSession}
        onReset={handleReset}
        depthScore={depthScore}
        currentStage={currentStage}
        isSessionActive={isSessionActive}
        onExtractEssence={handleExtractEssence}
        isExtracting={isExtracting}
        digitalTwinData={digitalTwinData}
      />

      {/* Main Chat Area */}
      <main className={`flex-1 flex flex-col relative z-10 ${!isSessionActive ? 'hidden md:flex' : 'flex'}`}>
        {/* Header */}
        <header className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-void-950 via-void-950/80 to-transparent z-20 flex items-center justify-between px-6 pointer-events-none">
          <div className="flex items-center gap-3 text-gold-200 pointer-events-auto">
            <div className="w-8 h-8 rounded-full bg-gold-500/10 flex items-center justify-center border border-gold-500/20 shadow-[0_0_15px_rgba(212,175,55,0.15)]">
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <h1 className="font-serif font-bold text-lg tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-gold-100 to-gold-400 drop-shadow-sm">바이브 철학관</h1>
              <p className="text-[10px] text-gray-500 font-sans tracking-widest uppercase">Vibe Philosophy Agent 4.0</p>
            </div>
          </div>

          <div className="flex items-center gap-3 pointer-events-auto">
            {/* Depth Score with Stage Indicator */}
            <div className="hidden md:flex items-center gap-3 glass-panel px-4 py-1.5 rounded-full">
              <Sparkles size={14} className={depthScore >= 85 ? "text-emerald-400 animate-pulse" : "text-gold-400"} />
              <span className="text-xs text-gray-300 font-medium tracking-wide">
                <span className={getStageColor(currentStage)}>{getStageName(currentStage)}</span>
                <span className="mx-1 text-gray-600">|</span>
                <span className={depthScore >= 85 ? "text-emerald-400 font-bold" : "text-gold-200"}>{depthScore}%</span>
                {currentModel === 'pro' && (
                  <>
                    <span className="mx-1 text-gray-600">|</span>
                    <span className="text-violet-400 font-medium">Pro</span>
                  </>
                )}
              </span>
            </div>

            {/* JSON Panel Toggle Button (Desktop) */}
            {isSessionActive && (
              <button
                onClick={() => setIsJsonPanelVisible(!isJsonPanelVisible)}
                className={`hidden lg:flex w-8 h-8 rounded-full items-center justify-center border transition-all ${
                  isJsonPanelVisible
                    ? 'bg-violet-500/20 border-violet-500/40 text-violet-400'
                    : 'bg-void-800 border-void-700 text-gray-400 hover:text-white'
                }`}
                title="JSON 프로필 패널"
              >
                {isJsonPanelVisible ? <PanelRightClose size={14} /> : <PanelRightOpen size={14} />}
              </button>
            )}

            {/* Mobile Reset Button */}
            {isSessionActive && (
              <button
                onClick={handleReset}
                className="md:hidden w-8 h-8 rounded-full bg-void-800 flex items-center justify-center border border-void-700 text-gray-400 hover:text-white"
              >
                <RefreshCcw size={14} />
              </button>
            )}
          </div>
        </header>

        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
        />
      </main>

      {/* Right Panel - JSON Profile (Desktop only) */}
      <JsonProfilePanel
        messages={messages}
        depthScore={depthScore}
        currentStage={currentStage}
        currentModel={currentModel}
        turnCount={turnCount}
        profile={profile}
        isVisible={isJsonPanelVisible && isSessionActive}
        onClose={() => setIsJsonPanelVisible(false)}
      />
    </div>
  );
};

export default App;
