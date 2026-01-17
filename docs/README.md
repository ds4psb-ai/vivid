# Vivid Documentation Index

> **Last Updated**: 2026-01-17
> **Maintainer**: Vivid Team
> **Version**: 4.0 (Post Multi-RAG Router)

---

## 📚 Quick Navigation

### Language Toggle
- 문서 내 `<details>` 섹션에서 한국어/English를 전환합니다. 기본 열림은 한국어입니다.
- Use the `<details>` sections labeled 한국어/English to switch languages. Default open is 한국어.

---

## 🏗️ Core Architecture Documents

| 문서 | 설명 | 상태 |
|------|------|------|
| [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) | Vivid Agent (Chokki) 아키텍처 | ✅ Active |
| [RAG_ARCHITECTURE.md](./RAG_ARCHITECTURE.md) | **Multi-RAG Router + Hybrid Search** | ✅ Active |
| [RAG_RELIABILITY.md](./RAG_RELIABILITY.md) | RAG 시스템 신뢰성 가이드 | ✅ Active |
| [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md) | **앱 개발자 가이드 (React 19)** | ✅ Active |
| [PANEL_DESIGN_UNITY_SPEC.md](./PANEL_DESIGN_UNITY_SPEC.md) | Compound Component System | ✅ Active |
| [UQSL_IMPLEMENTATION_SPEC.md](./UQSL_IMPLEMENTATION_SPEC.md) | Universal Quality Selection Layer | ✅ Active |

---

## 🎯 2026 Planning & Roadmap

| 문서 | 설명 | 상태 |
|------|------|------|
| [2026_PRIORITY_ROADMAP.md](./2026_PRIORITY_ROADMAP.md) | 2026 우선순위 로드맵 | ✅ Active |
| [P0_IMPLEMENTATION_SPEC_2026.md](./P0_IMPLEMENTATION_SPEC_2026.md) | P0 상세 설계서 | ✅ Active |
| [P0_PHASE4_MCP_INTEGRATION_PLAN_2026.md](./P0_PHASE4_MCP_INTEGRATION_PLAN_2026.md) | MCP Gateway 통합 | ✅ Active |
| [ARCHITECTURE_FLEXIBILITY_ANALYSIS_2026.md](./ARCHITECTURE_FLEXIBILITY_ANALYSIS_2026.md) | 아키텍처 유연성 분석 | ✅ Active |
| [DIMENSION_APP_MACRO_PLANNING_2026.md](./DIMENSION_APP_MACRO_PLANNING_2026.md) | Dimension 앱 매크로 플래닝 | ✅ Active |
| [DIMENSION_PANEL_UX_AUDIT_2026.md](./DIMENSION_PANEL_UX_AUDIT_2026.md) | UX 오디트 2026 | ✅ Active |
| [PRE_DEVELOPMENT_CHECKLIST.md](./PRE_DEVELOPMENT_CHECKLIST.md) | 개발 전 체크리스트 | ✅ Active |

---

## 🚀 Dimension Apps (13+)

현재 활성화된 Dimension 앱 목록:

| Dimension | 앱 이름 | 설명 | 상태 |
|-----------|--------|------|------|
| 1D | Prompt Alchemy | 프롬프트 최적화 | ✅ Production |
| 2D | Storyboard Sketcher | 스토리보드 생성 | ✅ Production |
| 3D | Visual Realizer | 이미지 프롬프트 | ✅ Production |
| 4D | Reference Decoder | 레퍼런스 분석 | ✅ Production |
| Story | Story Architect | 시나리오 생성 | ✅ Production |
| AD | Aesthetic Director | 미학 감독 | ✅ Production |
| QC | Quality Director | 품질 감독 | ✅ Production |
| AI | Abyss Mirror | 페르소나 분석 | ✅ Production |
| VEO | Video Maker | VEO 3.1 비디오 | ✅ Production |
| CC | Character Consistency | 캐릭터 일관성 | ✅ Production |
| Suno | Suno AI Music | AI 음악 생성 | ✅ Production |
| Kling | Kling 2.6 Video | 비디오 생성 | ✅ Production |
| Sound | Sound Crafter | 사운드 제작 | 🔧 Development |

> **개발 가이드**: [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md)

---

## 🔬 RAG System (Multi-RAG Router Architecture)

