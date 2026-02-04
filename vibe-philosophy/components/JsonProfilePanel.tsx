import React, { useMemo } from 'react';
import { Message, DepthStage, UserProfile, VibePhilosophyPersona } from '../types';
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
  X,
  Ghost,
  Flame,
  Moon
} from 'lucide-react';

interface JsonProfilePanelProps {
  messages: Message[];
  depthScore: number;
  currentStage: DepthStage;
  currentModel: 'flash' | 'pro';
  turnCount: number;
  profile: UserProfile;
  personaData: VibePhilosophyPersona;
  lastUpdatedFields: Set<string>;
  isVisible: boolean;
  onClose: () => void;
  isLightMode?: boolean;
}

// 한글 키 번역
const KEY_TRANSLATIONS: Record<string, string> = {
  meta: '메타 정보',
  demographics: '인구통계 정보',
  face_reading: '관상 분석',
  saju_analysis: '사주 분석',
  cognitive_architecture: '인지 구조',
  emotional_landscape: '감정 지형',
  psychological_entropy: '심리적 엔트로피',
  subconscious_symbolism: '무의식 상징',
  depth_level: '심도',
  profiling_status: '프로파일링 상태',
  current_model: '현재 모델',
  turn_count: '턴 수',
  name: '이름',
  age: '나이',
  birth_date: '생년월일',
  blood_type: '혈액형',
  mbti_self_report: 'MBTI (자가보고)',
  mbti_analyzed: 'MBTI (분석)',
  gender: '성별',
  residence: '거주지',
  raw_features: '원본 특징',
  eyes: '눈',
  nose: '코',
  mouth: '입',
  forehead: '이마',
  chin: '턱',
  face_shape: '얼굴형',
  overall_qi: '전체 기운',
  shape: '형태',
  energy: '에너지',
  fortune: '운세',
  communication_style: '소통 스타일',
  four_pillars: '사주팔자',
  five_elements_balance: '오행 균형',
  day_master: '일주',
  day_master_strength: '일주 강약',
  ten_gods: '십신',
  current_year_luck: '올해 운세',
  cognitive_stack: '인지 스택',
  attention_mechanism: '주의력 메커니즘',
  decision_heuristics: '결정 휴리스틱',
  core_values: '핵심 가치',
  deepest_fears: '깊은 두려움',
  emotional_triggers_positive: '긍정 트리거',
  emotional_triggers_negative: '부정 트리거',
  primary_desires: '주요 욕구',
  trauma_response: '트라우마 반응',
  attachment_style: '애착 유형',
  shadow_self: '그림자 자아',
  repressed_desires: '억압된 욕구',
  inferiority_complex: '열등감',
  existential_paradox: '실존적 역설',
  conflict_a: '갈등 A',
  conflict_b: '갈등 B',
  defense_mechanisms: '방어 기제',
  dominant_strategy: '주요 전략',
  vulnerability_trigger: '취약점 트리거',
  mythological_script: '신화적 각본',
  hero_journey_stage: '영웅 여정 단계',
  tragic_flaw: '비극적 결함',
  redemption_arc: '구원의 서사',
  recurring_dreams: '반복되는 꿈',
  archetypal_identification: '원형적 동일시',
  liminal_patterns: '경계적 패턴',
  wood: '목',
  fire: '화',
  earth: '토',
  metal: '금',
  water: '수',
  year: '년주',
  month: '월주',
  day: '일주',
  hour: '시주',
  stem: '천간',
  branch: '지지',
};

