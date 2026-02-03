import React, { useMemo } from 'react';
import { Message, DepthStage, UserProfile, LiveProfileData } from '../types';
import { EMOTIONAL_KEYWORDS } from '../constants';
import {
  Braces,
  ChevronRight,
  ChevronDown,
  Brain,
  Heart,
  Sparkles,
  Activity,
  Eye,
  Zap,
  X
} from 'lucide-react';

interface JsonProfilePanelProps {
  messages: Message[];
  depthScore: number;
  currentStage: DepthStage;
  currentModel: 'flash' | 'pro';
  turnCount: number;
  profile: UserProfile;
  isVisible: boolean;
  onClose: () => void;
}

// 키워드 추출 유틸
const extractKeywords = (messages: Message[]): LiveProfileData['extracted'] => {
  const userMessages = messages.filter(m => m.role === 'user').map(m => m.text).join(' ');

  const emotionalKeywords: string[] = [];
  const topicKeywords: string[] = [];
  const relationshipMentions: string[] = [];
  const deepSignals: string[] = [];

  // 감정 키워드 추출
  for (const keyword of EMOTIONAL_KEYWORDS) {
    if (userMessages.includes(keyword) && !emotionalKeywords.includes(keyword)) {
      emotionalKeywords.push(keyword);
    }
  }

  // 관계 키워드
  const relationshipWords = ['엄마', '아빠', '부모님', '남자친구', '여자친구', '애인', '남편', '아내', '친구', '상사', '동료', '가족'];
  for (const word of relationshipWords) {
    if (userMessages.includes(word) && !relationshipMentions.includes(word)) {
      relationshipMentions.push(word);
    }
  }

  // 깊은 고민 신호
  const deepSignalWords = ['진짜', '사실', '솔직히', '고백', '비밀', '처음으로', '아무에게도', '트라우마', '상처'];
  for (const word of deepSignalWords) {
    if (userMessages.includes(word) && !deepSignals.includes(word)) {
      deepSignals.push(word);
    }
  }

  // 토픽 키워드 (주요 명사)
  const topicWords = ['직장', '회사', '일', '돈', '연애', '결혼', '이별', '미래', '꿈', '건강', '가족', '성격', '스트레스'];
  for (const word of topicWords) {
    if (userMessages.includes(word) && !topicKeywords.includes(word)) {
      topicKeywords.push(word);
    }
  }

  return {
    emotionalKeywords: emotionalKeywords.slice(0, 8),
    topicKeywords: topicKeywords.slice(0, 6),
    relationshipMentions: relationshipMentions.slice(0, 5),
    deepSignals: deepSignals.slice(0, 5),
  };
};

// 오행 축약 문자열 생성
const formatFiveElements = (profile: UserProfile): string => {
  if (!profile.sajuAnalysis?.fiveElementsBalance) return '분석 대기';
  const { wood, fire, earth, metal, water } = profile.sajuAnalysis.fiveElementsBalance;
  const format = (val: number) => {
    if (val > 0.25) return '↑';
    if (val < 0.15) return '↓';
    return '=';
  };
  return `목${format(wood)} 화${format(fire)} 토${format(earth)} 금${format(metal)} 수${format(water)}`;
};

