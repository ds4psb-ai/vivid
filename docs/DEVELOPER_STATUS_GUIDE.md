# Vivid 프로젝트 개발 현황 및 작업 가이드

> **작성일**: 2026-01-07 (마지막 업데이트: 2026-01-15)
> **버전**: 1.1
> **대상**: 개발자 온보딩 및 현황 파악용

---

## 1. 프로젝트 개요

**Vivid**는 AI 기반 영상 제작 워크플로우 플랫폼입니다. 사용자가 아이디어를 입력하면 AI가 시나리오, 스토리보드, 프롬프트, 영상까지 순차적으로 생성하는 "차원(Dimension)" 기반 파이프라인을 제공합니다.

### 1.1 핵심 개념

| 용어 | 설명 |
|------|------|
| **Dimension (차원)** | 영상 제작의 각 단계를 담당하는 미니앱 (총 10개) |
| **Flow (열차)** | 여러 Dimension을 순차적으로 연결한 워크플로우 |
| **Capsule** | 각 Dimension의 실행 단위 (입력/출력 스키마 정의) |
| **초끼 (Chokki)** | AI 에이전트 이름 (채팅 방식으로 도구 실행) |
| **Singularity (특이점)** | 템플릿 갤러리 (미리 구성된 워크플로우) |

### 1.2 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Frontend** | Next.js 16.1, TypeScript, npm, TailwindCSS |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **Database** | PostgreSQL (Main), Redis (Cache), Qdrant (Vector) |
| **AI** | Google Gemini 3 Pro/Flash, Google Veo 3.1, Claude 4.5 |
| **Infra** | Docker (Colima), nohup 기반 로컬 개발 |

---

## 2. 디렉토리 구조

```
/Users/ted/vivid/
├── backend/
│   ├── app/
│   │   ├── routers/           # 53개 API 라우터
│   │   ├── services/          # 51개 비즈니스 로직
│   │   ├── agents/            # 초끼 에이전트 시스템
│   │   ├── adapters/          # 외부 서비스 어댑터
│   │   ├── fixtures/          # 캡슐 정의, 시드 데이터
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── models.py          # SQLAlchemy 모델
│   │   ├── dimension_adapter.py  # ⭐ 핵심: Dimension 실행 로직
│   │   ├── gemini_client.py   # Gemini API 클라이언트
│   │   └── main.py            # FastAPI 앱 엔트리
│   └── venv/                  # Python 가상환경
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js 라우트 (21개)
│   │   │   ├── dimension/     # 차원 앱 페이지들
│   │   │   ├── flow/          # 워크플로우(열차) 페이지
│   │   │   ├── singularity/   # 템플릿 갤러리
│   │   │   ├── crebit/        # 랜딩/대시보드
│   │   │   └── ...
│   │   ├── components/        # 78개 React 컴포넌트
│   │   │   ├── dimension/     # 차원 앱 패널들
│   │   │   ├── train/         # TrainWorkflowView 등
│   │   │   └── ...
│   │   └── lib/               # 유틸리티, API 클라이언트
│   └── package.json
├── docs/                      # 문서 (10개 핵심 + 35개 archive)
│   ├── PHASE2_APP_MAPPING_PLAN.md  # ⭐ Phase 2 상세 계획서
│   └── strategic/             # 전략 문서
├── data/                      # 미학 데이터셋, 패턴 정의
│   └── source_packs/bong/     # 봉준호 스타일 데이터 (4-layer)
└── docker-compose.yml         # PostgreSQL, Redis, Qdrant
```

---

## 3. 현재 구현 상태 (2026-01-07 기준)

### 3.1 완료된 기능 ✅

#### Backend

| 파일/모듈 | 설명 | 완성도 |
|-----------|------|--------|
| `dimension_adapter.py` | 13개 Dimension 캡슐 실행 로직 (16개 핸들러) | 95% |
| `routers/dimension/` | `/api/dimension/*` 엔드포인트 (디렉토리, 13개 모듈) | 95% |
| `routers/auth.py` | Google OAuth 인증 | 95% |
| `credit_service.py` | 크레딧 지갑/원장 시스템 | 90% |
| `services/vector_service.py` | Qdrant RAG 검색 | 80% |
| `gemini_client.py` | Gemini 3 Pro/Flash API | 95% |
| `agents/vivid_agent.py` | 초끼 에이전트 (3-라운드 디스패치) | 75% |

#### Frontend

