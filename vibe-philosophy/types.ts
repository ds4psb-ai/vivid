
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

// ===== 레거시 심연의 거울 확장 타입 =====
export interface PrimalDrives {
  libido_direction: string;      // 삶/창조/성적 에너지의 방향
  thanatos_manifestation: string; // 죽음/파괴/안식 본능의 발현
}

export interface EnvironmentalResistance {
  trigger_points: string[];      // '감옥'을 느끼게 하는 트리거
  rebellion_style: string;        // 저항 양식
}

export interface FamilyHistory {
  paternal_influence: string;
  maternal_influence: string;
  genetic_factors: string[];
}

export interface LifeTrajectory {
  childhood_imprints: string[];
  family_history: FamilyHistory;
  career_path: string[];
  turning_points: string[];
  current_status: string;
}

export interface CulturalContext {
  era_definition: string;         // 세대 정의
  social_taboos_broken: string[]; // 깨뜨린 금기들
  legacy_archetype: string;       // 레거시 원형
  fandom_dynamics: string;        // 추종 세력 역학
}

export interface ArtisticMethodology {
  obsession_points: string[];
  ritual_routine: string[];
  perfectionism_scope: string;
  collaboration_style: string;
}

export interface SignatureStyle {
  visual_motifs: string[];
  auditory_signatures: string[];
  narrative_structure: string;
  genre_fusion: string[];
}

export interface SensoryArchitecture {
  dominant_sense: string;
  synesthesia_tendency: boolean;
  rhythm_perception: string;
  space_perception: string;
}

export interface MasterAttributes {
  artistic_methodology: ArtisticMethodology;
  signature_style: SignatureStyle;
  sensory_architecture: SensoryArchitecture;
}

// ===== 바이브 철학관 페르소나 (레거시 심연의 거울 방식) =====
export interface VibePhilosophyPersona {
  meta: {
    depth_level: number;
    profiling_status: 'not_started' | 'in_progress' | 'complete';
    current_model: 'flash' | 'pro';
    turn_count: number;
  };
  demographics: {
    name: string;
    age: number | null;
    birth_date: string;
    blood_type: string;
    mbti_self_report: string;
    mbti_analyzed: string;
    gender: 'male' | 'female' | 'other' | '';
    residence: string;
  };
  face_reading: {
    raw_features: string;
    eyes: { shape: string; energy: string; fortune: string };
    nose: { shape: string; energy: string; fortune: string };
    mouth: { shape: string; energy: string; communication_style: string };
    forehead: { shape: string; energy: string; fortune: string };
    chin: { shape: string; energy: string; fortune: string };
    face_shape: string;
    overall_qi: string;
  };
  saju_analysis: {
    four_pillars: {
      year: { stem: string; branch: string } | null;
      month: { stem: string; branch: string } | null;
      day: { stem: string; branch: string } | null;
      hour: { stem: string; branch: string } | null;
    };
    five_elements_balance: { wood: number; fire: number; earth: number; metal: number; water: number };
    day_master: string;
    day_master_strength: 'strong' | 'weak' | 'balanced' | '';
    ten_gods: string[];
    current_year_luck: string;
  };
  cognitive_architecture: {
    mbti_analyzed: string;
    cognitive_stack: string[];
    attention_mechanism: string;
    decision_heuristics: string;
  };
  emotional_landscape: {
    core_values: string[];
    deepest_fears: string[];
    emotional_triggers_positive: string[];
    emotional_triggers_negative: string[];
    primary_desires: string[];
    trauma_response: string;
    attachment_style: 'secure' | 'anxious' | 'avoidant' | 'disorganized' | '';
  };
  psychological_entropy: {
    shadow_self: {
      repressed_desires: string[];
      inferiority_complex: string;
    };
    existential_paradox: {
      conflict_a: string;
      conflict_b: string;
    };
    defense_mechanisms: {
      dominant_strategy: string;
      specific_behaviors: string[];  // 🔥 레거시 핵심! 구체적 행동 분석 (최소 3개 이상)
      vulnerability_trigger: string;
    };
    primal_drives: PrimalDrives;  // 🔥 리비도/타나토스 분석
    environmental_resistance: EnvironmentalResistance;  // 🔥 환경 저항
    mythological_script: {
      hero_journey_stage: string;
      tragic_flaw: string;
      redemption_arc: string;
      current_enactment: string;  // 🔥 현재 연기 중인 신화
    };
  };
  subconscious_symbolism: {
    recurring_dreams: string[];
    archetypal_identification: string;
    liminal_patterns: string[];
  };
  // 🔥 레거시 확장 필드
  life_trajectory: LifeTrajectory;
  cultural_context: CulturalContext;
  master_attributes: MasterAttributes;
}

