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
  Moon,
  ScanFace,
  Compass,
  Shield,
  Swords,
  BookOpen,
  Target,
  Download,
  Fingerprint
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
  onDownloadSoul?: () => void;  // 🔥 영혼 다운로드 콜백
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
  specific_behaviors: '구체적 행동 패턴',
  mythological_script: '신화적 각본',
  hero_journey_stage: '영웅 여정 단계',
  tragic_flaw: '비극적 결함',
  redemption_arc: '구원의 서사',
  current_enactment: '현재 연기 중인 신화',
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
  // 🔥 레거시 확장 필드
  primal_drives: '원초적 충동',
  libido_direction: '리비도 방향',
  thanatos_manifestation: '타나토스 발현',
  environmental_resistance: '환경 저항',
  trigger_points: '트리거 포인트',
  rebellion_style: '저항 양식',
  life_trajectory: '인생 궤적',
  childhood_imprints: '어린 시절 각인',
  family_history: '가족력',
  paternal_influence: '부계 영향',
  maternal_influence: '모계 영향',
  genetic_factors: '유전적 요소',
  career_path: '경력 경로',
  turning_points: '인생 전환점',
  current_status: '현재 상태',
  cultural_context: '문화적 맥락',
  era_definition: '세대 정의',
  social_taboos_broken: '깨뜨린 금기',
  legacy_archetype: '레거시 원형',
  fandom_dynamics: '팬덤 역학',
  master_attributes: '거장 속성',
  artistic_methodology: '예술적 방법론',
  obsession_points: '집착 포인트',
  ritual_routine: '의식/루틴',
  perfectionism_scope: '완벽주의 범위',
  collaboration_style: '협업 스타일',
  signature_style: '시그니처 스타일',
  visual_motifs: '시각적 모티프',
  auditory_signatures: '청각적 시그니처',
  narrative_structure: '내러티브 구조',
  genre_fusion: '장르 융합',
  sensory_architecture: '감각 아키텍처',
  dominant_sense: '주요 감각',
  synesthesia_tendency: '공감각 성향',
  rhythm_perception: '리듬 인식',
  space_perception: '공간 인식',
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
  isLightMode?: boolean;
}> = ({ data, path, updatedFields, depth = 0, isLightMode = false }) => {
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
              isLightMode={isLightMode}
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
                    isLightMode={isLightMode}
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
  isLightMode = false,
  onDownloadSoul
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

            {/* Face Reading - 관상 분석 */}
            {(personaData.face_reading.overall_qi || personaData.face_reading.eyes.shape) && (
              <div className={`p-3 rounded-lg ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <ScanFace size={12} className={isLightMode ? 'text-amber-500' : 'text-gold-400'} />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>관상 분석</span>
                </div>
                <div className="space-y-2 text-xs">
                  {personaData.face_reading.overall_qi && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>전체 기운</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.face_reading.overall_qi}</span>
                    </div>
                  )}
                  {personaData.face_reading.face_shape && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>얼굴형</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.face_reading.face_shape}</span>
                    </div>
                  )}
                  {personaData.face_reading.eyes.shape && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>눈</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.face_reading.eyes.shape} ({personaData.face_reading.eyes.energy})</span>
                    </div>
                  )}
                  {personaData.face_reading.nose.shape && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>코</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.face_reading.nose.shape}</span>
                    </div>
                  )}
                  {personaData.face_reading.mouth.shape && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>입</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.face_reading.mouth.shape}</span>
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

            {/* Cognitive Architecture - 인지 구조 */}
            {(personaData.cognitive_architecture.mbti_analyzed || personaData.cognitive_architecture.cognitive_stack.length > 0) && (
              <div className={`p-3 rounded-lg ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'}`}>
                <div className="flex items-center gap-2 mb-3">
                  <Compass size={12} className={isLightMode ? 'text-blue-500' : 'text-blue-400'} />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>인지 구조</span>
                </div>
                <div className="space-y-2 text-xs">
                  {personaData.cognitive_architecture.mbti_analyzed && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>MBTI (분석)</span>
                      <span className="text-blue-400 font-medium">{personaData.cognitive_architecture.mbti_analyzed}</span>
                    </div>
                  )}
                  {personaData.cognitive_architecture.cognitive_stack.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>인지 스택</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.cognitive_architecture.cognitive_stack.map((fn, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-blue-500/20 text-blue-300 rounded">
                            {fn}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.cognitive_architecture.attention_mechanism && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>주의력</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.cognitive_architecture.attention_mechanism}</span>
                    </div>
                  )}
                  {personaData.cognitive_architecture.decision_heuristics && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>결정 방식</span>
                      <span className={isLightMode ? 'text-amber-800' : 'text-gray-300'}>{personaData.cognitive_architecture.decision_heuristics}</span>
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
                  {personaData.emotional_landscape.primary_desires.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>주요 욕구</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.emotional_landscape.primary_desires.map((desire, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-orange-500/20 text-orange-300 rounded">
                            {desire}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.emotional_landscape.emotional_triggers_positive.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>긍정 트리거</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.emotional_landscape.emotional_triggers_positive.map((t, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-green-500/20 text-green-300 rounded">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.emotional_landscape.emotional_triggers_negative.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>부정 트리거</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.emotional_landscape.emotional_triggers_negative.map((t, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-red-500/20 text-red-300 rounded">
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.emotional_landscape.trauma_response && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>트라우마 반응</span>
                      <span className="text-pink-300">{personaData.emotional_landscape.trauma_response}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Psychological Entropy (40% 이상) */}
            {depthScore >= 40 && (personaData.psychological_entropy.shadow_self.repressed_desires.length > 0 ||
              personaData.psychological_entropy.defense_mechanisms.dominant_strategy ||
              personaData.psychological_entropy.defense_mechanisms.specific_behaviors?.length > 0) && (
              <div className={`p-3 rounded-lg border ${theme.border} ${theme.bg} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <Ghost size={12} className={theme.text} />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>심리적 엔트로피</span>
                </div>
                <div className="space-y-2">
                  {personaData.psychological_entropy.shadow_self.repressed_desires.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>억압된 욕구 (그림자)</div>
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
                  {/* 🔥 구체적 행동 패턴 (레거시 핵심 필드) */}
                  {personaData.psychological_entropy.defense_mechanisms.specific_behaviors?.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>
                        구체적 행동 패턴 ({personaData.psychological_entropy.defense_mechanisms.specific_behaviors.length}개)
                      </div>
                      <div className="space-y-1">
                        {personaData.psychological_entropy.defense_mechanisms.specific_behaviors.map((behavior, i) => (
                          <div key={i} className="text-[10px] text-purple-300 bg-purple-500/10 px-2 py-1 rounded">
                            • {behavior}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.psychological_entropy.defense_mechanisms.vulnerability_trigger && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>취약점 트리거</span>
                      <span className="text-purple-300">{personaData.psychological_entropy.defense_mechanisms.vulnerability_trigger}</span>
                    </div>
                  )}
                  {(personaData.psychological_entropy.existential_paradox.conflict_a || personaData.psychological_entropy.existential_paradox.conflict_b) && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>실존적 역설</div>
                      <div className="text-[10px] text-indigo-300 italic">
                        {personaData.psychological_entropy.existential_paradox.conflict_a}
                        {personaData.psychological_entropy.existential_paradox.conflict_b && (
                          <span className="text-gray-500"> vs </span>
                        )}
                        {personaData.psychological_entropy.existential_paradox.conflict_b}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 🔥 Primal Drives - 원초적 충동 (50% 이상) */}
            {depthScore >= 50 && (personaData.psychological_entropy.primal_drives?.libido_direction ||
              personaData.psychological_entropy.primal_drives?.thanatos_manifestation) && (
              <div className={`p-3 rounded-lg border ${theme.border} ${theme.bg} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <Flame size={12} className="text-red-400" />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>원초적 충동</span>
                </div>
                <div className="space-y-2 text-xs">
                  {personaData.psychological_entropy.primal_drives?.libido_direction && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>리비도 방향 (생/창조)</div>
                      <div className="text-[10px] text-orange-300">{personaData.psychological_entropy.primal_drives.libido_direction}</div>
                    </div>
                  )}
                  {personaData.psychological_entropy.primal_drives?.thanatos_manifestation && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>타나토스 발현 (죽음/파괴)</div>
                      <div className="text-[10px] text-red-300">{personaData.psychological_entropy.primal_drives.thanatos_manifestation}</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Mythological Script - 신화적 각본 (50% 이상) */}
            {depthScore >= 50 && (personaData.psychological_entropy.mythological_script.hero_journey_stage ||
              personaData.psychological_entropy.mythological_script.tragic_flaw) && (
              <div className={`p-3 rounded-lg border ${theme.border} ${theme.bg} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <BookOpen size={12} className={theme.text} />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>신화적 각본</span>
                </div>
                <div className="space-y-2 text-xs">
                  {personaData.psychological_entropy.mythological_script.hero_journey_stage && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>영웅 여정</span>
                      <span className="text-amber-300">{personaData.psychological_entropy.mythological_script.hero_journey_stage}</span>
                    </div>
                  )}
                  {personaData.psychological_entropy.mythological_script.tragic_flaw && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>비극적 결함</span>
                      <span className="text-red-300">{personaData.psychological_entropy.mythological_script.tragic_flaw}</span>
                    </div>
                  )}
                  {personaData.psychological_entropy.mythological_script.redemption_arc && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>구원의 서사</span>
                      <span className="text-emerald-300">{personaData.psychological_entropy.mythological_script.redemption_arc}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Subconscious Symbolism (60% 이상) */}
            {depthScore >= 60 && (personaData.subconscious_symbolism.recurring_dreams.length > 0 ||
              personaData.subconscious_symbolism.archetypal_identification) && (
              <div className={`p-3 rounded-lg ${isLightMode ? 'bg-indigo-100 border border-indigo-300' : 'bg-indigo-900/20 border border-indigo-500/30'} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <Moon size={12} className="text-indigo-400" />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>무의식 상징</span>
                </div>
                <div className="space-y-2">
                  {personaData.subconscious_symbolism.recurring_dreams.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>반복되는 꿈</div>
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
                  {personaData.subconscious_symbolism.liminal_patterns.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>경계적 패턴</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.subconscious_symbolism.liminal_patterns.map((pattern, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-indigo-500/20 text-indigo-300 rounded">
                            {pattern}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 🔥 Life Trajectory - 인생 궤적 (55% 이상) */}
            {depthScore >= 55 && (personaData.life_trajectory?.childhood_imprints?.length > 0 ||
              personaData.life_trajectory?.turning_points?.length > 0 ||
              personaData.life_trajectory?.family_history?.paternal_influence) && (
              <div className={`p-3 rounded-lg ${isLightMode ? 'bg-cyan-100 border border-cyan-300' : 'bg-cyan-900/20 border border-cyan-500/30'} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <Compass size={12} className="text-cyan-400" />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>인생 궤적</span>
                </div>
                <div className="space-y-2">
                  {personaData.life_trajectory?.childhood_imprints?.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>어린 시절 각인</div>
                      <div className="space-y-1">
                        {personaData.life_trajectory.childhood_imprints.map((imprint, i) => (
                          <div key={i} className="text-[10px] text-cyan-300 bg-cyan-500/10 px-2 py-1 rounded">
                            • {imprint}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.life_trajectory?.family_history?.paternal_influence && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>부계 영향</span>
                      <span className="text-cyan-300">{personaData.life_trajectory.family_history.paternal_influence}</span>
                    </div>
                  )}
                  {personaData.life_trajectory?.family_history?.maternal_influence && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>모계 영향</span>
                      <span className="text-cyan-300">{personaData.life_trajectory.family_history.maternal_influence}</span>
                    </div>
                  )}
                  {personaData.life_trajectory?.turning_points?.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>인생 전환점</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.life_trajectory.turning_points.map((point, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-cyan-500/20 text-cyan-300 rounded">
                            {point}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {personaData.life_trajectory?.current_status && (
                    <div className="flex justify-between text-xs">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>현재 상태</span>
                      <span className="text-cyan-300">{personaData.life_trajectory.current_status}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 🔥 Cultural Context - 문화적 맥락 (70% 이상) */}
            {depthScore >= 70 && (personaData.cultural_context?.era_definition ||
              personaData.cultural_context?.legacy_archetype) && (
              <div className={`p-3 rounded-lg ${isLightMode ? 'bg-amber-100 border border-amber-300' : 'bg-amber-900/20 border border-amber-500/30'} animate-fadeIn`}>
                <div className="flex items-center gap-2 mb-3">
                  <Target size={12} className="text-amber-400" />
                  <span className={`text-[10px] font-bold uppercase tracking-widest ${isLightMode ? 'text-amber-600' : 'text-gray-400'}`}>문화적 맥락</span>
                </div>
                <div className="space-y-2 text-xs">
                  {personaData.cultural_context?.era_definition && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>세대 정의</span>
                      <span className="text-amber-300">{personaData.cultural_context.era_definition}</span>
                    </div>
                  )}
                  {personaData.cultural_context?.legacy_archetype && (
                    <div className="flex justify-between">
                      <span className={isLightMode ? 'text-amber-600' : 'text-gray-500'}>레거시 원형</span>
                      <span className="text-amber-300">{personaData.cultural_context.legacy_archetype}</span>
                    </div>
                  )}
                  {personaData.cultural_context?.social_taboos_broken?.length > 0 && (
                    <div>
                      <div className={`text-[9px] mb-1 ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>깨뜨린 금기</div>
                      <div className="flex flex-wrap gap-1">
                        {personaData.cultural_context.social_taboos_broken.map((taboo, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-[10px] bg-amber-500/20 text-amber-300 rounded">
                            {taboo}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        ) : (
          /* JSON Full View */
          <div className={`p-3 rounded-lg font-mono text-[11px] overflow-x-auto ${isLightMode ? 'bg-amber-50 border border-amber-200' : 'bg-void-900 border border-void-700'}`}>
            <RecursiveJson
              data={personaData}
              path=""
              updatedFields={lastUpdatedFields}
              depth={0}
              isLightMode={isLightMode}
            />
          </div>
        )}

        {/* 🔥 영혼 다운로드 버튼 (50% 이상일 때 활성화, 탭 공통) */}
        {depthScore >= 50 && onDownloadSoul && (
          <button
            onClick={onDownloadSoul}
            className={`w-full py-3 rounded-xl flex items-center justify-center gap-2 font-bold tracking-wide text-sm transition-all duration-300 ${
              depthScore >= 80
                ? 'bg-gradient-to-r from-emerald-600 to-teal-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:from-emerald-500 hover:to-teal-400'
                : 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-[0_0_15px_rgba(139,92,246,0.3)] hover:from-violet-500 hover:to-indigo-500'
            }`}
          >
            <Download size={16} />
            {depthScore >= 80 ? '영혼 다운로드 (완성)' : '영혼 다운로드 (진행 중)'}
          </button>
        )}

        {/* Progress hint */}
        <div className={`p-2 rounded border ${isLightMode ? 'bg-amber-50 border-amber-200' : 'bg-void-900/50 border-void-800'}`}>
          <div className={`text-[9px] text-center ${isLightMode ? 'text-amber-600' : 'text-gray-600'}`}>
            {depthScore >= 80
              ? '심층 프로파일링 완료 단계'
              : depthScore >= 60
              ? '무의식 레벨 탐색 중...'
              : depthScore >= 50
              ? '다운로드 가능 - 대화를 계속하면 더 정교해집니다'
              : depthScore >= 40
              ? 'Pro 모델 활성화 - 깊은 분석 진행 중'
              : `기본 정보 수집 중... (${50 - depthScore}% 더 필요)`}
          </div>
        </div>
      </div>
    </div>
  );
};

export default JsonProfilePanel;