| 파일/모듈 | 설명 | 완성도 |
|-----------|------|--------|
| `app/dimension/*/page.tsx` | 개별 차원 앱 페이지 (static routes) | 90% |
| `components/dimension/*.tsx` | 11개 차원 패널 컴포넌트 (Creative Editor 포함) | 85% |
| `components/train/TrainWorkflowView.tsx` | 열차 워크플로우 UI | 80% |
| `app/flow/page.tsx` | Flow 메인 페이지 | 80% |
| `app/singularity/page.tsx` | 템플릿 갤러리 | 70% |
| `components/AgentChatAccordion.tsx` | 초끼 채팅 UI | 75% |

### 3.2 10개 Dimension 앱 상태

| # | 앱 이름 | 라우트 | Backend | Frontend | 비고 |
|---|--------|--------|---------|----------|------|
| 1 | 심연해석기 | `/dimension/abyss` | ✅ 90% | ✅ 90% | 7단계 대화형 페르소나 분석 |
| 2 | 레퍼런스 해석기 | `/dimension/reference-decoder` | ✅ 90% | ✅ 90% | 동작 |
| 3 | 시나리오 생성기 | `/dimension/story-architect` | ✅ 85% | ✅ 85% | 동작 |
| 4 | 미학 디렉터 | `/dimension/aesthetic` | ✅ 85% | ✅ 85% | RAG 연동 완료 (6 auteurs) |
| 5 | 스토리보드 스케치 | `/dimension/storyboard` | ✅ 85% | ✅ 85% | 동작 |
| 6 | 사운드 크래프터 | `/dimension/sound-crafter` | ✅ 80% | ✅ 80% | 동작 |
| 7 | 프롬프트 연금술 | `/dimension/prompt` | ✅ 90% | ✅ 90% | 동작 |
| 8 | 비주얼 리얼라이저 | `/dimension/visual-realizer` | ✅ 85% | ✅ 85% | Midjourney 연동 |
| 9 | 비디오 메이커 | `/dimension/video-maker` | ✅ 90% | ✅ 85% | Veo 3.1 SSE 스트리밍 완료 |
| 10 | 퀄리티 디렉터 | `/dimension/quality-check` | ✅ 90% | ✅ 85% | Creative Editor 패널이 기본 페이지에 연결 |

### 3.3 미구현 / 진행 중 ❌🔄

| 기능 | 현재 상태 | 필요 작업 | 관련 파일 |
|------|----------|----------|-----------|
| **GA/RL 학습** | 프로토타입 | 보상 함수 → Pattern Lift 연동 | `_deprecated/` 참조 |
| **NotebookLM** | 스텁 | Enterprise API 실연동 | `notebooklm_client.py` |
| **Event-driven 워커** | 미구현 | Redis + Arq 배포 | - |
| **멀티랭귀지** | ko/en만 | i18n 확장 | - |

---

## 4. 우선순위별 TODO

### ✅ P0: 완료됨 (2026-01-08)

#### 4.1 Veo 3.1 비동기 폴링 안정화 ✅

- `services/veo_service.py` 구현 완료
- SSE 스트리밍 엔드포인트 추가 (`/veo/generate/stream`)
- 프론트엔드 `executeVeoGenerateStream()` 함수 추가
- 네트워크 에러 재시도, 한글 에러 메시지

#### 4.2 Quality Director 실동작 ✅

- `dimension_adapter.py`에 `run_quality_checker()` 구현 (L959-1098)
- 6가지 검수 기준 모두 동작: aesthetic, ad_suitability, consistency, safety, technical, narrative
- `/quality/check` 엔드포인트 완료

---

### ✅ P1: 완료됨 (2026-01-08)

#### 4.3 미학디렉터 RAG 연동 ✅

- `scripts/seed_aesthetic_rag.py` 스크립트 생성
- 6 auteurs Qdrant AD 컬렉션에 인덱싱 완료 (봉준호, 박찬욱, 신카이, 이창동, 나홍진, 홍상수)
- Tier1DimensionRAG Qdrant v1.16+ API 호환

#### 4.4 심연해석기 MVP ✅

- `run_persona_analyzer()` 구현 완료 (L1281-1435)
- 7단계: intro → saju → mbti → subconscious → unconscious → background → synthesis
- `AbyssInterpreterPanel.tsx` 21KB 대화 UI 완성
- Depth level 추적 (표층 → 심층 → 심연)

---

