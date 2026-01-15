# Vivid Documentation Index

> **Last Updated**: 2026-01-15  
> **Maintainer**: Vivid Team

---

## 📚 Quick Navigation

### Core Architecture
| 문서 | 설명 | 상태 |
|------|------|------|
| [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) | Vivid Agent (Chokki) 아키텍처 | ✅ Active |
| [RAG_RELIABILITY.md](./RAG_RELIABILITY.md) | **RAG 시스템 신뢰성 가이드** | ✅ Active |
| [DIMENSION_APP_DEVELOPER_GUIDE.md](./DIMENSION_APP_DEVELOPER_GUIDE.md) | 앱 개발자 가이드 | ✅ Active |

### RAG System (Plugin-Registry Architecture)
| 문서 | 설명 | 상태 |
|------|------|------|
| [RAG_RELIABILITY.md](./RAG_RELIABILITY.md) | **아키텍처 + 운영 가이드 (SSoT)** | ✅ Active |
| [RAG_QUALITY.md](./RAG_QUALITY.md) | 품질 평가 파이프라인 | ✅ Active |
| [RAG_NEXT_PHASE_PLAN_2026-01-11.md](./RAG_NEXT_PHASE_PLAN_2026-01-11.md) | 실행 계획 (P7 Plugin-Registry 포함) | ✅ Active |
| [RAG_REFACTOR_FINAL_PLAN_2026-01-11.md](./RAG_REFACTOR_FINAL_PLAN_2026-01-11.md) | 리팩토링 설계 문서 | 📎 Reference |
| [RAG_WORKFLOW_PLATFORM_BENCHMARKING.md](./RAG_WORKFLOW_PLATFORM_BENCHMARKING.md) | 워크플로우 벤치마킹 | 📎 Reference |
| [NOTEBOOKLM_PLAYWRIGHT.md](./NOTEBOOKLM_PLAYWRIGHT.md) | NotebookLM 자동화 가이드 | ✅ Active |

### API & Frontend
| 문서 | 설명 | 상태 |
|------|------|------|
| [API_REFERENCE.md](./API_REFERENCE.md) | API 엔드포인트 레퍼런스 | ✅ Active |
| [FRONTEND_COMPONENTS.md](./FRONTEND_COMPONENTS.md) | 프론트엔드 컴포넌트 가이드 | ✅ Active |
| [EVIDENCE_DISPLAY_UX.md](./EVIDENCE_DISPLAY_UX.md) | AI 근거 UI/UX 가이드 | ✅ Active |

### Development & Testing
| 문서 | 설명 | 상태 |
|------|------|------|
| [DEVELOPER_STATUS_GUIDE.md](./DEVELOPER_STATUS_GUIDE.md) | 개발 현황 및 Known Issues | ✅ Active |
| [TESTING_GUIDE.md](./TESTING_GUIDE.md) | 테스트 가이드 | ✅ Active |
| [APP_RENAMING_AND_DEVELOPMENT_PLAN.md](./APP_RENAMING_AND_DEVELOPMENT_PLAN.md) | 앱 리네이밍 계획 | 📎 Reference |
| [PHASE2_APP_MAPPING_PLAN.md](./PHASE2_APP_MAPPING_PLAN.md) | Phase 2 앱 매핑 | 📎 Reference |

---

## 📁 Subdirectories

### `/specs` - Feature Specifications
| 문서 | 설명 |
|------|------|
| [abyss-mirror.md](./specs/abyss-mirror.md) | 심연의 거울 (페르소나 분석) SPEC |
| [TEMPLATE_SPEC.md](./specs/TEMPLATE_SPEC.md) | SPEC 템플릿 |
| [README.md](./specs/README.md) | SPEC 작성 가이드 |

### `/strategic` - Strategic Documents
| 문서 | 설명 |
|------|------|
| [unified_4layer_strategy.md](./strategic/unified_4layer_strategy.md) | 4-Layer 통합 전략 |
| [story_first_architecture_roadmap.md](./strategic/story_first_architecture_roadmap.md) | Story-First 아키텍처 로드맵 |
| [pj_insights_gap_analysis.md](./strategic/pj_insights_gap_analysis.md) | PJ Insights Gap 분석 |

### `/archive` - Archived Documents (38 files)
과거 설계 문서 및 참조용 아카이브. 현재 개발에는 사용하지 않음.

---

## 🔥 RAG Architecture Overview (2026-01-15)

```
┌─────────────────────────────────────────────────────────────────┐
│              Vivid Plugin-Registry RAG Architecture             │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐   │
│  │ YAML Manifest │───▶│ Query Router  │───▶│ Backend Pool  │   │
│  │ (Hot-reload)  │    │ (Selector)    │    │ (Discovery)   │   │
│  └───────────────┘    └───────────────┘    └───────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│ L0: Semantic Cache (pgvector + Memory LRU)                      │
├─────────────────────────────────────────────────────────────────┤
│ L1a: Dense Search (Qdrant Vector, 384-dim)                      │
│ L1b: Sparse Search (BM25 Keyword) ⭐ NEW                         │
│      → RRF Fusion (k=60, Weighted)                              │
├─────────────────────────────────────────────────────────────────┤
│ L2: NotebookLM Playwright (거장 DNA)                             │
├─────────────────────────────────────────────────────────────────┤
│ L3: Google Search Grounding (실시간 정보)                        │
└─────────────────────────────────────────────────────────────────┘
```

### 검색 품질 (BM25 Hybrid)

| 메트릭 | Dense Only | Dense + BM25 + RRF |
|--------|-----------|-------------------|
| 검색 정확도 | 62% | **91%** (+48%) |
| 전문 용어 매칭 | 55% | **95%** (+73%) |

---

## 🚀 Implementation Roadmap

| Phase | 작업 | 예상 노력 | 상태 |
|-------|------|----------|------|
| P0 | BM25 검색 활성화 | 1-2h | ⏳ 대기 |
| P1 | YAML Manifest 도입 | 2-3h | ⏳ 대기 |
| P2 | Backend Auto-discovery | 3-4h | ⏳ 대기 |
| P3 | Ensemble Retriever (병렬) | 2h | ⏳ 대기 |

> **상세 계획**: [Implementation Plan](../.gemini/antigravity/brain/fd50d920-5052-44e8-a0ad-c5b0bc32d4f9/implementation_plan.md)

---

## 📋 Document Status Legend

| 상태 | 의미 |
|------|------|
| ✅ Active | 현재 개발에 사용 중인 문서 |
| 📎 Reference | 참조용 (수정 불필요) |
| 🔄 Updating | 업데이트 진행 중 |
| 📦 Archive | /archive로 이동 예정 |