### 2026-01-17 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Vivid Multi-RAG Router Architecture                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐           │
│   │    Query    │───▶│  Multi-RAG Router │───▶│  Backend Pool    │           │
│   │             │    │  (Intelligent)    │    │  (Auto-discover) │           │
│   └─────────────┘    └──────────────────┘    └──────────────────┘           │
│                              │                                               │
│                              ▼                                               │
│   ┌──────────────────────────────────────────────────────────────┐          │
│   │ Route Decision: NotebookLM | Qdrant | Hybrid | Skip          │          │
│   └──────────────────────────────────────────────────────────────┘          │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ L0: Semantic Cache (pgvector + Memory LRU + Redis)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ L1: Hybrid Vector Search                                                     │
│     ├─ Dense (Qdrant, 384-dim, Named Vectors)                               │
│     ├─ Sparse (BM25 Native) ⭐                                               │
│     └─ RRF Fusion (k=60, Weighted)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ L2: NotebookLM Playwright (거장 DNA - 봉준호, 놀란, 빌뇌브, 왕가위, 타란티노)  │
│     └─ Circuit Breaker: 3 failures → 60s cooldown                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ L3: Google Search Grounding (CRAG Pattern)                                   │
│     └─ confidence < 0.5 시 자동 활성화                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RAG Implementation Status (All Complete ✅)

| Phase | 작업 | 상태 |
|-------|------|------|
| P0 | Qdrant Native Sparse | ✅ 완료 |
| P0.5 | Hybrid 컬렉션 마이그레이션 | ✅ 완료 |
| P1 | YAML Manifest 도입 | ✅ 완료 |
| P2 | Backend ABC + Auto-discovery | ✅ 완료 |
| P3 | Ensemble Retriever | ✅ 완료 |
| P4 | Reranker | ✅ 완료 |
| P5 | Adaptive RAG (Query Classification) | ✅ 완료 |
| P6 | Feedback Collection | ✅ 완료 |
| P7 | Multi-RAG Router | ✅ 완료 |

### 검색 품질

| 메트릭 | Dense Only | Dense + BM25 + RRF | 개선율 |
|--------|-----------|-------------------|--------|
| 검색 정확도 | 62% | **91%** | +48% |
| 전문 용어 매칭 | 55% | **95%** | +73% |
| NDCG 점수 | 기준 | +26~31% | ✅ |

---

## 📡 API & Frontend

| 문서 | 설명 | 상태 |
|------|------|------|
| [API_REFERENCE.md](./API_REFERENCE.md) | API 엔드포인트 레퍼런스 | ✅ Active |
| [FRONTEND_COMPONENTS.md](./FRONTEND_COMPONENTS.md) | 프론트엔드 컴포넌트 가이드 | ✅ Active |
| [EVIDENCE_DISPLAY_UX.md](./EVIDENCE_DISPLAY_UX.md) | AI 근거 UI/UX 가이드 | ✅ Active |

### Frontend Tech Stack (2026)

- **Next.js 16** + App Router
- **React 19** (`useTransition`, `useOptimistic`, `startTransition`)
- **TypeScript** Strict Mode
- **Tailwind CSS** + Design Tokens (W3C DTCG 2025.10)
- **i18n** 국제화 지원 (Korean/English)
- **DimensionPanel** Compound Component System

---

## 🔐 Security & Compliance

| 문서 | 설명 | 상태 |
|------|------|------|
| [SECURITY_OVERVIEW.md](./SECURITY_OVERVIEW.md) | 보안 개요 | ✅ Active |
| [SECURITY_CONTROLS_BASELINE.md](./SECURITY_CONTROLS_BASELINE.md) | 보안 통제 기준 | ✅ Active |
| [ACCESS_CONTROL_POLICY.md](./ACCESS_CONTROL_POLICY.md) | 접근 통제 정책 | ✅ Active |
| [AI_RAG_SECURITY_POLICY.md](./AI_RAG_SECURITY_POLICY.md) | AI/RAG 보안 정책 | ✅ Active |
| [DATA_GOVERNANCE_POLICY.md](./DATA_GOVERNANCE_POLICY.md) | 데이터 거버넌스 | ✅ Active |
| [INCIDENT_RESPONSE_AND_BCP.md](./INCIDENT_RESPONSE_AND_BCP.md) | 인시던트 대응 | ✅ Active |
| [SECURE_SDLC_POLICY.md](./SECURE_SDLC_POLICY.md) | 보안 SDLC | ✅ Active |

---

## 🧪 Development & Testing

