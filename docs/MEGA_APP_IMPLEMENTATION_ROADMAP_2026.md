# Mega App Implementation Roadmap 2026

> **Version**: 2.0
> **Date**: 2026-01-28
> **Status**: 🔄 2026-H2 통합 아키텍처 구현 중
> **SSoT Reference**: [MEGA_APP_ARCHITECTURE_2026.md](./MEGA_APP_ARCHITECTURE_2026.md)

---

## Executive Summary

### 기존 (Phase 1-4 완료)

18개 Dimension 앱 → 3개 메가앱 통합 + VPE 신규 모듈 구현 ✅

### 신규 (Phase 1.x-2.x 진행)

**2026-H2 통합 아키텍처**: 독립 4개 앱 → **Saga 패턴 파이프라인 + 학습 가능한 시스템**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DNA Lab 통합 파이프라인 (Saga)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  [VPE] ──→ [AD] ──→ [Mirror] ──→ [QC]                                  │
│    ↓         ↓         ↓          ↓                                    │
│  Logic   Aesthetic  Persona    Quality                                 │
│  Vector  Guidelines   DNA      Report                                  │
│    │         │         │          │                                    │
│    └─────────┴────┬────┴──────────┘                                    │
│                   ↓                                                     │
│            DNALabResult                                                │
│                   ↓                                                     │
│    ┌──────────────┼──────────────┐                                     │
│    ↓              ↓              ↓                                     │
│ [Outbox]    [Transpiler]   [Drift Detection]                          │
│    ↓              ↓              ↓                                     │
│ Qdrant Sync  Veo/Kling    HITL Dashboard                               │
└─────────────────────────────────────────────────────────────────────────┘
```

**4-D DNA 통합 현황**:
| DNA 축 | 기술 기반 | 상태 |
|--------|----------|:----:|
| 거장 DNA | Qdrant 10개 컬렉션 | ✅ |
| 영상 DNA | VPE + Multimodal RAG | ✅ |
| 유저 DNA | PersonaMem-v2 + **Big Five (OCEAN)** | 🔄 |
| IP DNA | MegaNova + **Logic Vector Versioning** | 🔄 |

---

## Phase 1: VPE 신규 구축 (2주)

### 1.1 파일 구조

| 파일 | 역할 |
|------|------|
| `backend/app/schemas/vpe.py` | LogicVector, VPEParseRequest/Response 스키마 |
| `backend/app/services/vpe_service.py` | Gemini 3 Pro 영상 분석 서비스 |
| `backend/app/services/vpe_storage.py` | Qdrant Logic Vector 저장 |
| `backend/app/routers/vpe.py` | `/api/vpe/parse` 엔드포인트 |
| `config/apps/content/dimensions/vpe.yaml` | VPE SSoT 설정 |
| `backend/tests/routers/test_vpe.py` | 테스트 (15+ 케이스) |

### 1.2 VPE Schemas

```python
# backend/app/schemas/vpe.py

from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class LogicVector(BaseModel):
    """VPE 핵심 출력 - 거장 DNA 구조."""
    auteur_id: str
    cadence: Dict[str, Any]        # hook/build/climax timing
    composition: Dict[str, Any]    # primary_strategy, symmetry_score
    camera_grammar: Dict[str, float]  # dolly, handheld, push_in 비율
    lighting_physics: Dict[str, Any]  # key_light, color_temp_range
    color_science: Dict[str, Any]     # lut_reference, palette

class VPEParseRequest(BaseModel):
    video_uri: str                 # gs:// or https://
    auteur_hint: Optional[str] = None
    extract_shots: bool = True
    store_to_qdrant: bool = True

class VPEParseResponse(BaseModel):
    success: bool
    trace_id: str
    logic_vector: Optional[LogicVector] = None
    shots: Optional[List[Dict]] = None  # shot-by-shot analysis
    evidence_refs: List[str] = []
    confidence: float = 0.0
    qdrant_doc_id: Optional[str] = None
    error: Optional[str] = None