// 단계별 색상
const getStageTheme = (stage: DepthStage) => {
  switch (stage) {
    case 'exploration': return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400' };
    case 'development': return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400' };
    case 'subconscious': return { bg: 'bg-violet-500/10', border: 'border-violet-500/30', text: 'text-violet-400' };
    case 'unconscious': return { bg: 'bg-indigo-500/10', border: 'border-indigo-500/30', text: 'text-indigo-400' };
    case 'archetypal': return { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400' };
    case 'resolution': return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400' };
    default: return { bg: 'bg-gray-500/10', border: 'border-gray-500/30', text: 'text-gray-400' };
  }
};

const getStageName = (stage: DepthStage): string => {
  switch (stage) {
    case 'exploration': return '탐색';
    case 'development': return '전개';
    case 'subconscious': return '잠재의식';
    case 'unconscious': return '무의식';
    case 'archetypal': return '원형 통합';
    case 'resolution': return '최종 합성';
    default: return '탐색';
  }
};

const JsonProfilePanel: React.FC<JsonProfilePanelProps> = ({
  messages,
  depthScore,
  currentStage,
  currentModel,
  turnCount,
  profile,
  isVisible,
  onClose
}) => {
  const [isExpanded, setIsExpanded] = React.useState(true);
  const theme = getStageTheme(currentStage);

  const extracted = useMemo(() => extractKeywords(messages), [messages]);
  const fiveElementsStr = useMemo(() => formatFiveElements(profile), [profile.sajuAnalysis]);

  // 50% 미만이면 기본 정보만
  const isDeepMode = depthScore >= 50;

  if (!isVisible) return null;

  return (
    <div className={`w-80 flex-shrink-0 flex flex-col h-full bg-void-950/95 backdrop-blur-xl border-l border-void-800 overflow-y-auto z-20 transition-all duration-500 ${isDeepMode ? 'border-l-violet-500/30' : ''}`}>
      {/* Header */}
      <div className={`sticky top-0 z-10 p-4 border-b ${theme.border} ${theme.bg} backdrop-blur-xl`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Braces size={16} className={theme.text} />
            <span className="text-xs font-bold tracking-widest uppercase text-gray-300">Live Profile</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-void-800 rounded transition-colors"
            >
              {isExpanded ? <ChevronDown size={14} className="text-gray-500" /> : <ChevronRight size={14} className="text-gray-500" />}
            </button>
            <button
              onClick={onClose}
              className="p-1 hover:bg-void-800 rounded transition-colors lg:hidden"
            >
              <X size={14} className="text-gray-500" />
            </button>
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-5">
          {/* Meta Section */}
          <div className={`p-3 rounded-lg ${theme.bg} border ${theme.border}`}>
            <div className="flex items-center gap-2 mb-3">
              <Activity size={12} className={theme.text} />
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Session Meta</span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">심도</span>
                <span className={`font-mono font-bold ${theme.text}`}>{depthScore}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">단계</span>
                <span className={`font-medium ${theme.text}`}>{getStageName(currentStage)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">모델</span>
                <span className={`font-mono ${currentModel === 'pro' ? 'text-violet-400' : 'text-gray-400'}`}>
                  {currentModel === 'pro' ? 'Pro' : 'Flash'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">턴</span>
                <span className="font-mono text-gray-300">{turnCount}</span>
              </div>
            </div>
          </div>

          {/* Extracted Keywords */}
          <div className="p-3 rounded-lg bg-void-900 border border-void-700">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={12} className="text-gold-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Extracted</span>
            </div>

            {extracted.emotionalKeywords.length > 0 && (
              <div className="mb-3">
                <div className="text-[9px] text-gray-600 mb-1">감정 키워드</div>
                <div className="flex flex-wrap gap-1">
                  {extracted.emotionalKeywords.map((kw, i) => (
                    <span key={i} className="px-1.5 py-0.5 text-[10px] bg-red-500/20 text-red-300 rounded">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {extracted.topicKeywords.length > 0 && (
              <div className="mb-3">
                <div className="text-[9px] text-gray-600 mb-1">토픽</div>
                <div className="flex flex-wrap gap-1">
                  {extracted.topicKeywords.map((kw, i) => (
                    <span key={i} className="px-1.5 py-0.5 text-[10px] bg-blue-500/20 text-blue-300 rounded">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {extracted.relationshipMentions.length > 0 && (
              <div className="mb-3">
                <div className="text-[9px] text-gray-600 mb-1">관계 언급</div>
                <div className="flex flex-wrap gap-1">
                  {extracted.relationshipMentions.map((kw, i) => (
                    <span key={i} className="px-1.5 py-0.5 text-[10px] bg-pink-500/20 text-pink-300 rounded">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {extracted.deepSignals.length > 0 && (
              <div>
                <div className="text-[9px] text-gray-600 mb-1">깊은 고민 신호</div>
                <div className="flex flex-wrap gap-1">
                  {extracted.deepSignals.map((kw, i) => (
                    <span key={i} className="px-1.5 py-0.5 text-[10px] bg-violet-500/20 text-violet-300 rounded animate-pulse">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {extracted.emotionalKeywords.length === 0 &&
             extracted.topicKeywords.length === 0 &&
             extracted.relationshipMentions.length === 0 && (
              <div className="text-[10px] text-gray-600 italic">대화를 시작하면 키워드가 추출됩니다...</div>
            )}
          </div>

          {/* Profile Summary */}
          <div className="p-3 rounded-lg bg-void-900 border border-void-700">
            <div className="flex items-center gap-2 mb-3">
              <Brain size={12} className="text-gold-400" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Profile</span>
            </div>
            <div className="space-y-2 text-xs">
              <div>
                <div className="text-[9px] text-gray-600 mb-0.5">오행 균형</div>
                <div className="font-mono text-gray-300">{fiveElementsStr}</div>
              </div>
              {profile.sajuAnalysis?.dayMaster && (
                <div>
                  <div className="text-[9px] text-gray-600 mb-0.5">일주(日主)</div>
                  <div className="text-gray-300">
                    {profile.sajuAnalysis.dayMaster} ({profile.sajuAnalysis.dayMasterStrength})
                  </div>
                </div>
              )}
              {profile.mbti && (
                <div>
                  <div className="text-[9px] text-gray-600 mb-0.5">MBTI</div>
                  <div className="text-gray-300">{profile.mbti}</div>
                </div>
              )}
              {profile.faceFeatures && (
                <div>
                  <div className="text-[9px] text-gray-600 mb-0.5">관상 요약</div>
                  <div className="text-gray-400 text-[10px] line-clamp-2">{profile.faceFeatures.slice(0, 80)}...</div>
                </div>
              )}
            </div>
          </div>

          {/* Deep Analysis (50% 이상) */}
          {isDeepMode && (
            <div className={`p-3 rounded-lg border ${theme.border} ${theme.bg} animate-fadeIn`}>
              <div className="flex items-center gap-2 mb-3">
                <Eye size={12} className={theme.text} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Depth Analysis</span>
              </div>
              <div className="space-y-2 text-xs">
                <div>
                  <div className="text-[9px] text-gray-600 mb-0.5">현재 분석 모드</div>
                  <div className={`${theme.text} font-medium`}>
                    {currentStage === 'subconscious' && '잠재의식 패턴 탐색 중...'}
                    {currentStage === 'unconscious' && '무의식 그림자 분석 중...'}
                    {currentStage === 'archetypal' && '원형 통합 작업 중...'}
                    {currentStage === 'resolution' && '최종 솔루션 합성 중...'}
                    {(currentStage === 'exploration' || currentStage === 'development') && '심층 분석 준비 중...'}
                  </div>
                </div>
                {currentStage === 'unconscious' || currentStage === 'archetypal' || currentStage === 'resolution' ? (
                  <>
                    <div>
                      <div className="text-[9px] text-gray-600 mb-0.5">추정 원형</div>
                      <div className="text-purple-300">분석 진행 중...</div>
                    </div>
                    <div>
                      <div className="text-[9px] text-gray-600 mb-0.5">그림자 측면</div>
                      <div className="text-indigo-300">대화 데이터 수집 중...</div>
                    </div>
                  </>
                ) : null}
              </div>
            </div>
          )}

          {/* JSON Preview hint */}
          <div className="p-2 rounded bg-void-900/50 border border-void-800">
            <div className="text-[9px] text-gray-600 text-center">
              {depthScore >= 50
                ? '💾 심도 50% 달성 - JSON 다운로드 가능'
                : `📊 심도 ${50 - depthScore}% 더 필요`}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JsonProfilePanel;
