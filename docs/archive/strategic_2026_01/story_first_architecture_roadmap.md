# 🚀 Arcane 3-Layer Ecosystem 아키텍처 로드맵

> **Status**: ⚠️ Superseded (대체됨)
> **Created**: 2026-01-02
> **Superseded By**: [4-Layer 전략](./unified_4layer_strategy.md)

**목적**: 3-Layer 생태계 (도구 Fork + Human Cloud + RAG 지식) 구현

> [!WARNING]
> 이 문서는 **4-Layer 전략**으로 대체되었습니다.
> 최신 아키텍처는 [unified_4layer_strategy.md](./unified_4layer_strategy.md)를 참조하세요.
> Layer 4 (Trust & Governance)가 추가되었습니다.

## 📚 관련 문서

| 문서 | 역할 | 상태 |
|------|------|------|
| [4-Layer 전략](./unified_4layer_strategy.md) | 현재 정본 | Canonical |
| [PJ 인사이트 분석](./pj_insights_gap_analysis.md) | 배경 분석 | Reference |

---

---

## 📋 전략 전환

```
[이전]                          [현재]
DNA(How) → Shot Contract     →  3-Layer Ecosystem
     ↓                              ↓
   품질 검증                    도구 Fork + Human Cloud + RAG
```

> [!IMPORTANT]
> **핵심 변경**: 단순 검증 도구 → **3-Layer 수익 생태계**로 전환
> - Layer 1: 도구 Fork (Vibe Coding + 수익분배)
> - Layer 2: Human Cloud (의뢰-제작-납품)
> - Layer 3: RAG 지식 (집단지성)

---

## 🎯 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Arcane 3-Layer Ecosystem                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Layer 3: 지식 (Knowledge)                                             │ │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │ │
│  │ │ NotebookLM   │ │ Fork 히스토리│ │ 도구 조합    │                   │ │
│  │ │ RAG          │ │ 분석         │ │ 추천 엔진    │                   │ │
│  │ └──────────────┘ └──────────────┘ └──────────────┘                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                              ▲                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Layer 2: Human Cloud (콘텐츠)                                         │ │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │ │
│  │ │ 의뢰 시스템  │ │ 크리에이터   │ │ 납품/정산   │                   │ │
│  │ │              │ │ 매칭         │ │ 시스템       │                   │ │
│  │ └──────────────┘ └──────────────┘ └──────────────┘                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                              ▲                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Layer 1: 도구 Fork (Tools)                                            │ │
│  │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │ │
│  │ │ 크리에이티브 │ │ 사주/점술   │ │ Fork 관리   │                   │ │
│  │ │ 도구 (3개)   │ │ 도구 (2개)   │ │ + 수익분배   │                   │ │
│  │ └──────────────┘ └──────────────┘ └──────────────┘                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Phase 1: Layer 1 - 도구 Fork (Month 1-2)

### 1.1 핵심 도구 5개 개발 (Vibe Coding)

| 도구 | 기능 | 개발 기간 |
|------|------|:--------:|
| **영상 일관성 엔진** | 장편 씬별 톤/무드 유지 | 2주 |
| **거장 스타일 변환기** | 봉/박/나 스타일 적용 | 2주 |
| **브랜드 DNA 도구** | 광고 브랜드 가이드 | 1주 |
| **타로 해석기** | AI 타로 해석 | 1주 |
| **사주 분석기** | 생년월일 분석 | 1주 |

### 1.2 Fork 시스템 구현

```python
# backend/app/services/fork_manager.py [NEW]

class ForkManager:
    async def create_fork(
        self,
        original_tool_id: str,
        forker_user_id: str,
        customizations: dict
    ) -> Fork:
        """도구 Fork 생성 + 수익분배 설정"""
        pass
    
    async def calculate_revenue_share(
        self,
        fork_id: str,
        revenue: Decimal
    ) -> dict:
        """Fork 깊이에 따른 수익분배 계산"""
        # depth 0: 원작자 60% / 플랫폼 40%
        # depth 1+: 원작자 30% / 이전 Forker 30% / 플랫폼 40%
        pass
```

### 1.3 파일 구조

```
backend/app/
├── routers/
│   └── tools.py              # [NEW] Fork 도구 관리 API
├── services/
│   ├── fork_manager.py       # [NEW] Fork 수익분배
│   └── tool_builder.py       # [NEW] Vibe Coding 도구 생성
├── schemas/
│   └── fork.py               # [NEW] Fork 스키마
```

---

## 📖 Phase 2: Layer 2 - Human Cloud (Month 2-4)

### 2.1 의뢰-매칭-납품 시스템

