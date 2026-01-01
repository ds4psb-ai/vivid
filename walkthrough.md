# Walkthrough Log

**Date**: 2025-12-30 (Updated)  
**Scope**: VDG 2-Pass Internalization, NotebookLM 3-Tier RAG Architecture  
**Type**: Reference log (non-SoR). See `00_DOCS_INDEX.md` for canonical docs.

---

## 2025-12-30 Summary

### Story-First UI Integration (NEW)
- **Premium UI Components**:
  - `HookVariantSelector.tsx` - 8종 훅 스타일 + A/B 테스트 모드, Glassmorphism 디자인
  - `CanvasNarrativePanel.tsx` - 3-Tab 서사 제어 (부조화/감정/훅), Motion Tab 애니메이션
  - `DNAComplianceViewer.tsx` - DNA 가이드라인 준수 리포트, 샷별 위반 상세
  - `MetricsDashboard.tsx` - 바이럴 성과 대시보드, A/B 테스트 결과, 인사이트

- **Type Consolidation**:
  - `frontend/src/types/storyFirst.ts` - Story-First SSoT 타입 정의
  - `HookVariant`, `HookStyle`, `NarrativeArc`, `Sequence` 타입 통합
  - `BatchComplianceReport`, `ShotComplianceReport`, `RuleResult` 타입 통합

- **Canvas Layout Fix**:
  - `canvas/page.tsx` - 우상단 패널 겹침 문제 해결 (`mt-40`, `w-96`)
  - `pointer-events` 정밀 조정으로 상호작용 개선

- **Backend Integration**:
  - `capsules.py` - CapsuleRunRequest에 Story-First 필드 추가
  - `director_pack`, `scene_overrides`, `narrative_arc`, `hook_variant` 전달 로직

- **Documentation**:
  - `13_UI_DESIGN_GUIDE_2025-12.md` - Section 6.7/6.8 추가 (Story-First + Glassmorphism)
  - `00_DOCS_INDEX.md` - Frontend Components 섹션 추가
  - `README.md` - Story-First Features 섹션 추가

### VDG 2-Pass Pipeline Internalization
- **New Schemas** (`backend/app/schemas/`):
  - `vdg_v4.py` - VDG v4.0 core types (SemanticPassResult, VisualPassResult, VDGv4)
  - `director_pack.py` - DirectorPack coaching types (DNAInvariant, MutationSlot)
  - `metric_registry.py` - 25+ metric definitions (SSoT)
  
- **New Services** (`backend/app/services/vdg_2pass/`):
  - `semantic_pass.py` - Pass 1: Meaning/structure analysis
  - `visual_pass.py` - Pass 2: Visual metrics extraction
  - `analysis_planner.py` - Bridge: Pass 1 → Pass 2
  - `merger.py` - Quality gate & pass merge
  - `director_compiler.py` - VDG → DirectorPack compiler
  - `frame_extractor.py` - ffmpeg frame extraction
  - `gemini_utils.py` - API retry/repair utilities

- **Cleanup**: Removed `different project_vdg_2pass/` temp folder

### NotebookLM 3-Tier RAG Architecture
- **Tier 2**: `DNA_봉준호` notebook created & verified
- **Tier 3**: `FILM_기생충` notebook with 7 scene-analysis sources
- **API Key**: Confirmed `arkain.info@gmail.com` Gemini Enterprise

### Files Created
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/vdg_v4.py`
- `backend/app/schemas/director_pack.py`
- `backend/app/schemas/metric_registry.py`
- `backend/app/services/__init__.py`
- `backend/app/services/vdg_2pass/` (9 files)
- `data/notebooklm_sources_v2/film_parasite/` (7 JSON sources)

---

## 2025-12-29 Summary

### NotebookLM Loading Infrastructure (Phase 0-2)
- **Analytics Events**: `AnalyticsEvent` model + `/api/v1/analytics/*` endpoints
- **Distance Calculation**: `cluster_distance.py` (D = 0.55*DL + 0.35*DP + 0.10*DC)
- **Evidence Gate**: `evidence_gate.py` (≥95% claims with 2+ refs)
- **Pilot Metrics**: `/api/v1/ops/pilot-metrics` Go/No-Go dashboard

### Crebit Page
- Korean localization for Crebit landing page
- Updated 기획・제작 footer with (주)아캐인 business registration info

---

## 2025-12-28 Summary

### Google OAuth & Route Protection
- Added Google OAuth session flow (`backend/app/routers/auth.py`)
- Created Next.js middleware for protected routes (`frontend/src/middleware.ts`)
- UI polish: Glassmorphism sidebar buttons, canvas spacing, run log visibility

---

## API Endpoints Added

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analytics/events` | POST | Track user events |
| `/api/v1/analytics/metrics` | GET | Aggregated metrics |
| `/api/v1/ops/pilot-metrics` | GET | Go/No-Go dashboard (admin) |

---

## Verification

```bash
# VDG 2-Pass import check
cd backend && python3 -c "from app.services.vdg_2pass import SemanticPass, VisualPass, VDGMerger, DirectorCompiler; print('✅ OK')"

# Schema import check
cd backend && python3 -c "from app.schemas.vdg_v4 import VDGv4; from app.schemas.director_pack import DirectorPack; print('✅ OK')"
```

---

## Next Steps

1. ~~VDG 2-Pass internalization~~ ✅
2. ~~NotebookLM Tier 2/3 notebooks~~ ✅
3. Implement Tier 1 (META-INVARIANTS) notebooks
4. Audio Coach API integration with DirectorPack
5. Cross-tier query testing