### 🟢 P2: 개선 사항 (진행 중)

| 작업 | 설명 | 난이도 |
|------|------|--------|
| Event-driven 워커 | Redis + Arq 배포, 장시간 작업 비동기화 | 높음 |
| NotebookLM 실연동 | Enterprise API 연결 | 중간 |
| GA/RL 학습 루프 | 템플릿 자동 승격 | 높음 |
| 멀티랭귀지 | i18n 확장 (현재 ko/en) | 낮음 |

---

## 5. 개발 환경 설정

### 5.1 서버 시작

```bash
# 워크플로우: /server 슬래시 커맨드 또는 아래 수동 실행

# 1. Docker 컨테이너
colima start
docker start crebit-postgres crebit-redis crebit-qdrant

# 2. Backend (포트 8100)
cd /Users/ted/vivid/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload

# 3. Frontend (포트 3100, npm 사용)
cd /Users/ted/vivid/frontend
npm run dev
```

### 5.2 로그 위치

- Backend: `/tmp/vivid-backend.log`
- Frontend: `/tmp/vivid-frontend.log`

### 5.3 테스트

```bash
# Backend 테스트
cd backend && pytest -v

# Frontend 테스트
cd frontend && npm run test:e2e
```

---

## 6. 핵심 파일 Quick Reference

### Backend

| 파일 | 역할 | 편집 빈도 |
|------|------|----------|
| `dimension_adapter.py` (65KB) | Dimension 캡슐 실행 로직 | 높음 |
| `gemini_client.py` (46KB) | Gemini API 호출 | 중간 |
| `models.py` (41KB) | DB 모델 정의 | 낮음 |
| `fixtures/dimension_capsules.py` | 캡슐 스키마 정의 | 높음 |
| `agents/vivid_agent.py` | 초끼 에이전트 | 중간 |

### Frontend

| 파일 | 역할 | 편집 빈도 |
|------|------|----------|
| `components/train/TrainWorkflowView.tsx` | 열차 UI | 높음 |
| `app/flow/page.tsx` | Flow 메인 페이지 | 중간 |
| `components/dimension/*.tsx` | 10개 차원 패널 | 높음 |
| `lib/dimension-theme.ts` | 테마/라벨 정의 | 낮음 |

### 문서

| 파일 | 역할 |
|------|------|
| `00_DOCS_INDEX.md` | 문서 맵 |
| `docs/PHASE2_APP_MAPPING_PLAN.md` | Phase 2 상세 계획 (976줄) |
| `30_UNIFIED_EXECUTION_ROADMAP.md` | 로드맵 |
| `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md` | 아키텍처 철학 |

---

## 7. Known Issues

| 이슈 | 영향 | 상태 |
|------|------|------|
| ~~Agent SSE 중복 스레드~~ | ~~이벤트 중복 가능~~ | ✅ 해결 (StreamController) |
| ~~Global Chokki Accordion 레거시 파서~~ | ~~`agent.*` 이벤트 불일치~~ | ✅ 해결 (AG-UI 표준 매퍼) |
| ~~`aiofiles` 의존성 누락~~ | ~~일부 환경 import 실패~~ | ✅ 이미 추가됨 (L22) |
| ~~Affiliate API 404~~ | ~~`_deprecated`에만 존재~~ | ✅ 이미 마운트됨 (main.py L215) |
| ~~Pending tool UI stuck~~ | ~~결과 없으면 영구 대기~~ | ✅ 해결 (30초 타임아웃) |
| ~~Ghost Button Hallucination~~ | ~~가짜 UI 버튼 언급~~ | ✅ 해결 (Prompt Routing Hint 강화) |
| ~~Intent Router Miss~~ | ~~영어/트렌드 키워드 인식 실패~~ | ✅ 해결 (키워드/Regex 확장) |
| ~~Dimension Event Missing~~ | ~~Teaching Tool 실행 시 무응답~~ | ✅ 해결 (Event Handler 매핑 추가) |

---

## 8. 연락처 및 참고

- **메인 문서**: `/Users/ted/vivid/00_DOCS_INDEX.md`
- **Phase 2 계획**: `/Users/ted/vivid/docs/PHASE2_APP_MAPPING_PLAN.md`
- **서버 워크플로우**: `/Users/ted/vivid/.agent/workflows/server.md`

---

*이 문서는 2026-01-15 기준으로 업데이트되었습니다. 4-Layer 아키텍처 반영, Abyss Mirror 완료.*