// 초기 페르소나 상태
export const INITIAL_PERSONA: VibePhilosophyPersona = {
  meta: {
    depth_level: 0,
    profiling_status: 'not_started',
    current_model: 'flash',
    turn_count: 0,
  },
  demographics: {
    name: '',
    age: null,
    birth_date: '',
    blood_type: '',
    mbti_self_report: '',
    mbti_analyzed: '',
    gender: '',
    residence: '',
  },
  face_reading: {
    raw_features: '',
    eyes: { shape: '', energy: '', fortune: '' },
    nose: { shape: '', energy: '', fortune: '' },
    mouth: { shape: '', energy: '', communication_style: '' },
    forehead: { shape: '', energy: '', fortune: '' },
    chin: { shape: '', energy: '', fortune: '' },
    face_shape: '',
    overall_qi: '',
  },
  saju_analysis: {
    four_pillars: { year: null, month: null, day: null, hour: null },
    five_elements_balance: { wood: 0, fire: 0, earth: 0, metal: 0, water: 0 },
    day_master: '',
    day_master_strength: '',
    ten_gods: [],
    current_year_luck: '',
  },
  cognitive_architecture: {
    mbti_analyzed: '',
    cognitive_stack: [],
    attention_mechanism: '',
    decision_heuristics: '',
  },
  emotional_landscape: {
    core_values: [],
    deepest_fears: [],
    emotional_triggers_positive: [],
    emotional_triggers_negative: [],
    primary_desires: [],
    trauma_response: '',
    attachment_style: '',
  },
  psychological_entropy: {
    shadow_self: {
      repressed_desires: [],
      inferiority_complex: '',
    },
    existential_paradox: {
      conflict_a: '',
      conflict_b: '',
    },
    defense_mechanisms: {
      dominant_strategy: '',
      specific_behaviors: [],  // 🔥 구체적 행동 분석
      vulnerability_trigger: '',
    },
    primal_drives: {
      libido_direction: '',
      thanatos_manifestation: '',
    },
    environmental_resistance: {
      trigger_points: [],
      rebellion_style: '',
    },
    mythological_script: {
      hero_journey_stage: '',
      tragic_flaw: '',
      redemption_arc: '',
      current_enactment: '',
    },
  },
  subconscious_symbolism: {
    recurring_dreams: [],
    archetypal_identification: '',
    liminal_patterns: [],
  },
  // 🔥 레거시 확장 필드
  life_trajectory: {
    childhood_imprints: [],
    family_history: {
      paternal_influence: '',
      maternal_influence: '',
      genetic_factors: [],
    },
    career_path: [],
    turning_points: [],
    current_status: '',
  },
  cultural_context: {
    era_definition: '',
    social_taboos_broken: [],
    legacy_archetype: '',
    fandom_dynamics: '',
  },
  master_attributes: {
    artistic_methodology: {
      obsession_points: [],
      ritual_routine: [],
      perfectionism_scope: '',
      collaboration_style: '',
    },
    signature_style: {
      visual_motifs: [],
      auditory_signatures: [],
      narrative_structure: '',
      genre_fusion: [],
    },
    sensory_architecture: {
      dominant_sense: '',
      synesthesia_tendency: false,
      rhythm_perception: '',
      space_perception: '',
    },
  },
};

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