| 문서 | 설명 | 상태 |
|------|------|------|
| [DEVELOPER_STATUS_GUIDE.md](./DEVELOPER_STATUS_GUIDE.md) | 개발 현황 | ✅ Active |
| [TESTING_GUIDE.md](./TESTING_GUIDE.md) | 테스트 가이드 | ✅ Active |
| [PHASE_MINUS_1_TECHNICAL_FOUNDATION.md](./PHASE_MINUS_1_TECHNICAL_FOUNDATION.md) | 기술 기반 SPEC | ✅ Active |
| [PRE_PHASE_0_IMPLEMENTATION_SPEC.md](./PRE_PHASE_0_IMPLEMENTATION_SPEC.md) | Pre-Phase 0 SPEC | ✅ Active |

### Test Coverage (2026-01-17)

| 영역 | 테스트 수 | 상태 |
|------|---------|------|
| Dimension Apps Security | 653+ | ✅ |
| VEO Video Maker | 85 | ✅ |
| Abyss Mirror | 67 | ✅ |
| Character Consistency | 40+ | ✅ |
| RAG System | 100+ | ✅ |
| UQSL | 124 | ✅ |

---

## 📁 Subdirectories

### `/specs` - Feature Specifications

| 문서 | 설명 |
|------|------|
| [abyss-mirror.md](./specs/abyss-mirror.md) | 심연의 거울 (페르소나 분석) SPEC |
| [TEMPLATE_SPEC.md](./specs/TEMPLATE_SPEC.md) | SPEC 템플릿 |
| [README.md](./specs/README.md) | SPEC 작성 가이드 |

### `/research` - App Research Documents

| 문서 | 설명 |
|------|------|
| [01_ABYSS_MIRROR_RESEARCH.md](./research/01_ABYSS_MIRROR_RESEARCH.md) | Abyss Mirror 리서치 |
| [02_REFERENCE_DECODER_RESEARCH.md](./research/02_REFERENCE_DECODER_RESEARCH.md) | Reference Decoder 리서치 |
| [03_SCENARIO_GENERATOR_RESEARCH.md](./research/03_SCENARIO_GENERATOR_RESEARCH.md) | Scenario Generator 리서치 |
| [04_SOUND_CRAFTER_RESEARCH.md](./research/04_SOUND_CRAFTER_RESEARCH.md) | Sound Crafter 리서치 |
| [05_STORYBOARD_SKETCHER_RESEARCH.md](./research/05_STORYBOARD_SKETCHER_RESEARCH.md) | Storyboard Sketcher 리서치 |
| [06_PROMPT_ALCHEMY_RESEARCH.md](./research/06_PROMPT_ALCHEMY_RESEARCH.md) | Prompt Alchemy 리서치 |
| [07_VISUAL_REALIZER_RESEARCH.md](./research/07_VISUAL_REALIZER_RESEARCH.md) | Visual Realizer 리서치 |
| [08_VIDEO_MAKER_RESEARCH.md](./research/08_VIDEO_MAKER_RESEARCH.md) | Video Maker (VEO) 리서치 |
| [09_QUALITY_DIRECTOR_RESEARCH.md](./research/09_QUALITY_DIRECTOR_RESEARCH.md) | Quality Director 리서치 |
| [10_AESTHETIC_DIRECTOR_RESEARCH.md](./research/10_AESTHETIC_DIRECTOR_RESEARCH.md) | Aesthetic Director 리서치 |

### `/strategic` - Strategic Documents

| 문서 | 설명 |
|------|------|
| [unified_4layer_strategy.md](./strategic/unified_4layer_strategy.md) | 4-Layer 통합 전략 |
| [story_first_architecture_roadmap.md](./strategic/story_first_architecture_roadmap.md) | Story-First 아키텍처 |
| [pj_insights_gap_analysis.md](./strategic/pj_insights_gap_analysis.md) | PJ Insights Gap 분석 |

### `/archive` - Archived Documents (45+ files)

과거 설계 문서 및 참조용 아카이브. 현재 개발에는 사용하지 않음.

| 하위 폴더 | 설명 |
|----------|------|
| `/archive/planning/` | 완료된 플래닝 문서 (Phase 2, RAG 리팩토링 등) |
| `/archive/specs/` | 완료된 SPEC 문서 (P2, P3 Backend) |

---

## 📋 Document Status Legend

| 상태 | 의미 |
|------|------|
| ✅ Active | 현재 개발에 사용 중인 문서 |
| 📎 Reference | 참조용 (수정 불필요) |
| 🔄 Updating | 업데이트 진행 중 |
| 🔧 Development | 개발 진행 중 |
| 📦 Archive | /archive로 이동됨 |

---

## 🔗 Related Documents

- **CLAUDE.md** (프로젝트 루트): Claude Code 설정 및 핵심 규칙
- **backend/CLAUDE.md**: Backend 개발 가이드
- **frontend/CLAUDE.md**: Frontend 개발 가이드