```

### 1.3 VPE Service

> **패턴 참조**: `backend/app/services/veo_service.py` (async polling, dataclass)

```python
# backend/app/services/vpe_service.py

VPE_SYSTEM_PROMPT = """당신은 영화 분석 전문가입니다.
영상을 분석하여 Logic Vector를 추출하세요.

분석 항목:
1. CADENCE: 샷 길이 평균, 리듬 패턴, 템포
2. COMPOSITION: 구도 전략 (vertical_blocking, rule_of_thirds 등)
3. CAMERA_GRAMMAR: 카메라 움직임 비율 (dolly, handheld, static 등)
4. LIGHTING_PHYSICS: 조명 스타일, 색온도 범위
5. COLOR_SCIENCE: LUT 참조, 팔레트 색상

JSON 형식으로만 출력하세요."""

class VPEService:
    async def parse_video(
        self,
        video_uri: str,
        auteur_hint: Optional[str] = None,
    ) -> VPEParseResponse:
        # 1. Gemini 3 Pro video understanding API 호출
        # 2. LogicVector 파싱
        # 3. evidence_refs 생성
        # 4. Qdrant 저장 (optional)
```

### 1.4 VPE Router

> **패턴 참조**: `backend/app/routers/dimension/_base.py` (execute_dimension_tool)

```python
# backend/app/routers/vpe.py

router = APIRouter(prefix="/api/vpe", tags=["VPE"])