```python
# backend/app/services/matching_service.py [NEW]

class MatchingService:
    async def create_request(
        self,
        requester_id: str,
        brief: RequestBrief
    ) -> Request:
        """의뢰 생성"""
        pass
    
    async def match_creator(
        self,
        request_id: str
    ) -> Creator:
        """크리에이터 매칭 (포트폴리오 + 도구 역량 기반)"""
        pass
    
    async def complete_delivery(
        self,
        request_id: str,
        deliverables: list
    ) -> Settlement:
        """납품 완료 + 정산 (75/25 분배)"""
        pass
```

### 2.2 저작권 안전 설계

```python
# backend/app/schemas/request.py [NEW]

class DeliveryContract(BaseModel):
    request_id: str
    copyright_owner: str  # 항상 요청자
    creator_id: str
    tools_used: List[str]
    ai_services_used: List[str]  # Veo 3.1, Sora 2 등
    legal_disclaimer: str
```

---

## 📊 Phase 3: Layer 3 - RAG 지식 (Month 4-6)

### 3.1 NotebookLM RAG 통합

```python
# backend/app/services/rag_recommender.py [NEW]

class RAGRecommender:
    async def recommend_inputs(
        self,
        tool_id: str,
        user_context: dict
    ) -> InputRecommendation:
        """도구별 최적 입력값 추천"""
        pass
    
    async def recommend_tool_combo(
        self,
        user_request: str
    ) -> ToolComboRecommendation:
        """도구 조합 노드 추천"""
        pass
```

### 3.2 집단지성 데이터 수집

```python
# backend/app/schemas/collective_intelligence.py [NEW]

class ForkHistory(BaseModel):
    tool_id: str
    fork_chain: List[str]  # Fork 트리
    customizations: List[dict]
    success_metrics: dict

class UsagePattern(BaseModel):
    tool_combo: List[str]
    input_params: dict
    output_quality: float
    user_rating: float
```

---

## 📋 MVP 구현 순서 (12단계)

| # | 항목 | Layer | 기간 |
|---|------|:-----:|:----:|
| 1 | 영상 일관성 엔진 MVP | L1 | 1주 |
| 2 | Fork 시스템 기본 구현 | L1 | 1주 |
| 3 | 거장 스타일 변환기 | L1 | 2주 |
| 4 | 브랜드 DNA 도구 | L1 | 1주 |
| 5 | 타로/사주 도구 | L1 | 1주 |
| 6 | Human Cloud MVP | L2 | 2주 |
| 7 | 크리에이터 매칭 | L2 | 1주 |
| 8 | 납품/정산 시스템 | L2 | 1주 |
| 9 | RAG 기본 연동 | L3 | 2주 |
| 10 | 입력값 추천 | L3 | 1주 |
| 11 | 도구 조합 추천 | L3 | 2주 |
| 12 | 집단지성 대시보드 | L3 | 1주 |

---

## 🗂️ 전체 파일 구조 변경

```
backend/app/
├── routers/
│   ├── teaching.py           # [기존] Teaching Tools
│   ├── tools.py              # [NEW] Fork 도구 관리
│   ├── humancloud.py         # [NEW] 의뢰-매칭-납품
│   └── knowledge.py          # [NEW] RAG 추천 API
├── services/
│   ├── fork_manager.py       # [NEW] Fork 수익분배
│   ├── tool_builder.py       # [NEW] Vibe Coding 도구 생성
│   ├── matching_service.py   # [NEW] 크리에이터 매칭
│   ├── settlement_service.py # [NEW] 납품 정산
│   └── rag_recommender.py    # [NEW] RAG 추천
├── schemas/
│   ├── fork.py               # [NEW] Fork 스키마
│   ├── request.py            # [NEW] 의뢰 스키마
│   └── collective_intelligence.py # [NEW] 집단지성 스키마
```

---

## 🎯 성공 지표

| 지표 | 2개월 | 6개월 | 12개월 |
|------|:-----:|:-----:|:------:|
| 도구 수 | 5 | 10 | 30 |
| Fork 수 | 50 | 500 | 2,000 |
| Human Cloud 의뢰 | 20 | 300 | 1,000 |
| RAG 추천 사용 | 100/일 | 1,000/일 | 5,000/일 |
| 월 수익 | ₩10M | ₩15M | ₩50M |

---

## 🔥 즉시 실행 (Week 1)

| 우선순위 | 액션 | 담당 |
|:--------:|------|:----:|
| 🔴 P0 | 영상 일관성 엔진 MVP | Dev |
| 🔴 P0 | Fork 수익분배 계약 설계 | Legal |
| 🔴 P0 | Human Cloud 플랫폼 MVP | Dev |
| 🟠 P1 | 거장 스타일 변환기 | Dev |
| 🟠 P1 | 크리에이터 10명 모집 | BD |
