

import React, { useState } from 'react';
import { UserProfile, AnalysisMode, CalendarType, DepthStage } from '../types';
import { Settings, User, ScrollText, Dna, Activity, ScanFace, Brain, Heart, Upload, CheckCircle, Loader2, Play, Sparkles, Fingerprint, Download, MapPin, Clock } from 'lucide-react';
import { extractFaceFeatures } from '../services/gemini';

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
  onExtractEssence?: () => void;
  isExtracting?: boolean;
  digitalTwinData?: string | null;
}

const ControlPanel: React.FC<ControlPanelProps> = ({
  profile, setProfile, mode, onModeChange, onStartSession, onReset, depthScore, currentStage, isSessionActive,
  onExtractEssence, isExtracting, digitalTwinData
}) => {
  const [isAnalyzingPartner, setIsAnalyzingPartner] = useState(false);
  const [isAnalyzingUser, setIsAnalyzingUser] = useState(false);
  const [isDraggingUser, setIsDraggingUser] = useState(false);
  const [isDraggingPartner, setIsDraggingPartner] = useState(false);

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

  const handleDownloadJson = () => {
    if (!digitalTwinData) return;
    const blob = new Blob([digitalTwinData], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `vibe_soul_${profile.name || 'user'}_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
        const features = await extractFaceFeatures(base64);
        setProfile({
          ...profile,
          faceFeatures: features,
        });
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
        setProfile({
          ...profile,
          partner: {
            ...(profile.partner || {
              name: '', birthDate: '', calendarType: 'solar', birthTime: '', birthPlace: '', bloodType: '', mbti: '', gender: 'other'
            }),
            faceFeatures: features
          }
        });
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
    { id: 'integrated', label: '통합 심층 분석', icon: <Brain size={15} /> },
    { id: 'couple', label: '커플 궁합 (New)', icon: <Heart size={15} /> },
    { id: 'face', label: '관상학 분석', icon: <ScanFace size={15} /> },
    { id: 'blood', label: '혈액형 심리', icon: <Dna size={15} /> },
    { id: 'mbti', label: 'MBTI 인지구조', icon: <Activity size={15} /> },
    { id: 'saju', label: '사주명리 운세', icon: <ScrollText size={15} /> },
  ];

  const SectionHeader = ({ icon: Icon, title }: { icon: any, title: string }) => (
    <div className="flex items-center gap-2 text-gray-400 border-b border-void-800 pb-2 mb-3">
      <Icon size={14} className="text-gold-500/70" />
      <h3 className="font-bold text-[10px] uppercase tracking-widest text-gray-400">{title}</h3>
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
    <div className={`w-full md:w-80 flex-shrink-0 flex flex-col h-full bg-void-950/90 backdrop-blur-xl border-r border-void-800 overflow-y-auto p-5 z-20 scrollbar-hide ${isSessionActive ? 'hidden md:flex' : 'flex'}`}>

      <div className="flex items-center gap-2 mb-8 mt-2 text-gold-400/80">
        <Settings className="w-5 h-5" />
        <h2 className="text-sm font-bold tracking-[0.2em] uppercase">Control Center</h2>
      </div>

      {/* Depth Score with Stage - Visible only when session active */}
      {isSessionActive && (
        <div className="mb-10 relative group">
          <div className={`absolute -inset-0.5 bg-gradient-to-r ${getStageColor(currentStage)} rounded-xl opacity-30 blur transition duration-500 group-hover:opacity-50`}></div>
          <div className="relative bg-void-900 p-5 rounded-xl border border-void-700/50 overflow-hidden">
            <div className="flex justify-between items-start mb-3 relative z-10">
              <div>
                <span className={`text-[10px] font-bold uppercase tracking-widest bg-gradient-to-r ${getStageColor(currentStage)} bg-clip-text text-transparent flex items-center gap-1`}>
                  <Sparkles size={10} /> {getStageName(currentStage)}
                </span>
                <p className="text-[9px] text-gray-500 mt-1">{getStageDescription(currentStage)}</p>
              </div>
              <span className="text-3xl font-serif font-bold text-gray-100">{depthScore}<span className="text-sm font-sans font-light text-gray-600 ml-0.5">%</span></span>
            </div>

            <div className="w-full bg-void-950 h-2 rounded-full overflow-hidden relative z-10 border border-void-800">
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
            <div className="flex justify-between mt-1 text-[7px] text-gray-600">
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
        <SectionHeader icon={User} title="Client Profile (본인)" />

        <div className="space-y-3">
          {/* User Face Upload */}
          <div className="mb-4">
            <label className="block text-[10px] text-gray-500 mb-2 ml-1">본인 관상 사진</label>
            {isAnalyzingUser ? (
              <div className="w-full h-16 rounded-lg bg-gold-500/10 flex items-center justify-center border border-gold-500/30">
                <Loader2 className="animate-spin text-gold-400" size={16} />
                <span className="ml-2 text-xs text-gold-200">얼굴 분석 중...</span>
              </div>
            ) : profile.faceFeatures ? (
              <div className="w-full p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle size={16} className="text-emerald-400" />
                  <span className="text-xs text-emerald-200">관상 데이터 확보됨</span>
                </div>
                <label className="cursor-pointer text-[10px] underline text-emerald-400 hover:text-emerald-300">
                  재업로드
                  <input type="file" accept="image/*" className="hidden" onChange={handleUserImageUpload} />
                </label>
              </div>
            ) : (
              <label
                className={`w-full h-20 rounded-lg border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all group ${isDraggingUser
                    ? 'border-gold-400 bg-gold-500/20 scale-[1.02]'
                    : 'border-gold-500/30 hover:bg-gold-500/5 hover:border-gold-500/50'
                  }`}
                onDragOver={(e) => { e.preventDefault(); setIsDraggingUser(true); }}
                onDragEnter={(e) => { e.preventDefault(); setIsDraggingUser(true); }}
                onDragLeave={() => setIsDraggingUser(false)}
                onDrop={handleUserDrop}
              >
                <Upload size={16} className={`mb-1 transition-all ${isDraggingUser ? 'text-gold-400 scale-110' : 'text-gold-400/50 group-hover:text-gold-400'}`} />
                <span className={`text-[10px] transition-all ${isDraggingUser ? 'text-gold-300' : 'text-gold-300/70 group-hover:text-gold-200'}`}>
                  {isDraggingUser ? '여기에 놓으세요!' : '클릭 또는 드래그 앤 드롭'}
                </span>
                <input type="file" accept="image/*" className="hidden" onChange={handleUserImageUpload} />
              </label>
            )}
          </div>

          <div>
            <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">이름</label>
            <input
              type="text"
              name="name"
              value={profile.name}
              onChange={handleProfileChange}
              className="w-full glass-input rounded-md px-3 py-2.5 text-xs focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">생년월일 (사주 필수)</label>
            <div className="flex flex-col gap-2">
              <div className="flex bg-void-900/50 rounded-md p-1 border border-void-700/50 w-full">
                <button
                  onClick={() => handleCalendarChange('solar')}
                  className={`flex-1 py-1 rounded text-[10px] font-bold transition-all ${profile.calendarType === 'solar'
                    ? 'bg-gold-500 text-void-950 shadow-sm'
                    : 'text-gray-500 hover:text-gray-300'
                    }`}
                >
                  양력
                </button>
                <button
                  onClick={() => handleCalendarChange('lunar')}
                  className={`flex-1 py-1 rounded text-[10px] font-bold transition-all ${profile.calendarType === 'lunar'
                    ? 'bg-violet-500 text-white shadow-sm'
                    : 'text-gray-500 hover:text-gray-300'
                    }`}
                >
                  음력
                </button>
              </div>
              <div className="flex gap-1">
                <select
                  value={profile.birthDate ? profile.birthDate.split('-')[0] : ''}
                  onChange={(e) => {
                    const year = e.target.value;
                    const month = profile.birthDate?.split('-')[1] || '01';
                    const day = profile.birthDate?.split('-')[2] || '01';
                    setProfile({ ...profile, birthDate: year ? `${year}-${month}-${day}` : '' });
                  }}
                  className="flex-[1.2] glass-input rounded-md px-1 py-2.5 text-[11px] focus:outline-none appearance-none text-center"
                >
                  <option value="">년도</option>
                  {Array.from({ length: 80 }, (_, i) => 2010 - i).map((y) => (
                    <option key={y} value={y} className="bg-void-900">{y}년</option>
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
                  className="flex-1 glass-input rounded-md px-1 py-2.5 text-[11px] focus:outline-none appearance-none text-center"
                >
                  <option value="">월</option>
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={String(m).padStart(2, '0')} className="bg-void-900">{m}월</option>
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
                  className="flex-1 glass-input rounded-md px-1 py-2.5 text-[11px] focus:outline-none appearance-none text-center"
                >
                  <option value="">일</option>
                  {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                    <option key={d} value={String(d).padStart(2, '0')} className="bg-void-900">{d}일</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1 flex items-center gap-1">
                <Clock size={10} /> 태어난 시간
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
                  className="flex-1 glass-input rounded-md px-1 py-2.5 text-[11px] focus:outline-none appearance-none text-center"
                >
                  <option value="">시</option>
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={String(i).padStart(2, '0')} className="bg-void-900">
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
                  className="flex-1 glass-input rounded-md px-1 py-2.5 text-[11px] focus:outline-none appearance-none text-center"
                >
                  <option value="">분</option>
                  {[0, 15, 30, 45].map((m) => (
                    <option key={m} value={String(m).padStart(2, '0')} className="bg-void-900">
                      {m}분
                    </option>
                  ))}
                </select>
              </div>
              <span className="text-[8px] text-gray-600 ml-1">모르면 비워두세요</span>
            </div>
            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1 flex items-center gap-1">
                <MapPin size={10} /> 출생지
              </label>
              <input
                type="text"
                name="birthPlace"
                value={profile.birthPlace}
                onChange={handleProfileChange}
                placeholder="예: 서울, 부산"
                className="w-full glass-input rounded-md px-2 py-2.5 text-xs focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] text-gray-500 mb-1.5 ml-1 flex items-center gap-1">
              <MapPin size={10} /> 현재 거주지
            </label>
            <input
              type="text"
              name="residence"
              value={profile.residence}
              onChange={handleProfileChange}
              placeholder="예: 서울 강남구"
              className="w-full glass-input rounded-md px-3 py-2.5 text-xs focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">혈액형</label>
              <select
                name="bloodType"
                value={profile.bloodType}
                onChange={handleProfileChange}
                className="w-full glass-input rounded-md px-2 py-2.5 text-xs focus:outline-none appearance-none"
              >
                <option value="">선택</option>
                <option value="A" className="bg-void-900">A형</option>
                <option value="B" className="bg-void-900">B형</option>
                <option value="O" className="bg-void-900">O형</option>
                <option value="AB" className="bg-void-900">AB형</option>
              </select>
            </div>
            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">MBTI</label>
              <input
                type="text"
                name="mbti"
                value={profile.mbti}
                onChange={handleProfileChange}
                placeholder="예: INFP"
                className="w-full glass-input rounded-md px-3 py-2.5 text-xs focus:outline-none uppercase"
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">성별</label>
            <select
              name="gender"
              value={profile.gender}
              onChange={handleProfileChange}
              className="w-full glass-input rounded-md px-2 py-2.5 text-xs focus:outline-none appearance-none"
            >
              <option value="male" className="bg-void-900">남성</option>
              <option value="female" className="bg-void-900">여성</option>
              <option value="other" className="bg-void-900">기타</option>
            </select>
          </div>
        </div>
      </div>

      {/* Partner Profile Section */}
      {mode === 'couple' && (
        <div className="mb-8 space-y-5 animate-fadeIn">
          <SectionHeader icon={Heart} title="Partner Profile (상대방)" />

          <div className="space-y-3 bg-pink-900/10 p-3 rounded-xl border border-pink-500/10">

            {/* Partner Face Upload */}
            <div className="mb-4">
              <label className="block text-[10px] text-pink-300 mb-2 ml-1">상대방 관상 사진</label>
              {isAnalyzingPartner ? (
                <div className="w-full h-16 rounded-lg bg-pink-500/10 flex items-center justify-center border border-pink-500/30">
                  <Loader2 className="animate-spin text-pink-400" size={16} />
                  <span className="ml-2 text-xs text-pink-200">분석 중...</span>
                </div>
              ) : profile.partner?.faceFeatures ? (
                <div className="w-full p-3 rounded-lg border border-pink-500/30 bg-pink-500/10 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-pink-400" />
                    <span className="text-xs text-pink-200">데이터 확보됨</span>
                  </div>
                  <label className="cursor-pointer text-[10px] underline text-pink-400 hover:text-pink-300">
                    재업로드
                    <input type="file" accept="image/*" className="hidden" onChange={handlePartnerImageUpload} />
                  </label>
                </div>
              ) : (
                <label
                  className={`w-full h-20 rounded-lg border-2 border-dashed flex flex-col items-center justify-center cursor-pointer transition-all group ${isDraggingPartner
                      ? 'border-pink-400 bg-pink-500/20 scale-[1.02]'
                      : 'border-pink-500/30 hover:bg-pink-500/5 hover:border-pink-500/50'
                    }`}
                  onDragOver={(e) => { e.preventDefault(); setIsDraggingPartner(true); }}
                  onDragEnter={(e) => { e.preventDefault(); setIsDraggingPartner(true); }}
                  onDragLeave={() => setIsDraggingPartner(false)}
                  onDrop={handlePartnerDrop}
                >
                  <Upload size={16} className={`mb-1 transition-all ${isDraggingPartner ? 'text-pink-400 scale-110' : 'text-pink-400/50 group-hover:text-pink-400'}`} />
                  <span className={`text-[10px] transition-all ${isDraggingPartner ? 'text-pink-300' : 'text-pink-300/70 group-hover:text-pink-200'}`}>
                    {isDraggingPartner ? '여기에 놓으세요!' : '클릭 또는 드래그 앤 드롭'}
                  </span>
                  <input type="file" accept="image/*" className="hidden" onChange={handlePartnerImageUpload} />
                </label>
              )}
            </div>

            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">이름</label>
              <input
                type="text"
                name="name"
                value={profile.partner?.name || ''}
                onChange={handlePartnerChange}
                className="w-full glass-input rounded-md px-3 py-2.5 text-xs focus:outline-none border-pink-500/20 focus:border-pink-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">생년월일</label>
              <div className="flex flex-col gap-2">
                <div className="flex bg-void-900/50 rounded-md p-1 border border-pink-500/20 w-full">
                  <button
                    onClick={() => handlePartnerCalendarChange('solar')}
                    className={`flex-1 py-1 rounded text-[10px] font-bold transition-all ${profile.partner?.calendarType === 'solar'
                      ? 'bg-pink-500 text-white shadow-sm'
                      : 'text-gray-500 hover:text-gray-300'
                      }`}
                  >
                    양력
                  </button>
                  <button
                    onClick={() => handlePartnerCalendarChange('lunar')}
                    className={`flex-1 py-1 rounded text-[10px] font-bold transition-all ${profile.partner?.calendarType === 'lunar'
                      ? 'bg-violet-500 text-white shadow-sm'
                      : 'text-gray-500 hover:text-gray-300'
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
                  className="w-full glass-input rounded-md px-2 py-2.5 text-[11px] focus:outline-none border-pink-500/20 focus:border-pink-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">태어난 시간</label>
                <input
                  type="time"
                  name="birthTime"
                  value={profile.partner?.birthTime || ''}
                  onChange={handlePartnerChange}
                  className="w-full glass-input rounded-md px-2 py-2.5 text-[11px] focus:outline-none border-pink-500/20 focus:border-pink-500"
                />
              </div>
              <div>
                <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">출생지</label>
                <input
                  type="text"
                  name="birthPlace"
                  value={profile.partner?.birthPlace || ''}
                  onChange={handlePartnerChange}
                  placeholder="예: 대전"
                  className="w-full glass-input rounded-md px-2 py-2.5 text-xs focus:outline-none border-pink-500/20 focus:border-pink-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">성별</label>
                <select
                  name="gender"
                  value={profile.partner?.gender || 'other'}
                  onChange={handlePartnerChange}
                  className="w-full glass-input rounded-md px-2 py-2.5 text-xs focus:outline-none appearance-none border-pink-500/20 focus:border-pink-500"
                >
                  <option value="male" className="bg-void-900">남성</option>
                  <option value="female" className="bg-void-900">여성</option>
                  <option value="other" className="bg-void-900">기타</option>
                </select>
              </div>
              <div>
                <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">MBTI</label>
                <input
                  type="text"
                  name="mbti"
                  value={profile.partner?.mbti || ''}
                  onChange={handlePartnerChange}
                  placeholder="예: ENFJ"
                  className="w-full glass-input rounded-md px-3 py-2.5 text-xs focus:outline-none uppercase border-pink-500/20 focus:border-pink-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-[10px] text-gray-500 mb-1.5 ml-1">혈액형</label>
              <select
                name="bloodType"
                value={profile.partner?.bloodType || ''}
                onChange={handlePartnerChange}
                className="w-full glass-input rounded-md px-2 py-2.5 text-xs focus:outline-none appearance-none border-pink-500/20 focus:border-pink-500"
              >
                <option value="">선택</option>
                <option value="A" className="bg-void-900">A형</option>
                <option value="B" className="bg-void-900">B형</option>
                <option value="O" className="bg-void-900">O형</option>
                <option value="AB" className="bg-void-900">AB형</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* START BUTTON - 분석 렌즈 위에 배치 */}
      <div className="mb-6 space-y-3 pt-2 border-t border-void-800">
        {/* SOUL EXTRACTION - Visible when Depth >= 50 */}
        {isSessionActive && depthScore >= 50 && (
          <div className="mb-2 animate-fadeIn">
            {digitalTwinData ? (
              <button
                onClick={handleDownloadJson}
                className="w-full py-3 rounded-lg flex items-center justify-center gap-2 font-bold tracking-widest text-xs transition-all duration-500 bg-emerald-900/40 border border-emerald-500/50 text-emerald-400 hover:bg-emerald-800/50 shadow-[0_0_20px_rgba(16,185,129,0.2)]"
              >
                <Download size={14} />
                영혼 다운로드
              </button>
            ) : (
              <button
                onClick={onExtractEssence}
                disabled={isExtracting}
                className="w-full py-3 rounded-lg flex items-center justify-center gap-2 font-bold tracking-widest text-xs transition-all duration-500 bg-gradient-to-r from-violet-600 to-indigo-600 border border-violet-400/30 text-white hover:from-violet-500 hover:to-indigo-500 shadow-[0_0_20px_rgba(139,92,246,0.3)] relative overflow-hidden group"
              >
                {isExtracting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    영혼 추출 중...
                  </>
                ) : (
                  <>
                    <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-500 ease-in-out"></div>
                    <Fingerprint size={14} />
                    디지털 영혼 추출
                  </>
                )}
              </button>
            )}
          </div>
        )}

        {/* START BUTTON */}
        <button
          onClick={onStartSession}
          disabled={isAnalyzingUser || isAnalyzingPartner}
          className={`w-full py-4 rounded-lg flex items-center justify-center gap-2 font-bold tracking-widest text-xs transition-all duration-500 shadow-lg ${isSessionActive
            ? 'bg-void-800 border border-gold-500/30 text-gold-400 hover:bg-gold-500/10'
            : 'bg-gradient-to-r from-gold-600 to-gold-400 text-void-950 hover:from-gold-500 hover:to-gold-300 shadow-[0_0_20px_rgba(212,175,55,0.2)]'
            }`}
        >
          <Play size={12} fill="currentColor" />
          {isSessionActive ? "분석 업데이트" : "상담 시작하기"}
        </button>

        {isSessionActive && (
          <button
            onClick={onReset}
            className="w-full py-2 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/5 transition-all uppercase text-[10px] tracking-widest font-bold"
          >
            초기화
          </button>
        )}
      </div>

      {/* Mode Selection */}
      <div className="mb-8 space-y-3">
        <SectionHeader icon={Activity} title="분석 렌즈" />
        <div className="grid grid-cols-1 gap-2 pt-1">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => onModeChange(m.id)}
              className={`flex items-center gap-3 px-3 py-3 rounded-lg text-xs transition-all duration-300 font-medium border ${mode === m.id
                ? 'bg-void-800 border-gold-500/40 text-gold-200 shadow-[0_0_15px_rgba(212,175,55,0.1)]'
                : 'bg-transparent border-transparent text-gray-500 hover:bg-void-800 hover:text-gray-300'
                }`}
            >
              <span className={mode === m.id ? 'text-gold-400' : 'text-gray-600'}>{m.icon}</span>
              {m.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ControlPanel;