@router.post("/parse", response_model=VPEParseResponse)
async def parse_video(
    request: VPEParseRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VPEParseResponse:
    # Credit deduction (50 credits)
    # VPE service 호출
    # Refund on failure
```

### 1.5 VPE YAML Config

```yaml
# config/apps/content/dimensions/vpe.yaml

$schema: "vivid-app/v2"
metadata:
  name: vpe
  type: dimension
  version: "1.0.0"

display:
  name_ko: "비디오 파싱 엔진"
  name_en: "Video Parsing Engine"
  icon: "🎥"

capabilities:
  - name: execution
    config:
      credit_cost: 50
      endpoint: "/api/vpe/parse"
      capsule_key: "vpe.video.parse"
```

---

## Phase 2: DNA Lab 통합 (1주)

### 2.1 파일 구조

```
backend/app/routers/dna_lab/
├── __init__.py
├── router.py          # DNA Lab 통합 라우터
└── _utils.py          # 공통 유틸

backend/app/services/
└── dna_lab_service.py # 오케스트레이션 서비스
```

### 2.2 DNA Lab Service

```python
# backend/app/services/dna_lab_service.py

@dataclass
class DNALabResult:
    success: bool
    trace_id: str
    logic_vector: Optional[LogicVector] = None
    aesthetic_guidelines: Optional[Dict] = None
    persona_dna: Optional[Dict] = None
    quality_score: Optional[float] = None
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0

class DNALabService:
    async def extract_dna(
        self,
        video_uri: Optional[str] = None,
        concept: Optional[str] = None,
        auteur_key: Optional[str] = None,
        components: List[str] = ["ad"],  # vpe, ad, mirror, qc
    ) -> DNALabResult:
        # 선택된 컴포넌트만 실행
        # Logic Vector 병합
        # evidence_refs 집계
```

### 2.3 DNA Lab Router

```python
# backend/app/routers/dna_lab/router.py

router = APIRouter(prefix="/api/dna-lab", tags=["DNA Lab"])

@router.post("/extract")
async def extract_dna(request: DNALabRequest, ...):
    # components 기반 실행
    # credit = sum(component_costs)

@router.post("/vpe/parse")   # VPE 직접 접근
@router.post("/aesthetic")   # AD 직접 접근
@router.post("/mirror")      # Mirror 직접 접근
@router.post("/quality")     # QC 직접 접근
```

### 2.4 기존 라우터 리디렉션

```python
# backend/app/routers/dimension/aesthetic.py

@router.post("/aesthetic/direct")
async def aesthetic_direct(...):
    # 기존 로직 유지 (backward compatibility)
    # Deprecation warning 추가
```

---

## Phase 3: Story Engine 통합 (1.5주)

### 3.1 파일 구조

```
backend/app/routers/story_engine/
├── __init__.py
├── router.py              # Story Engine 통합 라우터
├── system_prompt.py       # System Prompt Generator
└── _utils.py

backend/app/services/
└── story_engine_service.py
```

### 3.2 System Prompt Generator

> **핵심 기능**: Logic Vector → Shot Grammar System Prompt 변환

```python
# backend/app/routers/story_engine/system_prompt.py

class SystemPromptGenerator:
    def generate(
        self,
        logic_vector: LogicVector,
        story_structure: Dict,
        target_platform: str = "veo",
    ) -> str:
        """
        Logic Vector + Story Structure → Platform-specific System Prompt
        
        Example output:
        "You are a director following Bong Joon-ho's style.
         Camera: 35% dolly, 15% handheld, 2% push-in
         Lighting: low-key, 3200-5600K
         Composition: vertical_blocking with 0.74 symmetry
         Pacing: hook at 0.3s, build at 0.5s, climax at 3.5s"
        """
```

### 3.3 Story Engine Router

```python
# backend/app/routers/story_engine/router.py

router = APIRouter(prefix="/api/story-engine", tags=["Story Engine"])

@router.post("/generate")
async def generate_story(request: StoryEngineRequest, ...):
    # Story 생성 + System Prompt 생성

@router.post("/story")         # Story Architect 직접 접근
@router.post("/prompt")        # Prompt Alchemy 직접 접근
@router.post("/system-prompt") # System Prompt 생성만
```

---

## Phase 4: Production Bridge (0.5주)

### 4.1 파일 구조

```
backend/app/routers/production/
├── __init__.py
├── router.py              # Production Bridge 통합 라우터
├── providers/
│   ├── __init__.py
│   ├── base.py            # BaseProvider ABC
│   ├── veo.py             # VEO Provider
│   ├── kling.py           # Kling Provider
│   └── suno.py            # Suno Provider
└── _utils.py

backend/app/services/
└── production_bridge_service.py
```

### 4.2 Provider Interface

```python
# backend/app/routers/production/providers/base.py

class MediaType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"

@dataclass
class GenerationRequest:
    prompt: str
    negative_prompt: Optional[str] = None
    duration_seconds: Optional[int] = None
    aspect_ratio: str = "16:9"
    system_prompt: Optional[str] = None  # DNA Lab에서 받은 System Prompt

@dataclass
class GenerationResult:
    success: bool
    provider: str
    media_uri: Optional[str] = None
    trace_id: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    credits_used: int = 0
    error: Optional[str] = None

class BaseProvider(ABC):
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        pass
    
    @abstractmethod
    def calculate_credits(self, request: GenerationRequest) -> int:
        pass
```

### 4.3 Production Bridge Service

```python
# backend/app/services/production_bridge_service.py

class ProductionBridgeService:
    providers = {
        "veo": VeoProvider(),
        "kling": KlingProvider(),
        "suno": SunoProvider(),
        "imagen": ImagenProvider(),
    }
    
    async def generate(
        self,
        provider: str,
        request: GenerationRequest,
    ) -> GenerationResult:
        return await self.providers[provider].generate(request)
    
    async def generate_best(
        self,
        request: GenerationRequest,
        media_type: MediaType,
    ) -> GenerationResult:
        # 자동 provider 선택 (비용/품질 기준)
```

---

## Phase 5: Frontend 통합 (0.5주)

### 5.1 새 페이지 생성

| 경로 | 컴포넌트 |
|------|----------|
| `/dna-lab` | DNA Lab Hub (탭: VPE, AD, Mirror, QC) |
| `/story-engine` | Story Engine Hub (탭: Story, Prompt) |
| `/production` | Production Bridge Hub (탭: VEO, Kling, Suno) |

### 5.2 Legacy 리디렉션

```typescript
// frontend/src/middleware.ts

const LEGACY_REDIRECTS: Record<string, string> = {
  "/dimension/aesthetic": "/dna-lab?tab=ad",
  "/dimension/abyss-mirror": "/dna-lab?tab=mirror",
  "/dimension/quality-check": "/dna-lab?tab=qc",
  "/dimension/story-architect": "/story-engine?tab=story",
  "/dimension/prompt": "/story-engine?tab=prompt",
  "/dimension/video-maker": "/production?provider=veo",
  "/dimension/kling": "/production?provider=kling",
  "/dimension/suno": "/production?provider=suno",
};
```

### 5.3 dimension-data.ts 업데이트

```typescript
// frontend/src/config/dimension-data.ts

export const MEGA_APPS = {
  "dna-lab": {
    name: "DNA Lab",
    icon: "🧬",
    modules: ["vpe", "ad", "mirror", "qc"],
  },
  "story-engine": {
    name: "Story Engine",
    icon: "📝",
    modules: ["story", "prompt"],
  },
  "production": {
    name: "Production Bridge",
    icon: "🎬",
    providers: ["veo", "kling", "suno", "imagen"],
  },
};
```

---

## Critical Files Reference

| 파일 | 참조 용도 |
|------|----------|
| `backend/app/dimension_adapter.py` | CapsuleResult, handler 패턴 |
| `backend/app/services/veo_service.py` | async polling, dataclass 패턴 |
| `backend/app/routers/dimension/_base.py` | execute_dimension_tool, SSE 패턴 |
| `backend/app/rag/tier1_dimension_rag.py` | Qdrant 저장 패턴 |
| `docs/MEGA_APP_ARCHITECTURE_2026.md` | SSoT 아키텍처 문서 |

---

## Verification Plan

### 자동화된 테스트

```bash
# 1. VPE 테스트
pytest backend/tests/routers/test_vpe.py -v

# 2. DNA Lab 테스트
pytest backend/tests/routers/test_dna_lab.py -v

# 3. Story Engine 테스트
pytest backend/tests/routers/test_story_engine.py -v

# 4. Production Bridge 테스트
pytest backend/tests/routers/test_production_bridge.py -v

# 5. 전체 검증
cd backend && source venv/bin/activate && pytest --tb=short -q
cd frontend && npm run build
```

### 수동 검증

1. **VPE 품질**: "기생충" 3분 클립 분석 → Logic Vector 품질 확인
2. **System Prompt**: DNA Lab → Story Engine → VEO 생성 플로우
3. **Production Bridge**: VEO → Kling 교체 시 Story Engine 코드 변경 없음

---

## Implementation Order

```
Phase 1: VPE schemas → VPE service → VPE router → VPE tests
    │
    ▼
Phase 2: DNA Lab service → DNA Lab router → DNA Lab tests
    │
    ▼
Phase 3: System Prompt Generator → Story Engine service → Story Engine tests
    │
    ▼
Phase 4: Provider interface → Production Bridge service → Production Bridge tests
    │
    ▼
Phase 5: Frontend 3 mega app pages → Legacy redirects
```

---

## 관련 문서

| 문서 | 역할 |
|------|------|
| [MEGA_APP_ARCHITECTURE_2026.md](./MEGA_APP_ARCHITECTURE_2026.md) | SSoT 아키텍처 |
| [SSOT_DECISIONS_LOG.md](./SSOT_DECISIONS_LOG.md) | Decision 011 |
| [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md) | 앱 개발 가이드 |

---

*Created: 2026-01-26 by Development Team*
