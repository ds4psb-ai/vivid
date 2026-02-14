# AD Studio Local Audit Map

이 문서는 Vivid 조감독(AD Studio)의 코드 전수조사 시점 기준 로컬 지형도다.

## 1. Entry / API Boundary

- `backend/app/routers/dimension/ad_studio.py`
- 핵심 포인트:
  - `POST /ad-studio/analyze`
  - `POST /ad-studio/analyze/stream`
  - `POST /ad-studio/analyze-video`
  - `GET /ad-studio/techniques`
  - 입력 제약: scenario min/max, style_hint max, target_engines enum
  - 기본 엔진: `kling`, `seedance`, `veo`
  - 시퀀스 응답에 `continuity_score` 노출 여부

## 2. Core Brain / Decomposition

- `backend/app/services/ad_brain.py`
- 핵심 포인트:
  - scenario 분석 파이프라인 (decomposition → validation/fix → sequence build)
  - evidence refs 조립 (`model:*`, `decomposition:*`, `pacing:*`)
  - video 분석은 scenario 분석 파이프를 재사용
  - `_calculate_continuity_score` 가중치/정규화 회귀 여부

## 3. Prompt Compilation

- `backend/app/services/ad_prompt_engine.py`
- `backend/app/services/adapters/*`
- 핵심 포인트:
  - 엔진별 프롬프트 계약 분리 유지
  - 엔진 추가 시 adapter 계층으로 확장

## 4. Frontend Contract

- `frontend/src/components/dimension/ADStudioPanel.tsx`
- `frontend/src/components/dimension/ad-studio/SequenceTimeline.tsx`
- 핵심 포인트:
  - 입력 탭: `scenario` / `video`
  - `MAX_SCENARIO_LENGTH` 클라이언트 검증
  - 크레딧 부족/할당량/재시도 흐름
  - 호출 엔드포인트:
    - `/api/dimension/ad-studio/analyze`
    - `/api/dimension/ad-studio/analyze-video`
  - 연속성 배지/밴드(녹색/황색/적색) 렌더링 규칙 유지

## 5. Test Anchors

- `backend/tests/routers/test_ad_studio.py`
- `frontend/src/components/dimension/ad-studio/SequenceTimeline.test.tsx`
- 최소 보장 영역:
  - 라우터 등록/엔드포인트 존재
  - request/response 스키마 검증
  - 입력 sanitization
  - RAG preset 연결
  - 연속성 점수 계산/표시 회귀 방지

## 6. Adjacent Modules (변경 영향 주의)

- `backend/app/routers/dimension/_base.py` (dimension 등록/credit mapping)
- `backend/app/rag/rag_presets.py` (`AD_STUDIO` preset)
- `backend/app/rag/cinematic_techniques.py` (기법 코퍼스 질의)
- `frontend/src/lib/dimension-data.ts` (dimension 메타/설명)

## 7. Quick Impact Checklist

1. 엔진 enum 변경 시:
- router validators
- frontend toggles/payload
- tests (invalid engine, defaults)

2. decomposition 출력 변경 시:
- ADStudioResponse schema
- SceneCard/SequenceTimeline 렌더링
- evidence_refs 및 export JSON 계약

3. 크레딧/실행 흐름 변경 시:
- backend capsule cost mapping
- frontend credit modal + retry policy
