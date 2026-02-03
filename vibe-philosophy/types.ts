
export type Role = 'user' | 'model';

export type AnalysisMode = 'integrated' | 'blood' | 'mbti' | 'saju' | 'face' | 'couple';

// 심도 단계 타입 (6단계 확장)
export type DepthStage =
  | 'exploration'   // 0-25%: 라포 형성
  | 'development'   // 26-45%: 표면 고민
  | 'subconscious'  // 46-65%: 잠재의식 (NEW)
  | 'unconscious'   // 66-85%: 무의식 (NEW)
  | 'archetypal'    // 86-95%: 원형 통합 (NEW)
  | 'resolution';   // 96-100%: 최종 합성

// 레거시 호환용 4단계 (기존 코드 호환)
export type DepthStageLegacy = 'exploration' | 'development' | 'deep' | 'resolution';

export interface Message {
  id: string;
  role: Role;
  text: string;
  timestamp: Date;
  isThinking?: boolean;
}

export type CalendarType = 'solar' | 'lunar';

// ===== HEXACO 성격 모델 타입 =====
export interface HEXACOFacet {
  score: number; // 0-100
  description: string;
}

export interface HEXACODimension {
  score: number; // 0-100
  facets: {
    sincerity: HEXACOFacet;
    fairness: HEXACOFacet;
    greedAvoidance: HEXACOFacet;
    modesty: HEXACOFacet;
  };
}

export interface BigFiveDimension {
  score: number; // 0-100
  facets: string[];
}

export interface PersonalityArchitecture {
  bigFive: {
    openness: BigFiveDimension;
    conscientiousness: BigFiveDimension;
    extraversion: BigFiveDimension;
    agreeableness: BigFiveDimension;
    neuroticism: BigFiveDimension;
  };
  hexacoExtension: {
    honestyHumility: HEXACODimension;
  };
}

// ===== 동양철학 타입 =====
export type FiveElement = 'wood' | 'fire' | 'earth' | 'metal' | 'water';
export type HeavenlyStem = '甲' | '乙' | '丙' | '丁' | '戊' | '己' | '庚' | '辛' | '壬' | '癸';
export type EarthlyBranch = '子' | '丑' | '寅' | '卯' | '辰' | '巳' | '午' | '未' | '申' | '酉' | '戌' | '亥';
export type TenGod = '비겁' | '식상' | '재성' | '관성' | '인성' | '편인' | '정인' | '편관' | '정관' | '편재' | '정재' | '식신' | '상관';

export interface Pillar {
  stem: HeavenlyStem;
  branch: EarthlyBranch;
  hiddenStems: HeavenlyStem[];
  element: FiveElement;
}

export interface FiveElementsBalance {
  wood: number;  // 0.0 - 1.0
  fire: number;
  earth: number;
  metal: number;
  water: number;
}

export interface SajuAnalysis {
  fourPillars: {
    year: Pillar;
    month: Pillar;
    day: Pillar;
    hour: Pillar | null; // 시간 모를 경우 null
  };
  fiveElementsBalance: FiveElementsBalance;
  tenGods: TenGod[];
  dayMaster: HeavenlyStem;
  dayMasterStrength: 'strong' | 'weak' | 'balanced';
  majorLuckCycles: string[]; // 대운
  currentYearLuck: string;   // 세운
}

// ===== 구조화된 관상 분석 타입 =====
export interface FacialFeature {
  shape: string;
  energy: string;
  fortuneIndicator?: string;
}

export interface StructuredFaceReading {
  eyes: FacialFeature & { leftRight?: string };
  eyebrows: FacialFeature;
  nose: FacialFeature;
  mouth: FacialFeature & { communicationStyle?: string };
  ears: FacialFeature;
  faceShape: string;
  forehead: FacialFeature;
  chin: FacialFeature;
  overallQi: string;
  personalityInference: string;
}

// ===== 동양철학 통합 타입 =====
export interface EasternMetaphysics {
  sajuAnalysis: SajuAnalysis;
  faceReading: StructuredFaceReading;
}

export interface PersonData {
  name: string;
  birthDate: string; // YYYY-MM-DD
  calendarType: CalendarType; // Added: Solar or Lunar
  birthTime: string; // HH:mm
  birthPlace: string;
  bloodType: string;
  mbti: string;
  gender: 'male' | 'female' | 'other';
  faceFeatures?: string; // Pre-analyzed text description of the face
  structuredFaceReading?: StructuredFaceReading; // 구조화된 관상 분석
  sajuAnalysis?: SajuAnalysis; // 구조화된 사주 분석
}

