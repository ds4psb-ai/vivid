

import React, { useState } from 'react';
import { UserProfile, AnalysisMode, CalendarType, DepthStage } from '../types';
import { Settings, User, ScrollText, Dna, Activity, ScanFace, Brain, Heart, Upload, CheckCircle, Loader2, Play, Sparkles, MapPin, Clock } from 'lucide-react';
import { extractFaceFeatures, extractStructuredFaceReading } from '../services/gemini';

interface ControlPanelProps {
  profile: UserProfile;
  setProfile: (p: UserProfile) => void;
  mode: AnalysisMode;
  onModeChange: (m: AnalysisMode) => void;
  onStartSession: () => void;
  onReset: () => void;
  depthScore: number;
  currentStage: DepthStage;
  isSessionActive: boolean;
  isLightMode?: boolean;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  profile, setProfile, mode, onModeChange, onStartSession, onReset, depthScore, currentStage, isSessionActive,
  isLightMode = false
}) => {
  const [isAnalyzingPartner, setIsAnalyzingPartner] = useState(false);
  const [isAnalyzingUser, setIsAnalyzingUser] = useState(false);
  const [isDraggingUser, setIsDraggingUser] = useState(false);
  const [isDraggingPartner, setIsDraggingPartner] = useState(false);

  // 동적 input 클래스
  const inputClass = isLightMode
    ? 'light-input rounded-lg px-4 py-3 text-sm focus:outline-none'
    : 'glass-input rounded-lg px-4 py-3 text-sm focus:outline-none';

  const selectClass = isLightMode
    ? 'light-input rounded-lg px-3 py-3 text-sm focus:outline-none appearance-none'
    : 'glass-input rounded-lg px-3 py-3 text-sm focus:outline-none appearance-none';

  const labelClass = isLightMode ? 'text-amber-700' : 'text-gray-500';

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile({ ...profile, [name]: value });
  };

  const handleCalendarChange = (type: CalendarType) => {
    setProfile({ ...profile, calendarType: type });
  };

  const handlePartnerCalendarChange = (type: CalendarType) => {
    setProfile({
      ...profile,
      partner: {
        ...(profile.partner || {
          name: '', birthDate: '', calendarType: 'solar', birthTime: '', birthPlace: '', bloodType: '', mbti: '', gender: 'other'
        }),
        calendarType: type
      }
    });
  };

  const handlePartnerChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setProfile({
      ...profile,
      partner: {
        ...(profile.partner || {
          name: '', birthDate: '', calendarType: 'solar', birthTime: '', birthPlace: '', bloodType: '', mbti: '', gender: 'other'
        }),
        [name]: value
      }
    });
  };

  // --- Image Upload Handlers ---

  const processUserImage = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드 가능합니다.');
      return;
    }
    setIsAnalyzingUser(true);
    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64 = reader.result as string;
      try {
        // 텍스트 설명 + 구조화된 관상 분석 동시 호출
        const [features, structuredReading] = await Promise.all([
          extractFaceFeatures(base64),
          extractStructuredFaceReading(base64)
        ]);

        setProfile(prev => ({
          ...prev,
          faceFeatures: features,
          structuredFaceReading: structuredReading || undefined,
        }));
      } catch (error) {
        console.error("User Face Analysis Failed", error);
        alert("관상 분석에 실패했습니다.");
      } finally {
        setIsAnalyzingUser(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleUserImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processUserImage(file);
  };

  const handleUserDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDraggingUser(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processUserImage(file);
  };

  const processPartnerImage = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('이미지 파일만 업로드 가능합니다.');
      return;
    }
    setIsAnalyzingPartner(true);
    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64 = reader.result as string;
      try {
        const features = await extractFaceFeatures(base64);
        // 함수형 업데이트로 최신 상태 보장 (클로저 문제 해결)
        setProfile(prev => ({
          ...prev,
          partner: {
            ...(prev.partner || {
              name: '', birthDate: '', calendarType: 'solar', birthTime: '', birthPlace: '', bloodType: '', mbti: '', gender: 'other'
            }),
            faceFeatures: features
          }
        }));
      } catch (error) {
        console.error("Partner Face Analysis Failed", error);
        alert("상대방 관상 분석에 실패했습니다.");
      } finally {
        setIsAnalyzingPartner(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handlePartnerImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processPartnerImage(file);
  };

  const handlePartnerDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDraggingPartner(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processPartnerImage(file);
  };

  const modes: { id: AnalysisMode; label: string; icon: React.ReactNode }[] = [
    { id: 'integrated', label: '통합 심층 분석', icon: <Brain size={18} /> },
    { id: 'couple', label: '커플 궁합', icon: <Heart size={18} /> },
    { id: 'face', label: '관상학 분석', icon: <ScanFace size={18} /> },
    { id: 'blood', label: '혈액형 심리', icon: <Dna size={18} /> },
    { id: 'mbti', label: 'MBTI 인지구조', icon: <Activity size={18} /> },
    { id: 'saju', label: '사주명리 운세', icon: <ScrollText size={18} /> },
  ];

  const SectionHeader = ({ icon: Icon, title }: { icon: any, title: string }) => (
    <div className={`flex items-center gap-2 border-b pb-2 mb-4 ${
      isLightMode
        ? 'text-amber-700 border-amber-200'
        : 'text-gray-400 border-void-800'
    }`}>
      <Icon size={18} className={isLightMode ? 'text-amber-500' : 'text-gold-500/70'} />
      <h3 className={`font-bold text-sm tracking-wide ${isLightMode ? 'text-amber-800' : 'text-gray-300'}`}>{title}</h3>
    </div>
  );

  // 심도 단계에 따른 색상 (6단계)
  const getStageColor = (stage: DepthStage): string => {
    switch (stage) {
      case 'exploration': return 'from-blue-500 to-blue-600';
      case 'development': return 'from-yellow-500 to-orange-500';
      case 'subconscious': return 'from-violet-500 to-violet-600';
      case 'unconscious': return 'from-indigo-500 to-indigo-600';
      case 'archetypal': return 'from-purple-500 to-purple-600';
      case 'resolution': return 'from-emerald-500 to-teal-500';
      default: return 'from-gold-500 to-gold-600';
    }
  };

  const getStageName = (stage: DepthStage): string => {
    switch (stage) {
      case 'exploration': return '탐색 단계';
      case 'development': return '전개 단계';
      case 'subconscious': return '잠재의식 단계';
      case 'unconscious': return '무의식 단계';
      case 'archetypal': return '원형 통합 단계';
      case 'resolution': return '최종 합성 단계';
      default: return '탐색 단계';
    }
  };

  const getStageDescription = (stage: DepthStage): string => {
    switch (stage) {
      case 'exploration': return '라포 형성 중...';
      case 'development': return '표면 고민 확인 중...';
      case 'subconscious': return '잠재의식 패턴 탐색 중...';
      case 'unconscious': return '그림자 분석 중...';
      case 'archetypal': return '원형 통합 작업 중...';
      case 'resolution': return '최종 솔루션 합성!';
      default: return '라포 형성 중...';
    }
  };

  return (
    <div className={`w-full md:w-96 flex-shrink-0 flex flex-col h-full backdrop-blur-xl overflow-y-auto p-6 z-20 scrollbar-hide transition-colors duration-500 ${isSessionActive ? 'hidden md:flex' : 'flex'} ${
      isLightMode
        ? 'bg-white/90 border-r border-amber-200'
        : 'bg-void-950/90 border-r border-void-800'
    }`}>

      <div className={`flex items-center gap-3 mb-8 mt-2 ${isLightMode ? 'text-amber-600' : 'text-gold-400/80'}`}>
        <Settings className="w-6 h-6" />
        <h2 className="text-lg font-bold tracking-wide">설정 패널</h2>
      </div>

      {/* Depth Score with Stage - Visible only when session active */}
      {isSessionActive && (
        <div className="mb-10 relative group">
          <div className={`absolute -inset-0.5 bg-gradient-to-r ${getStageColor(currentStage)} rounded-xl opacity-30 blur transition duration-500 group-hover:opacity-50`}></div>
          <div className={`relative p-5 rounded-xl border overflow-hidden ${
              isLightMode
                ? 'bg-white border-amber-200'
                : 'bg-void-900 border-void-700/50'
            }`}>
            <div className="flex justify-between items-start mb-3 relative z-10">
              <div>
                <span className={`text-xs font-bold uppercase tracking-widest bg-gradient-to-r ${getStageColor(currentStage)} bg-clip-text text-transparent flex items-center gap-1`}>
                  <Sparkles size={12} /> {getStageName(currentStage)}
                </span>
                <p className={`text-xs mt-1 ${isLightMode ? 'text-amber-600' : 'text-gray-500'}`}>{getStageDescription(currentStage)}</p>
              </div>
              <span className={`text-4xl font-serif font-bold ${isLightMode ? 'text-amber-900' : 'text-gray-100'}`}>{depthScore}<span className={`text-base font-sans font-light ml-0.5 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>%</span></span>
            </div>

            <div className={`w-full h-3 rounded-full overflow-hidden relative z-10 border ${
              isLightMode ? 'bg-amber-100 border-amber-200' : 'bg-void-950 border-void-800'
            }`}>
              {/* 단계별 구간 표시 (6단계) */}
              <div className="absolute inset-0 flex">
                <div className="w-[25%] border-r border-void-700/50"></div>
                <div className="w-[20%] border-r border-void-700/50"></div>
                <div className="w-[20%] border-r border-void-700/50"></div>
                <div className="w-[20%] border-r border-void-700/50"></div>
                <div className="w-[10%] border-r border-void-700/50"></div>
                <div className="w-[5%]"></div>
              </div>
              <div
                className={`h-full transition-all duration-1000 ease-out bg-gradient-to-r ${getStageColor(currentStage)} shadow-[0_0_10px_currentColor]`}
                style={{ width: `${Math.min(depthScore, 100)}%` }}
              ></div>
            </div>
            <div className={`flex justify-between mt-2 text-[10px] ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>
              <span>탐색</span>
              <span>전개</span>
              <span>잠재</span>
              <span>무의식</span>
              <span>원형</span>
              <span>합성</span>
            </div>
          </div>
        </div>
      )}

      {/* User Profile Section */}
      <div className="mb-8 space-y-5">
        <SectionHeader icon={User} title="내 정보" />

        <div className="space-y-4">
          {/* User Face Upload */}
          <div className="mb-4">
            <label className={`block text-xs ${labelClass} mb-2 ml-1`}>본인 관상 사진</label>
            {isAnalyzingUser ? (
              <div className="w-full h-20 rounded-lg bg-gold-500/10 flex items-center justify-center border border-gold-500/30">
                <Loader2 className="animate-spin text-gold-400" size={20} />
                <span className="ml-2 text-sm text-gold-200">얼굴 분석 중...</span>
              </div>
            ) : profile.faceFeatures ? (
              <div className="w-full p-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle size={20} className="text-emerald-400" />
                  <span className="text-sm text-emerald-200">관상 데이터 확보됨</span>
                </div>
                <label className="cursor-pointer text-xs underline text-emerald-400 hover:text-emerald-300">
                  재업로드
                  <input type="file" accept="image/*" className="hidden" onChange={handleUserImageUpload} />
                </label>
              </div>
            ) : (
              <label
                className={`w-full h-24 rounded-lg border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all group ${isDraggingUser
                    ? 'border-gold-400 bg-gold-500/20 scale-[1.02]'
                    : 'border-gold-500/30 hover:bg-gold-500/5 hover:border-gold-500/50'
                  }`}
                onDragOver={(e) => { e.preventDefault(); setIsDraggingUser(true); }}
                onDragEnter={(e) => { e.preventDefault(); setIsDraggingUser(true); }}
                onDragLeave={() => setIsDraggingUser(false)}
                onDrop={handleUserDrop}
              >
                <Upload size={20} className={`mb-1 transition-all ${isDraggingUser ? 'text-gold-400 scale-110' : 'text-gold-400/50 group-hover:text-gold-400'}`} />
                <span className={`text-xs transition-all ${isDraggingUser ? 'text-gold-300' : 'text-gold-300/70 group-hover:text-gold-200'}`}>
                  {isDraggingUser ? '여기에 놓으세요!' : '클릭 또는 드래그 앤 드롭'}
                </span>
                <input type="file" accept="image/*" className="hidden" onChange={handleUserImageUpload} />
              </label>
            )}
          </div>

          <div>
            <label className={`block text-xs mb-2 ml-1 ${labelClass}`}>이름</label>
            <input
              type="text"
              name="name"
              value={profile.name}
              onChange={handleProfileChange}
              className={`w-full ${inputClass}`}
            />
          </div>

          <div>
            <label className={`block text-xs ${labelClass} mb-2 ml-1`}>생년월일 (사주 필수)</label>
            <div className="flex flex-col gap-2">
              <div className={`flex rounded-lg p-1 border w-full ${
                  isLightMode ? 'bg-amber-50 border-amber-200' : 'bg-void-900/50 border-void-700/50'
                }`}>
                <button
                  onClick={() => handleCalendarChange('solar')}
                  className={`flex-1 py-2 rounded-md text-xs font-bold transition-all ${profile.calendarType === 'solar'
                    ? isLightMode ? 'bg-amber-500 text-white shadow-sm' : 'bg-gold-500 text-void-950 shadow-sm'
                    : isLightMode ? 'text-amber-400 hover:text-amber-600' : 'text-gray-500 hover:text-gray-300'
                    }`}
                >
                  양력
                </button>
                <button
                  onClick={() => handleCalendarChange('lunar')}
                  className={`flex-1 py-2 rounded-md text-xs font-bold transition-all ${profile.calendarType === 'lunar'
                    ? 'bg-violet-500 text-white shadow-sm'
                    : isLightMode ? 'text-amber-400 hover:text-amber-600' : 'text-gray-500 hover:text-gray-300'
                    }`}
                >
                  음력
                </button>
              </div>
              <div className="flex gap-2">
                <select
                  value={profile.birthDate ? profile.birthDate.split('-')[0] : ''}
                  onChange={(e) => {
                    const year = e.target.value;
                    const month = profile.birthDate?.split('-')[1] || '01';
                    const day = profile.birthDate?.split('-')[2] || '01';
                    setProfile({ ...profile, birthDate: year ? `${year}-${month}-${day}` : '' });
                  }}
                  className={`flex-[1.2] ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-2 py-3 text-sm focus:outline-none appearance-none text-center`}
                >
                  <option value="">년도</option>
                  {Array.from({ length: 80 }, (_, i) => 2010 - i).map((y) => (
                    <option key={y} value={y} className={isLightMode ? 'bg-white' : 'bg-void-900'}>{y}년</option>
                  ))}
                </select>
                <select
                  value={profile.birthDate ? profile.birthDate.split('-')[1] : ''}
                  onChange={(e) => {
                    const year = profile.birthDate?.split('-')[0] || '1990';
                    const month = e.target.value;
                    const day = profile.birthDate?.split('-')[2] || '01';
                    setProfile({ ...profile, birthDate: month ? `${year}-${month}-${day}` : '' });
                  }}
                  className={`flex-1 ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-2 py-3 text-sm focus:outline-none appearance-none text-center`}
                >
                  <option value="">월</option>
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={String(m).padStart(2, '0')} className={isLightMode ? 'bg-white' : 'bg-void-900'}>{m}월</option>
                  ))}
                </select>
                <select
                  value={profile.birthDate ? profile.birthDate.split('-')[2] : ''}
                  onChange={(e) => {
                    const year = profile.birthDate?.split('-')[0] || '1990';
                    const month = profile.birthDate?.split('-')[1] || '01';
                    const day = e.target.value;
                    setProfile({ ...profile, birthDate: day ? `${year}-${month}-${day}` : '' });
                  }}
                  className={`flex-1 ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-2 py-3 text-sm focus:outline-none appearance-none text-center`}
                >
                  <option value="">일</option>
                  {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                    <option key={d} value={String(d).padStart(2, '0')} className={isLightMode ? 'bg-white' : 'bg-void-900'}>{d}일</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1 flex items-center gap-1`}>
                <Clock size={12} /> 태어난 시간
              </label>
              <div className="flex gap-1">
                <select
                  name="birthTimeHour"
                  value={profile.birthTime ? profile.birthTime.split(':')[0] : ''}
                  onChange={(e) => {
                    const hour = e.target.value;
                    const min = profile.birthTime?.split(':')[1] || '00';
                    setProfile({ ...profile, birthTime: hour ? `${hour}:${min}` : '' });
                  }}
                  className={`flex-1 ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-1 py-3 text-sm focus:outline-none appearance-none text-center`}
                >
                  <option value="">시</option>
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={String(i).padStart(2, '0')} className={isLightMode ? 'bg-white' : 'bg-void-900'}>
                      {i}시
                    </option>
                  ))}
                </select>
                <select
                  name="birthTimeMin"
                  value={profile.birthTime ? profile.birthTime.split(':')[1] : ''}
                  onChange={(e) => {
                    const hour = profile.birthTime?.split(':')[0] || '00';
                    const min = e.target.value;
                    setProfile({ ...profile, birthTime: min ? `${hour}:${min}` : '' });
                  }}
                  className={`flex-1 ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-1 py-3 text-sm focus:outline-none appearance-none text-center`}
                >
                  <option value="">분</option>
                  {Array.from({ length: 60 }, (_, i) => i).map((m) => (
                    <option key={m} value={String(m).padStart(2, '0')} className={isLightMode ? 'bg-white' : 'bg-void-900'}>
                      {m}분
                    </option>
                  ))}
                </select>
              </div>
              <span className="text-[10px] text-gray-600 ml-1">모르면 비워두세요</span>
            </div>
            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1 flex items-center gap-1`}>
                <MapPin size={12} /> 출생지
              </label>
              <input
                type="text"
                name="birthPlace"
                value={profile.birthPlace}
                onChange={handleProfileChange}
                placeholder="예: 서울"
                className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-3 py-3 text-sm focus:outline-none`}
              />
            </div>
          </div>

          <div>
            <label className={`block text-xs ${labelClass} mb-2 ml-1 flex items-center gap-1`}>
              <MapPin size={12} /> 현재 거주지
            </label>
            <input
              type="text"
              name="residence"
              value={profile.residence}
              onChange={handleProfileChange}
              placeholder="예: 서울 강남구"
              className={`w-full ${inputClass}`}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1`}>혈액형</label>
              <select
                name="bloodType"
                value={profile.bloodType}
                onChange={handleProfileChange}
                className={`w-full ${selectClass}`}
              >
                <option value="">선택</option>
                <option value="A" className={isLightMode ? 'bg-white' : 'bg-void-900'}>A형</option>
                <option value="B" className={isLightMode ? 'bg-white' : 'bg-void-900'}>B형</option>
                <option value="O" className={isLightMode ? 'bg-white' : 'bg-void-900'}>O형</option>
                <option value="AB" className={isLightMode ? 'bg-white' : 'bg-void-900'}>AB형</option>
              </select>
            </div>
            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1`}>MBTI</label>
              <input
                type="text"
                name="mbti"
                value={profile.mbti}
                onChange={handleProfileChange}
                placeholder="예: INFP"
                className={`w-full ${inputClass} uppercase`}
              />
            </div>
          </div>

          <div>
            <label className={`block text-xs ${labelClass} mb-2 ml-1`}>성별</label>
            <select
              name="gender"
              value={profile.gender}
              onChange={handleProfileChange}
              className={`w-full ${selectClass}`}
            >
              <option value="male" className={isLightMode ? 'bg-white' : 'bg-void-900'}>남성</option>
              <option value="female" className={isLightMode ? 'bg-white' : 'bg-void-900'}>여성</option>
              <option value="other" className={isLightMode ? 'bg-white' : 'bg-void-900'}>기타</option>
            </select>
          </div>
        </div>
      </div>

      {/* Partner Profile Section */}
      {mode === 'couple' && (
        <div className="mb-8 space-y-5 animate-fadeIn">
          <SectionHeader icon={Heart} title="상대방 정보" />

          <div className="space-y-4 bg-pink-900/10 p-4 rounded-xl border border-pink-500/10">

            {/* Partner Face Upload */}
            <div className="mb-4">
              <label className="block text-xs text-pink-300 mb-2 ml-1">상대방 관상 사진</label>
              {isAnalyzingPartner ? (
                <div className="w-full h-20 rounded-lg bg-pink-500/10 flex items-center justify-center border border-pink-500/30">
                  <Loader2 className="animate-spin text-pink-400" size={20} />
                  <span className="ml-2 text-sm text-pink-200">분석 중...</span>
                </div>
              ) : profile.partner?.faceFeatures ? (
                <div className="w-full p-4 rounded-lg border border-pink-500/30 bg-pink-500/10 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={20} className="text-pink-400" />
                    <span className="text-sm text-pink-200">데이터 확보됨</span>
                  </div>
                  <label className="cursor-pointer text-xs underline text-pink-400 hover:text-pink-300">
                    재업로드
                    <input type="file" accept="image/*" className="hidden" onChange={handlePartnerImageUpload} />
                  </label>
                </div>
              ) : (
                <label
                  className={`w-full h-24 rounded-lg border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all group ${isDraggingPartner
                      ? 'border-pink-400 bg-pink-500/20 scale-[1.02]'
                      : 'border-pink-500/30 hover:bg-pink-500/5 hover:border-pink-500/50'
                    }`}
                  onDragOver={(e) => { e.preventDefault(); setIsDraggingPartner(true); }}
                  onDragEnter={(e) => { e.preventDefault(); setIsDraggingPartner(true); }}
                  onDragLeave={() => setIsDraggingPartner(false)}
                  onDrop={handlePartnerDrop}
                >
                  <Upload size={20} className={`mb-1 transition-all ${isDraggingPartner ? 'text-pink-400 scale-110' : 'text-pink-400/50 group-hover:text-pink-400'}`} />
                  <span className={`text-xs transition-all ${isDraggingPartner ? 'text-pink-300' : 'text-pink-300/70 group-hover:text-pink-200'}`}>
                    {isDraggingPartner ? '여기에 놓으세요!' : '클릭 또는 드래그 앤 드롭'}
                  </span>
                  <input type="file" accept="image/*" className="hidden" onChange={handlePartnerImageUpload} />
                </label>
              )}
            </div>

            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1`}>이름</label>
              <input
                type="text"
                name="name"
                value={profile.partner?.name || ''}
                onChange={handlePartnerChange}
                className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-4 py-3 text-sm focus:outline-none border-pink-500/20 focus:border-pink-500`}
              />
            </div>

            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1`}>생년월일</label>
              <div className="flex flex-col gap-2">
                <div className="flex bg-void-900/50 rounded-lg p-1 border border-pink-500/20 w-full">
                  <button
                    onClick={() => handlePartnerCalendarChange('solar')}
                    className={`flex-1 py-2 rounded-md text-xs font-bold transition-all ${profile.partner?.calendarType === 'solar'
                      ? 'bg-pink-500 text-white shadow-sm'
                      : isLightMode ? 'text-amber-400 hover:text-amber-600' : 'text-gray-500 hover:text-gray-300'
                      }`}
                  >
                    양력
                  </button>
                  <button
                    onClick={() => handlePartnerCalendarChange('lunar')}
                    className={`flex-1 py-2 rounded-md text-xs font-bold transition-all ${profile.partner?.calendarType === 'lunar'
                      ? 'bg-violet-500 text-white shadow-sm'
                      : isLightMode ? 'text-amber-400 hover:text-amber-600' : 'text-gray-500 hover:text-gray-300'
                      }`}
                  >
                    음력
                  </button>
                </div>
                <input
                  type="date"
                  name="birthDate"
                  value={profile.partner?.birthDate || ''}
                  onChange={handlePartnerChange}
                  className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-3 py-3 text-sm focus:outline-none border-pink-500/20 focus:border-pink-500`}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={`block text-xs ${labelClass} mb-2 ml-1`}>태어난 시간</label>
                <input
                  type="time"
                  name="birthTime"
                  value={profile.partner?.birthTime || ''}
                  onChange={handlePartnerChange}
                  className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-3 py-3 text-sm focus:outline-none border-pink-500/20 focus:border-pink-500`}
                />
              </div>
              <div>
                <label className={`block text-xs ${labelClass} mb-2 ml-1`}>출생지</label>
                <input
                  type="text"
                  name="birthPlace"
                  value={profile.partner?.birthPlace || ''}
                  onChange={handlePartnerChange}
                  placeholder="예: 대전"
                  className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-3 py-3 text-sm focus:outline-none border-pink-500/20 focus:border-pink-500`}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={`block text-xs ${labelClass} mb-2 ml-1`}>성별</label>
                <select
                  name="gender"
                  value={profile.partner?.gender || 'other'}
                  onChange={handlePartnerChange}
                  className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-3 py-3 text-sm focus:outline-none appearance-none border-pink-500/20 focus:border-pink-500`}
                >
                  <option value="male" className={isLightMode ? 'bg-white' : 'bg-void-900'}>남성</option>
                  <option value="female" className={isLightMode ? 'bg-white' : 'bg-void-900'}>여성</option>
                  <option value="other" className={isLightMode ? 'bg-white' : 'bg-void-900'}>기타</option>
                </select>
              </div>
              <div>
                <label className={`block text-xs ${labelClass} mb-2 ml-1`}>MBTI</label>
                <input
                  type="text"
                  name="mbti"
                  value={profile.partner?.mbti || ''}
                  onChange={handlePartnerChange}
                  placeholder="예: ENFJ"
                  className={`w-full ${inputClass} uppercase border-pink-500/20 focus:border-pink-500`}
                />
              </div>
            </div>

            <div>
              <label className={`block text-xs ${labelClass} mb-2 ml-1`}>혈액형</label>
              <select
                name="bloodType"
                value={profile.partner?.bloodType || ''}
                onChange={handlePartnerChange}
                className={`w-full ${isLightMode ? 'light-input' : 'glass-input'} rounded-lg px-3 py-3 text-sm focus:outline-none appearance-none border-pink-500/20 focus:border-pink-500`}
              >
                <option value="">선택</option>
                <option value="A" className={isLightMode ? 'bg-white' : 'bg-void-900'}>A형</option>
                <option value="B" className={isLightMode ? 'bg-white' : 'bg-void-900'}>B형</option>
                <option value="O" className={isLightMode ? 'bg-white' : 'bg-void-900'}>O형</option>
                <option value="AB" className={isLightMode ? 'bg-white' : 'bg-void-900'}>AB형</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* START BUTTON - 분석 렌즈 위에 배치 */}
      <div className="mb-6 space-y-3 pt-4 border-t border-void-800">
        {/* START BUTTON */}
        <button
          onClick={onStartSession}
          disabled={isAnalyzingUser || isAnalyzingPartner}
          className={`w-full py-5 rounded-xl flex items-center justify-center gap-3 font-bold tracking-wide text-base transition-all duration-500 shadow-lg ${isSessionActive
            ? isLightMode
              ? 'bg-amber-100 border border-amber-400 text-amber-700 hover:bg-amber-200'
              : 'bg-void-800 border border-gold-500/30 text-gold-400 hover:bg-gold-500/10'
            : isLightMode
              ? 'bg-gradient-to-r from-amber-500 to-amber-400 text-white hover:from-amber-400 hover:to-amber-300 shadow-[0_0_20px_rgba(245,158,11,0.3)]'
              : 'bg-gradient-to-r from-gold-600 to-gold-400 text-void-950 hover:from-gold-500 hover:to-gold-300 shadow-[0_0_20px_rgba(212,175,55,0.2)]'
            }`}
        >
          <Play size={16} fill="currentColor" />
          {isSessionActive ? "분석 업데이트" : "상담 시작하기"}
        </button>

        {isSessionActive && (
          <button
            onClick={onReset}
            className={`w-full py-3 rounded-xl transition-all text-sm tracking-wide font-medium ${
              isLightMode
                ? 'text-amber-500 hover:text-red-500 hover:bg-red-50'
                : 'text-gray-500 hover:text-red-400 hover:bg-red-500/5'
            }`}
          >
            초기화
          </button>
        )}
      </div>

      {/* Mode Selection */}
      <div className="mb-8 space-y-4">
        <SectionHeader icon={Activity} title="분석 렌즈" />
        <div className="grid grid-cols-1 gap-2 pt-1">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => onModeChange(m.id)}
              className={`flex items-center gap-3 px-4 py-4 rounded-xl text-sm transition-all duration-300 font-medium border ${mode === m.id
                ? isLightMode
                  ? 'bg-amber-100 border-amber-400 text-amber-800 shadow-[0_0_15px_rgba(245,158,11,0.1)]'
                  : 'bg-void-800 border-gold-500/40 text-gold-200 shadow-[0_0_15px_rgba(212,175,55,0.1)]'
                : isLightMode
                  ? 'bg-transparent border-transparent text-amber-500 hover:bg-amber-50 hover:text-amber-700'
                  : 'bg-transparent border-transparent text-gray-500 hover:bg-void-800 hover:text-gray-300'
                }`}
            >
              <span className={mode === m.id
                  ? isLightMode ? 'text-amber-600' : 'text-gold-400'
                  : isLightMode ? 'text-amber-400' : 'text-gray-600'
                }>{m.icon}</span>
              {m.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