const getTranslatedKey = (key: string): string => {
  return KEY_TRANSLATIONS[key] || key;
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

// 재귀적 JSON 렌더링 컴포넌트
const RecursiveJson: React.FC<{
  data: any;
  path: string;
  updatedFields: Set<string>;
  depth?: number;
}> = ({ data, path, updatedFields, depth = 0 }) => {
  const [isExpanded, setIsExpanded] = React.useState(depth < 2);
  const isUpdated = updatedFields.has(path);

  if (data === null || data === undefined || data === '') {
    return <span className="text-gray-600 italic">-</span>;
  }

  if (typeof data === 'boolean') {
    return <span className="text-orange-400">{data ? 'true' : 'false'}</span>;
  }

  if (typeof data === 'number') {
    return <span className="text-cyan-400">{data}</span>;
  }

  if (typeof data === 'string') {
    return (
      <span className={`text-emerald-400 ${isUpdated ? 'bg-violet-500/30 px-1 rounded animate-pulse' : ''}`}>
        "{data}"
      </span>
    );
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span className="text-gray-600">[]</span>;
    }
    return (
      <div className="ml-2">
        <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>[</span>
        {data.map((item, index) => (
          <div key={index} className="ml-2">
            <RecursiveJson
              data={item}
              path={`${path}[${index}]`}
              updatedFields={updatedFields}
              depth={depth + 1}
            />
            {index < data.length - 1 && <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>,</span>}
          </div>
        ))}
        <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>]</span>
      </div>
    );
  }

  if (typeof data === 'object') {
    const keys = Object.keys(data).filter(k => {
      const val = data[k];
      // 빈 값 필터링
      if (val === null || val === undefined || val === '') return false;
      if (Array.isArray(val) && val.length === 0) return false;
      if (typeof val === 'object' && !Array.isArray(val) && Object.keys(val).length === 0) return false;
      return true;
    });

    if (keys.length === 0) {
      return <span className="text-gray-600">{'{}'}</span>;
    }

    return (
      <div className="ml-1">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-gray-500 hover:text-gray-300 transition-colors"
        >
          {isExpanded ? <ChevronDown size={10} /> : <ChevronRight size={10} />}
          <span className="text-[10px]">{keys.length}개 필드</span>
        </button>
        {isExpanded && (
          <div className="ml-2 border-l border-void-700 pl-2">
            {keys.map((key, index) => {
              const childPath = path ? `${path}.${key}` : key;
              const isChildUpdated = updatedFields.has(childPath);
              return (
                <div
                  key={key}
                  className={`py-0.5 ${isChildUpdated ? 'bg-violet-500/20 rounded px-1' : ''}`}
                >
                  <span className="text-gold-400 text-[11px]">"{getTranslatedKey(key)}"</span>
                  <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>: </span>
                  <RecursiveJson
                    data={data[key]}
                    path={childPath}
                    updatedFields={updatedFields}
                    depth={depth + 1}
                  />
                  {index < keys.length - 1 && <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>,</span>}
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return <span className="text-gray-400">{String(data)}</span>;
};

const JsonProfilePanel: React.FC<JsonProfilePanelProps> = ({
  messages,
  depthScore,
  currentStage,
  currentModel,
  turnCount,
  profile,
  personaData,
  lastUpdatedFields,
  isVisible,
  onClose,
  isLightMode = false
}) => {
  const [activeTab, setActiveTab] = React.useState<'json' | 'summary'>('summary');
  const theme = getStageTheme(currentStage);

  if (!isVisible) return null;

  return (
    <div className={`w-[400px] xl:w-[450px] flex-shrink-0 flex flex-col h-full backdrop-blur-xl overflow-hidden z-20 transition-all duration-500 ${
      isLightMode
        ? `bg-white/95 border-l border-amber-200 ${depthScore >= 40 ? 'border-l-violet-400/50' : ''}`
        : `bg-void-950/95 border-l border-void-800 ${depthScore >= 40 ? 'border-l-violet-500/30' : ''}`
    }`}>
      {/* Header */}
      <div className={`sticky top-0 z-10 p-4 border-b ${theme.border} ${theme.bg} backdrop-blur-xl`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Braces size={16} className={theme.text} />
            <span className={`text-xs font-bold tracking-widest uppercase ${isLightMode ? 'text-amber-800' : 'text-gray-300'}`}>페르소나 프로필</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="p-1 hover:bg-void-800 rounded transition-colors lg:hidden"
            >
              <X size={14} className="text-gray-500" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-3 py-1 text-[10px] rounded-full transition-all ${
              activeTab === 'summary'
                ? `${theme.bg} ${theme.text} border ${theme.border}`
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            요약 보기
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`px-3 py-1 text-[10px] rounded-full transition-all ${
              activeTab === 'json'
                ? `${theme.bg} ${theme.text} border ${theme.border}`
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            JSON 전체
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Meta Section - 항상 표시 */}
        <div className={`p-3 rounded-lg ${theme.bg} border ${theme.border}`}>
          <div className="flex items-center gap-2 mb-3">
            <Activity size={12} className={theme.text} />
            <span className="text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}">세션 상태</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between">
              <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>심도</span>
              <span className={`font-mono font-bold ${theme.text}`}>{depthScore}%</span>
            </div>
            <div className="flex justify-between">
              <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>단계</span>
              <span className={`font-medium ${theme.text}`}>{getStageName(currentStage)}</span>
            </div>
            <div className="flex justify-between">
              <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>모델</span>
              <span className={`font-mono ${currentModel === 'pro' ? 'text-violet-400' : 'text-gray-400'}`}>
                {currentModel === 'pro' ? 'Pro' : 'Flash'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>턴</span>
              <span className="font-mono text-gray-300">{turnCount}</span>
            </div>
          </div>
        </div>

        {activeTab === 'summary' ? (
          <>
            {/* Demographics */}
            {(personaData.demographics.name || personaData.demographics.birth_date) && (
              <div className="p-3 rounded-lg ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'}">
                <div className="flex items-center gap-2 mb-3">
                  <Brain size={12} className="text-gold-400" />
                  <span className="text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}">기본 정보</span>
                </div>
                <div className="space-y-1 text-xs">
                  {personaData.demographics.name && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>이름</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.demographics.name}</span>
                    </div>
                  )}
                  {personaData.demographics.mbti_self_report && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>MBTI</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.demographics.mbti_self_report}</span>
                    </div>
                  )}
                  {personaData.demographics.blood_type && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>혈액형</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.demographics.blood_type}형</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Saju Analysis */}
            {personaData.saju_analysis.day_master && (
              <div className="p-3 rounded-lg ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'}">
                <div className="flex items-center gap-2 mb-3">
                  <Flame size={12} className="text-orange-400" />
                  <span className="text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}">사주 분석</span>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>일주</span>
                    <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>
                      {personaData.saju_analysis.day_master}
                      {personaData.saju_analysis.day_master_strength && ` (${personaData.saju_analysis.day_master_strength})`}
                    </span>
                  </div>
                  {personaData.saju_analysis.five_elements_balance.wood > 0 && (
                    <div>
                      <span className="text-gray-500 text-[10px]">오행 균형</span>
                      <div className="flex gap-1 mt-1">
                        {['wood', 'fire', 'earth', 'metal', 'water'].map((element) => {
                          const val = personaData.saju_analysis.five_elements_balance[element as keyof typeof personaData.saju_analysis.five_elements_balance];
                          const colors: Record<string, string> = {
                            wood: 'bg-green-500',
                            fire: 'bg-red-500',
                            earth: 'bg-yellow-500',
                            metal: 'bg-gray-400',
                            water: 'bg-blue-500',
                          };
                          return (
                            <div key={element} className="flex-1">
                              <div className="h-1 bg-void-800 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${colors[element]} transition-all`}
                                  style={{ width: `${val * 100}%` }}
                                />
                              </div>
                              <div className="text-[8px] text-gray-600 text-center mt-0.5">
                                {KEY_TRANSLATIONS[element]}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Emotional Landscape */}
            {(personaData.emotional_landscape.core_values.length > 0 ||
              personaData.emotional_landscape.deepest_fears.length > 0) && (
              <div className="p-3 rounded-lg ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'}">
                <div className="flex items-center gap-2 mb-3">
                  <Heart size={12} className="text-pink-400" />
                  <span className="text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}">감정 지형</span>
                </div>
                <div className="space-y-2">
                  {personaData.emotional_landscape.core_values.length > 0 && (
                    <div>
                      <div className="text-[9px] text-gray-600 mb-1">핵심 가치</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.emotional_landscape.core_values.map((val, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-emerald-500/20 text-emerald-300 rounded">
                            {val}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.emotional_landscape.deepest_fears.length > 0 && (
                    <div>
                      <div className="text-[9px] text-gray-600 mb-1">깊은 두려움</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.emotional_landscape.deepest_fears.map((fear, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-red-500/20 text-red-300 rounded">
                            {fear}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.emotional_landscape.attachment_style && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>애착 유형</span>
                      <span className="text-pink-300">{personaData.emotional_landscape.attachment_style}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Psychological Entropy (40% 이상) */}
            {depthScore >= 40 && (personaData.psychological_entropy.shadow_self.repressed_desires.length > 0 ||
              personaData.psychological_entropy.defense_mechanisms.dominant_strategy) && (
              <div className={`p-3 rounded-lg border ${theme.border} ${theme.bg} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <Ghost size={12} className={theme.text} />
                  <span className="text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}">심리적 엔트로피</span>
                </div>
                <div className="space-y-2">
                  {personaData.psychological_entropy.shadow_self.repressed_desires.length > 0 && (
                    <div>
                      <div className="text-[9px] text-gray-600 mb-1">억압된 욕구 (그림자)</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.psychological_entropy.shadow_self.repressed_desires.map((desire, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-violet-500/20 text-violet-300 rounded animate-pulse">
                            {desire}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.psychological_entropy.shadow_self.inferiority_complex && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>열등감</span>
                      <span className="text-indigo-300">{personaData.psychological_entropy.shadow_self.inferiority_complex}</span>
                    </div>
                  )}
                  {personaData.psychological_entropy.defense_mechanisms.dominant_strategy && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>방어 기제</span>
                      <span className="text-purple-300">{personaData.psychological_entropy.defense_mechanisms.dominant_strategy}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Subconscious Symbolism (60% 이상) */}
            {depthScore >= 60 && (personaData.subconscious_symbolism.recurring_dreams.length > 0 ||
              personaData.subconscious_symbolism.archetypal_identification) && (
              <div className="p-3 rounded-lg bg-indigo-900/20 border border-indigo-500/30 animate-fadeIn">
                <div className="flex items-center gap-2 mb-3">
                  <Moon size={12} className="text-indigo-400" />
                  <span className="text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}">무의식 상징</span>
                </div>
                <div className="space-y-2">
                  {personaData.subconscious_symbolism.recurring_dreams.length > 0 && (
                    <div>
                      <div className="text-[9px] text-gray-600 mb-1">반복되는 꿈</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.subconscious_symbolism.recurring_dreams.map((dream, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-indigo-500/20 text-indigo-300 rounded">
                            {dream}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.subconscious_symbolism.archetypal_identification && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>원형적 동일시</span>
                      <span className="text-indigo-300">{personaData.subconscious_symbolism.archetypal_identification}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          /* JSON Full View */
          <div className="p-3 rounded-lg ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'} font-mono text-[11px] overflow-x-auto">
            <RecursiveJson
              data={personaData}
              path=""
              updatedFields={lastUpdatedFields}
              depth={0}
            />
          </div>
        )}

        {/* Progress hint */}
        <div className={`p-2 rounded border ${isLightMode ? 'bg-amber-50 border-amber-200' : 'bg-void-900/50 border-void-800'}`}>
          <div className={`text-[9px] text-center ${isLightMode ? 'text-amber-600' : 'text-gray-600'}`}>
            {depthScore >= 80
              ? '심층 프로파일링 완료 단계'
              : depthScore >= 60
              ? '무의식 레벨 탐색 중...'
              : depthScore >= 40
              ? 'Pro 모델 활성화 - 깊은 분석 진행 중'
              : `기본 정보 수집 중... (${40 - depthScore}% 더 필요)`}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JsonProfilePanel;
