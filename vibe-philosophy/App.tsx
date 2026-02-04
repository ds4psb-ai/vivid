

import React, { useState, useEffect, useRef } from 'react';
import ControlPanel from './components/ControlPanel';
import ChatInterface from './components/ChatInterface';
import JsonProfilePanel from './components/JsonProfilePanel';
import { Message, UserProfile, AnalysisMode, DepthStage, VibePhilosophyPersona, INITIAL_PERSONA } from './types';
import {
  initializeChat,
  sendMessageToGemini,
  generateDigitalTwin,
  getCurrentDepthStage,
  updatePersonaState
} from './services/gemini';
import { GET_GREETING_TRIGGER, getDepthStage, calculateDepthFromFields, deepMergePersona } from './constants';
import { Sparkles, BrainCircuit, RefreshCcw, PanelRightOpen, PanelRightClose, Sun, Moon } from 'lucide-react';

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
  const [isJsonPanelVisible, setIsJsonPanelVisible] = useState(true); // 항상 표시로 변경

  // 페르소나 상태 (레거시 심연의 거울 방식)
  const [personaData, setPersonaData] = useState<VibePhilosophyPersona>(INITIAL_PERSONA);
  const [lastUpdatedFields, setLastUpdatedFields] = useState<Set<string>>(new Set());

  // 테마 상태 (라이트/다크) - 밝은 모드가 디폴트
  const [isLightMode, setIsLightMode] = useState(true);

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

  // 심도 점수 변경 시 단계 업데이트 및 모델 전환 (40% 임계값으로 변경)
  useEffect(() => {
    const newStage = getDepthStage(depthScore);
    const shouldBePro = depthScore >= 40; // 50% -> 40% 변경

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
      }

      // 단계 전환 또는 모델 업그레이드 시 채팅 세션 재초기화
      if (isSessionActive) {
        initializeChat(mode, profile, messagesRef.current, depthScore);
      }
    }
  }, [depthScore, currentStage, isSessionActive, mode, profile]);

  // Handle Session Start (Triggered from ControlPanel)
  const handleStartSession = async () => {
    setIsLoading(true);
    setIsSessionActive(true);
    setTurnCount(0);
    setMessages([]);
    messagesRef.current = [];
    setDigitalTwinData(null);
    setIsJsonPanelVisible(true); // 세션 시작부터 항상 표시

    // 페르소나 초기화 (프로필 정보 반영)
    const initialPersona: VibePhilosophyPersona = {
      ...INITIAL_PERSONA,
      meta: {
        ...INITIAL_PERSONA.meta,
        profiling_status: 'in_progress',
        current_model: 'pro', // 초기 분석은 Pro 강제
        turn_count: 0,
      },
      demographics: {
        ...INITIAL_PERSONA.demographics,
        name: profile.name || '',
        birth_date: profile.birthDate || '',
        blood_type: profile.bloodType || '',
        mbti_self_report: profile.mbti || '',
        gender: profile.gender || '',
        residence: profile.residence || '',
      },
      face_reading: {
        ...INITIAL_PERSONA.face_reading,
        raw_features: profile.faceFeatures || '',
      },
    };

    // 사주 분석이 있으면 반영
    if (profile.sajuAnalysis) {
      initialPersona.saju_analysis = {
        four_pillars: {
          year: profile.sajuAnalysis.fourPillars?.year ? { stem: profile.sajuAnalysis.fourPillars.year.stem, branch: profile.sajuAnalysis.fourPillars.year.branch } : null,
          month: profile.sajuAnalysis.fourPillars?.month ? { stem: profile.sajuAnalysis.fourPillars.month.stem, branch: profile.sajuAnalysis.fourPillars.month.branch } : null,
          day: profile.sajuAnalysis.fourPillars?.day ? { stem: profile.sajuAnalysis.fourPillars.day.stem, branch: profile.sajuAnalysis.fourPillars.day.branch } : null,
          hour: profile.sajuAnalysis.fourPillars?.hour ? { stem: profile.sajuAnalysis.fourPillars.hour.stem, branch: profile.sajuAnalysis.fourPillars.hour.branch } : null,
        },
        five_elements_balance: profile.sajuAnalysis.fiveElementsBalance || { wood: 0, fire: 0, earth: 0, metal: 0, water: 0 },
        day_master: profile.sajuAnalysis.dayMaster || '',
        day_master_strength: profile.sajuAnalysis.dayMasterStrength || '',
        ten_gods: profile.sajuAnalysis.tenGods || [],
        current_year_luck: profile.sajuAnalysis.currentYearLuck || '',
      };
    }

    setPersonaData(initialPersona);

    // 필드 기반 심도 계산
    const initialDepth = calculateDepthFromFields(initialPersona);
    setDepthScore(initialDepth);
    setCurrentStage(getDepthStage(initialDepth));

    // 초기 분석은 Pro 모델 강제
    const shouldBePro = true; // 초기 분석은 무조건 Pro
    isProModelActiveRef.current = shouldBePro;
    setCurrentModel('pro');

    try {
      // 1. Initialize Chat with current profile (Pro 모델 사용)
      initializeChat(mode, profile, [], initialDepth);

      // 2. Pro 모델로 초기 분석 및 인사 (updatePersonaState 사용)
      const { persona, response, updatedPaths } = await updatePersonaState(
        initialPersona,
        "",
        `세션 시작. 프로필 정보: ${JSON.stringify(profile)}`,
        true // isInitialConsultation = true → Pro 강제
      );

      // 페르소나 병합
      const { merged } = deepMergePersona(initialPersona, persona);
      setPersonaData(merged);
      setLastUpdatedFields(updatedPaths);

      // 필드 기반 심도 재계산
      const newDepth = calculateDepthFromFields(merged);
      setDepthScore(newDepth);

      if (response) {
        setMessages([{
          id: `init-greeting-${Date.now()}`,
          role: 'model',
          text: response,
          timestamp: new Date(),
        }]);
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
    setIsJsonPanelVisible(true); // 패널은 항상 표시 유지
    prevModeRef.current = 'integrated';
    prevStageRef.current = 'exploration';
    isProModelActiveRef.current = false;
    setPersonaData(INITIAL_PERSONA); // 페르소나 리셋
    setLastUpdatedFields(new Set()); // 업데이트 필드 리셋
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

      // 대화 기록 생성
      const conversationHistory = messagesRef.current
        .map(m => `${m.role === 'user' ? '사용자' : '도사'}: ${m.text}`)
        .join('\n');

      // 페르소나 상태 업데이트 (새 방식)
      const { persona, response, updatedPaths } = await updatePersonaState(
        personaData,
        conversationHistory,
        text,
        false // 일반 대화는 isInitialConsultation = false
      );

      // 페르소나 병합
      const { merged } = deepMergePersona(personaData, persona);
      setPersonaData(merged);
      setLastUpdatedFields(updatedPaths);

      // 필드 기반 심도 계산
      const newDepth = calculateDepthFromFields(merged);
      setDepthScore(newDepth);

      // 단계 변경 확인
      const newStage = getDepthStage(newDepth);
      if (newStage !== currentStage) {
        console.log(`[App] Stage changed after message: ${currentStage} -> ${newStage}`);
      }

      const newModelMsg: Message = {
        id: `model-${Date.now()}`,
        role: 'model',
        text: response,
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

  // 심도에 따른 배경 테마 (40%부터 변화 시작)
  const getBackgroundTheme = (depth: number) => {
    if (depth < 40) {
      // 기본 다크 테마 (0-39%)
      return {
        topLeft: 'bg-violet-900/10',
        bottomRight: 'bg-gold-600/5',
        accent: 'bg-indigo-900/10',
        particles: false,
        glow: false,
      };
    } else if (depth < 60) {
      // 40-59%: 바이올렛 각성
      return {
        topLeft: 'bg-violet-600/25',
        bottomRight: 'bg-indigo-600/20',
        accent: 'bg-purple-500/20',
        particles: true,
        glow: true,
      };
    } else if (depth < 80) {
      // 60-79%: 심연 진입 (인디고/퍼플)
      return {
        topLeft: 'bg-indigo-600/30',
        bottomRight: 'bg-violet-700/25',
        accent: 'bg-purple-600/25',
        particles: true,
        glow: true,
      };
    } else {
      // 80-100%: 에메랄드/틸 합성
      return {
        topLeft: 'bg-emerald-500/20',
        bottomRight: 'bg-teal-600/25',
        accent: 'bg-cyan-500/15',
        particles: true,
        glow: true,
      };
    }
  };

  const bgTheme = getBackgroundTheme(depthScore);

  // 라이트 모드용 배경 테마
  const getLightBackgroundTheme = (depth: number) => {
    if (depth < 40) {
      return {
        topLeft: 'bg-amber-200/40',
        bottomRight: 'bg-yellow-200/30',
        accent: 'bg-orange-200/30',
      };
    } else if (depth < 60) {
      return {
        topLeft: 'bg-violet-300/40',
        bottomRight: 'bg-purple-200/35',
        accent: 'bg-indigo-300/30',
      };
    } else if (depth < 80) {
      return {
        topLeft: 'bg-indigo-300/45',
        bottomRight: 'bg-purple-300/40',
        accent: 'bg-violet-300/35',
      };
    } else {
      return {
        topLeft: 'bg-emerald-300/40',
        bottomRight: 'bg-teal-200/35',
        accent: 'bg-cyan-300/30',
      };
    }
  };

  const lightBgTheme = getLightBackgroundTheme(depthScore);

  return (
    <div className={`flex h-screen w-full overflow-hidden font-sans relative transition-colors duration-500 ${
      isLightMode
        ? 'bg-amber-50 text-gray-800'
        : 'bg-void-950 text-gray-100'
    }`}>
      {/* Global Background Ambience - 심도에 따라 동적 변경 */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden transition-all duration-1000">
        {/* Main gradient blobs */}
        <div className={`absolute top-[-10%] left-[-10%] w-[40%] h-[40%] ${isLightMode ? lightBgTheme.topLeft : bgTheme.topLeft} rounded-full blur-[120px] transition-all duration-1000`}></div>
        <div className={`absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] ${isLightMode ? lightBgTheme.bottomRight : bgTheme.bottomRight} rounded-full blur-[100px] transition-all duration-1000`}></div>
        <div className={`absolute top-[20%] right-[20%] w-[20%] h-[20%] ${isLightMode ? lightBgTheme.accent : bgTheme.accent} rounded-full blur-[80px] transition-all duration-1000 ${depthScore >= 40 ? 'animate-pulse' : ''}`}></div>

        {/* 40% 이상: 추가 효과 */}
        {depthScore >= 40 && (
          <>
            {/* Floating orbs */}
            <div className="absolute top-[50%] left-[10%] w-[15%] h-[15%] bg-violet-500/15 rounded-full blur-[60px] animate-float-slow"></div>
            <div className="absolute top-[30%] right-[15%] w-[12%] h-[12%] bg-indigo-500/15 rounded-full blur-[50px] animate-float-slower"></div>

            {/* Subtle grid overlay */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.3)_100%)]"></div>
          </>
        )}

        {/* 60% 이상: 심연 진입 효과 */}
        {depthScore >= 60 && (
          <>
            <div className="absolute top-[60%] right-[30%] w-[20%] h-[20%] bg-purple-600/20 rounded-full blur-[70px] animate-pulse"></div>
            <div className="absolute bottom-[20%] left-[20%] w-[18%] h-[18%] bg-indigo-600/15 rounded-full blur-[60px] animate-float-slow"></div>

            {/* Vignette effect */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(0,0,0,0.4)_100%)]"></div>
          </>
        )}

        {/* 80% 이상: 합성 단계 - 에메랄드 글로우 */}
        {depthScore >= 80 && (
          <>
            <div className="absolute top-[40%] left-[40%] w-[25%] h-[25%] bg-emerald-500/20 rounded-full blur-[80px] animate-pulse"></div>
            <div className="absolute bottom-[10%] right-[40%] w-[15%] h-[15%] bg-teal-500/15 rounded-full blur-[50px] animate-float-slower"></div>
          </>
        )}
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
        isLightMode={isLightMode}
      />

      {/* Main Chat Area */}
      <main className={`flex-1 flex flex-col relative z-10 ${!isSessionActive ? 'hidden md:flex' : 'flex'}`}>
        {/* Header */}
        <header className={`absolute top-0 left-0 right-0 h-16 z-20 flex items-center justify-between px-6 pointer-events-none transition-colors duration-500 ${
          isLightMode
            ? 'bg-gradient-to-b from-amber-50 via-amber-50/80 to-transparent'
            : 'bg-gradient-to-b from-void-950 via-void-950/80 to-transparent'
        }`}>
          <div className={`flex items-center gap-3 pointer-events-auto ${isLightMode ? 'text-amber-800' : 'text-gold-200'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center border shadow-lg ${
              isLightMode
                ? 'bg-amber-100 border-amber-300'
                : 'bg-gold-500/10 border-gold-500/20 shadow-[0_0_15px_rgba(212,175,55,0.15)]'
            }`}>
              <BrainCircuit className="w-4 h-4" />
            </div>
            <div>
              <h1 className={`font-serif font-bold text-lg tracking-wider drop-shadow-sm ${
                isLightMode
                  ? 'text-amber-900'
                  : 'text-transparent bg-clip-text bg-gradient-to-r from-gold-100 to-gold-400'
              }`}>바이브 철학관</h1>
              <p className={`text-[10px] font-sans tracking-widest uppercase ${isLightMode ? 'text-amber-600' : 'text-gray-500'}`}>Vibe Philosophy Agent 4.0</p>
            </div>
          </div>

          <div className="flex items-center gap-3 pointer-events-auto">
            {/* Depth Score with Stage Indicator */}
            <div className={`hidden md:flex items-center gap-3 px-4 py-1.5 rounded-full ${
              isLightMode
                ? 'bg-white/80 border border-amber-200 shadow-sm'
                : 'glass-panel'
            }`}>
              <Sparkles size={14} className={depthScore >= 85 ? "text-emerald-500 animate-pulse" : isLightMode ? "text-amber-500" : "text-gold-400"} />
              <span className={`text-xs font-medium tracking-wide ${isLightMode ? 'text-gray-600' : 'text-gray-300'}`}>
                <span className={getStageColor(currentStage)}>{getStageName(currentStage)}</span>
                <span className={`mx-1 ${isLightMode ? 'text-gray-400' : 'text-gray-600'}`}>|</span>
                <span className={depthScore >= 85 ? "text-emerald-500 font-bold" : isLightMode ? "text-amber-700" : "text-gold-200"}>{depthScore}%</span>
                {currentModel === 'pro' && (
                  <>
                    <span className={`mx-1 ${isLightMode ? 'text-gray-400' : 'text-gray-600'}`}>|</span>
                    <span className="text-violet-500 font-medium">Pro</span>
                  </>
                )}
              </span>
            </div>

            {/* Light/Dark Mode Toggle */}
            <button
              onClick={() => setIsLightMode(!isLightMode)}
              className={`w-8 h-8 rounded-full flex items-center justify-center border transition-all ${
                isLightMode
                  ? 'bg-amber-100 border-amber-300 text-amber-600 hover:bg-amber-200'
                  : 'bg-void-800 border-void-700 text-gray-400 hover:text-white'
              }`}
              title={isLightMode ? '다크 모드로 전환' : '라이트 모드로 전환'}
            >
              {isLightMode ? <Moon size={14} /> : <Sun size={14} />}
            </button>

            {/* JSON Panel Toggle Button (Desktop) */}
            {isSessionActive && (
              <button
                onClick={() => setIsJsonPanelVisible(!isJsonPanelVisible)}
                className={`hidden lg:flex w-8 h-8 rounded-full items-center justify-center border transition-all ${
                  isJsonPanelVisible
                    ? 'bg-violet-500/20 border-violet-500/40 text-violet-400'
                    : isLightMode
                      ? 'bg-white border-gray-300 text-gray-500 hover:text-gray-800'
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
          isLightMode={isLightMode}
        />
      </main>

      {/* Right Panel - JSON Profile (Desktop only, 항상 표시) */}
      <JsonProfilePanel
        messages={messages}
        depthScore={depthScore}
        currentStage={currentStage}
        currentModel={currentModel}
        turnCount={turnCount}
        profile={profile}
        personaData={personaData}
        lastUpdatedFields={lastUpdatedFields}
        isVisible={isJsonPanelVisible}
        onClose={() => setIsJsonPanelVisible(false)}
        isLightMode={isLightMode}
      />
    </div>
  );
};

export default App;