export interface UserProfile extends PersonData {
  residence: string; // Current residence
  faceImage?: string; // Transient Base64 string (Deleted immediately after analysis)
  partner?: PersonData; // Partner data including faceFeatures
}

export interface SystemPromptConfig {
  mode: AnalysisMode;
  userProfile: UserProfile;
}

export interface ChatState {
  depthScore: number; // 0 to 100
  isReadyForRevelation: boolean; // true if score >= 70
  currentStage: DepthStage; // 현재 심도 단계
}

// ===== 디지털 트윈 확장 타입 =====
export interface DigitalTwinData {
  cognitiveArchitecture: {
    attentionMechanism: string;
    decisionHeuristics: string;
    iqRange: string;
    mbti: { type: string; certainty: number };
  };
  personalityArchitecture: PersonalityArchitecture;
  easternMetaphysics: EasternMetaphysics;
  creativeDna: {
    aestheticPreferences: string[];
    creativeTriggers: string[];
    inspirationSources: string[];
    outputMediums: string[];
  };
  emotionalLandscape: {
    coreValues: string[];
    deepestFears: string[];
    emotionalTriggers: { positive: string[]; negative: string[] };
    primaryDesires: string[];
    traumaResponse: string;
  };
  psychologicalEntropy: {
    defenseMechanisms: { dominantStrategy: string; vulnerabilityTrigger: string };
    existentialParadox: { conflictA: string; conflictB: string };
    shadowSelf: { repressedDesires: string[]; inferiorityComplex: string };
  };
}

// ===== 실시간 프로파일 데이터 (JSON 패널용) =====
export interface LiveProfileData {
  // 메타 정보
  meta: {
    currentDepth: number;
    currentStage: DepthStage;
    currentModel: 'flash' | 'pro';
    turnCount: number;
    sessionStartTime: Date;
  };
  // 추출된 키워드/감정
  extracted: {
    emotionalKeywords: string[];
    topicKeywords: string[];
    relationshipMentions: string[];
    deepSignals: string[];
  };
  // 사주/관상 요약 (프로필에서)
  profileSummary: {
    fiveElementsShort: string; // "목↑ 화↓ 토= 금↑ 수↓"
    dominantTenGod: string;
    faceReadingSummary: string;
    mbtiCognitive: string;
  };
  // 심층 분석 (50% 이상)
  depthAnalysis?: {
    dominantArchetype: string;
    shadowAspects: string[];
    attachmentStyle: string;
    coreComplex: string;
  };
}

// ===== 확장된 디지털 트윈 V2 (무의식/잠재의식 레벨) =====
export interface NeurologicalSignature {
  dominantHemisphere: 'left' | 'right' | 'balanced';
  limbicReactivity: {
    triggers: string[];
    soothing: string[];
  };
  prefrontalCharacteristics: {
    impulseControl: number; // 0-100
  };
}

export interface DepthPsychologicalProfile {
  consciousSelf: {
    persona: string;
    egoStrength: number; // 0-100
  };
  personalUnconscious: {
    complexes: Array<{
      name: string;
      intensity: number; // 0-100
      origin: string;
    }>;
    shadowAspects: {
      disownedTraits: string[];
      integrationLevel: number; // 0-100
    };
  };
  collectiveUnconscious: {
    dominantArchetypes: Array<{
      name: string;
      activation: number; // 0-100
    }>;
    mythologicalResonance: string;
  };
}

export interface AttachmentArchitecture {
  primaryStyle: 'secure' | 'anxious' | 'avoidant' | 'disorganized';
  abandonmentSensitivity: number; // 0-100
  intimacyTolerance: number; // 0-100
}

export interface ExistentialCoordinates {
  meaningFramework: {
    coreValues: string[];
    purpose: string;
  };
  mortalityRelationship: {
    deathAnxiety: number; // 0-100
  };
}

export interface DigitalTwinDataV2 extends DigitalTwinData {
  neurologicalSignature?: NeurologicalSignature;
  depthPsychologicalProfile?: DepthPsychologicalProfile;
  attachmentArchitecture?: AttachmentArchitecture;
  existentialCoordinates?: ExistentialCoordinates;
}
