# Pre-Development Checklist (2026 Best Practices)

> **버전**: 1.2
> **최종 검증일**: 2026-01-16
> **대상**: Dimension 앱 개발자, RAG 데이터 큐레이터
> **목적**: 본격적인 개발 시작 전 필수 준비사항 체크리스트

---

## Executive Summary

이 문서는 **앱 개발자**와 **데이터 큐레이터**가 본격적인 개발/운영에 들어가기 전에 반드시 완료해야 할 사전 준비 단계를 정의합니다.

| 대상 | 예상 소요 시간 | 목표 |
|------|---------------|------|
| **앱 개발자** | 1-2일 | 첫 커밋까지 시간 최소화 |
| **데이터 큐레이터** | 2-3일 | 고품질 RAG 데이터 파이프라인 구축 |

---

## Part A: 앱 개발자 Pre-Development Checklist

### Phase 1: 환경 설정 (Day 0)

#### 1.1 시스템 요구사항 확인

| 항목 | 최소 요구사항 | 권장 |
|------|-------------|------|
| **Node.js/Bun** | Node 20.x 또는 Bun 1.x | Bun 1.3+ (권장) |
| **Python** | 3.11 | 3.12+ |
| **Docker** | 24.x | 25.x+ |
| **Git** | 2.40+ | 최신 |
| **RAM** | 8GB | 16GB+ |
| **Disk** | 20GB 여유 | SSD 50GB+ |

```bash
# 버전 확인 명령어 (Bun 환경)
bun --version && python3 --version && docker --version && git --version

# Node.js 환경인 경우
node -v && python3 --version && docker --version && git --version
```

- [ ] Node.js 20+ 설치 확인
- [ ] Python 3.11+ 설치 확인
- [ ] Docker Desktop 설치 및 실행 확인
- [ ] Git 설치 및 SSH 키 설정

#### 1.2 저장소 클론 및 의존성 설치

```bash
# 1. 저장소 클론
git clone git@github.com:ds4psb-ai/vivid.git
cd vivid

# 2. Frontend 의존성
cd frontend && npm install

# 3. Backend 의존성
cd ../backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

- [ ] 저장소 클론 완료
- [ ] Frontend 의존성 설치 (`npm install`)
- [ ] Backend 가상환경 생성 및 활성화
- [ ] Backend 의존성 설치 (`pip install -r requirements.txt`)

#### 1.3 로컬 서비스 구동

```bash
# Docker 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

| 서비스 | 포트 | 확인 URL |
|--------|------|----------|
| PostgreSQL | 5433 | `psql -h localhost -p 5433 -U vivid` |
| Redis | 6380 | `redis-cli -p 6380 ping` |
| Qdrant | 6333 | http://localhost:6333/dashboard |

- [ ] Docker Compose 서비스 기동 (`docker-compose up -d`)
- [ ] PostgreSQL 연결 확인
- [ ] Redis 연결 확인
- [ ] Qdrant 대시보드 접근 확인

#### 1.4 환경 변수 설정

```bash
# Backend
cp backend/.env.example backend/.env
# 필수 값 설정: DATABASE_URL, REDIS_URL, GEMINI_API_KEY

# Frontend
cp frontend/.env.example frontend/.env.local
# 필수 값 설정: NEXT_PUBLIC_API_URL
```

- [ ] Backend `.env` 파일 생성 및 설정
- [ ] Frontend `.env.local` 파일 생성 및 설정
- [ ] API 키 (Gemini, etc.) 발급 및 설정

---

### Phase 2: 빌드 및 테스트 검증 (Day 0-1)

#### 2.1 빌드 검증

```bash
# Backend 테스트
cd backend && source venv/bin/activate
pytest --tb=short -q

# Frontend 빌드
cd ../frontend && npm run build
```

- [ ] Backend pytest 전체 통과
- [ ] Frontend build 성공
- [ ] ESLint/TypeScript 에러 없음

#### 2.2 개발 서버 구동 확인

```bash
# Backend (터미널 1)
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8100

# Frontend (터미널 2)
cd frontend && npm run dev
```

| 서비스 | URL | 확인 사항 |
|--------|-----|----------|
| Backend API | http://localhost:8100/docs | Swagger UI 로드 |
| Frontend | http://localhost:3100 | 홈 페이지 렌더링 |

- [ ] Backend API 서버 정상 구동 (http://localhost:8100/docs)
- [ ] Frontend 개발 서버 정상 구동 (http://localhost:3100)
- [ ] API 연동 확인 (Network 탭에서 8100 요청 확인)

---

### Phase 3: 필수 문서 숙지 (Day 1)

#### 3.1 핵심 문서 읽기 (필수)

| 우선순위 | 문서 | 경로 | 예상 시간 |
|---------|------|------|----------|
| **P0** | 루트 CLAUDE.md | `/CLAUDE.md` | 15분 |
| **P0** | 앱 개발자 가이드 | `/docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | 45분 |
| **P1** | Frontend CLAUDE.md | `/frontend/CLAUDE.md` | 10분 |
| **P1** | Backend CLAUDE.md | `/backend/CLAUDE.md` | 10분 |
| **P2** | UQSL 스펙 | `/docs/UQSL_IMPLEMENTATION_SPEC.md` | 30분 |

- [ ] CLAUDE.md (루트) 읽기 완료
- [ ] DIMENSION_APP_DEVELOPER_GUIDE.md 읽기 완료
- [ ] 담당 영역 CLAUDE.md (frontend/backend) 읽기 완료

#### 3.2 아키텍처 이해

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 16)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Dimension   │  │ Agent Chat  │  │ Singularity         │ │
│  │ Panels      │  │ (SSE)       │  │ (Templates)         │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼───────────────────┼─────────────┘
          │                │                   │
          ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Dimension   │  │ Workflow    │  │ RAG                 │ │
│  │ Routers     │  │ Agent       │  │ (Tier0 + Tier1)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

- [ ] 4-Layer 생태계 아키텍처 이해
- [ ] Dimension 앱 구조 이해 (YAML SSoT → Router → Panel)
- [ ] RAG 2-Tier 구조 이해 (NotebookLM + Qdrant)

#### 3.3 코딩 컨벤션 확인

**Frontend (TypeScript/React)**
- [ ] React 19 훅 패턴 이해 (`useTransition`, `useOptimistic`)
- [ ] DimensionPanel Compound Component 구조 이해
- [ ] ESLint 규칙 확인 (`eslint.config.mjs`)

**Backend (Python/FastAPI)**
- [ ] 타입 힌트 필수 사용
- [ ] async/await 패턴 이해
- [ ] Pydantic v2 모델 사용법

---

### Phase 4: 담당 앱 분석 (Day 1-2)

#### 4.1 기존 앱 코드 분석

담당 Dimension 앱의 기존 코드를 분석합니다:

```bash
# 앱 관련 파일 확인
ls -la config/apps/content/dimensions/{your_app}.yaml
ls -la backend/app/routers/dimension/{your_app}.py
ls -la frontend/src/components/dimension/{YourApp}Panel.tsx
```

- [ ] YAML 설정 파일 분석 (capabilities, credit_cost, RAG 설정)
- [ ] Backend 라우터 코드 분석
- [ ] Frontend 패널 코드 분석
- [ ] 기존 테스트 코드 확인

#### 4.2 유사 앱 참조

| 앱 유형 | 참조 앱 | 특징 |
|---------|--------|------|
| 생성형 | PromptGeneratorPanel | 기본 생성 패턴 |
| 분석형 | AestheticDirectorPanel | UQSL 통합, RAG 연동 |
| 멀티모달 | VeoVideoPanel | 파일 업로드, 대용량 처리 |

- [ ] 유사 앱 코드 분석 완료
- [ ] 공통 패턴 파악

---

### Phase 5: 개발 준비 완료 확인

#### 5.1 최종 체크리스트

```bash
# 전체 상태 확인 스크립트
cd /path/to/vivid

# 1. Docker 서비스
docker-compose ps | grep -E "Up|running"

# 2. Backend 테스트
cd backend && source venv/bin/activate && pytest -q --tb=no

# 3. Frontend 빌드
cd ../frontend && npm run build

# 4. 타입 체크
npm run lint
```

- [ ] 모든 Docker 서비스 정상 가동
- [ ] Backend 테스트 100% 통과
- [ ] Frontend 빌드 성공
- [ ] Lint 에러 없음
- [ ] 개발 서버에서 담당 앱 페이지 접근 가능

---

## Part B: RAG 데이터 큐레이터 Pre-Development Checklist

### Phase 1: 환경 및 도구 준비 (Day 0)

#### 1.1 필수 도구 설치

| 도구 | 용도 | 설치 확인 |
|------|------|----------|
| **Chrome** | NotebookLM 접근 | 최신 버전 |
| **Python 3.11+** | 스크립트 실행 | `python3 --version` |
| **Qdrant CLI** | 벡터 DB 관리 | `pip install qdrant-client` |

- [ ] Chrome 브라우저 설치 (NotebookLM용)
- [ ] Python 3.11+ 설치
- [ ] qdrant-client 패키지 설치

#### 1.2 NotebookLM 접근 설정

```bash
# Chrome CDP 모드 시작 (인증 유지용)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir=/tmp/chrome-debug-9223
```

- [ ] Google 계정 로그인
- [ ] NotebookLM (notebooklm.google.com) 접근 확인
- [ ] 기존 노트북 목록 확인

#### 1.3 Qdrant 연결 확인

```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collections = client.get_collections()
print(f"Collections: {[c.name for c in collections.collections]}")
```

- [ ] Qdrant 대시보드 접근 (http://localhost:6333/dashboard)
- [ ] 기존 컬렉션 목록 확인
- [ ] Python 클라이언트 연결 테스트

---

### Phase 2: 데이터 품질 기준 숙지 (Day 0-1)

#### 2.1 RAG 데이터 큐레이터 가이드 읽기

- [ ] `/docs/RAG_DATA_CURATOR_GUIDE.md` 전체 읽기 (45분)
- [ ] 소스 품질 등급 (A/B/C/D) 이해
- [ ] Semantic Chunking 전략 이해
- [ ] 메타데이터 태깅 규칙 이해

#### 2.2 데이터 품질 8-Step 체크리스트 (2026 Industry Standard)

| Step | 항목 | 설명 |
|------|------|------|
| 1 | **정확성 검증** | 출처가 신뢰할 수 있는가? |
| 2 | **완전성 확인** | 필수 정보가 누락되지 않았는가? |
| 3 | **형식 표준화** | 일관된 형식으로 변환되었는가? |
| 4 | **중복 제거** | 동일/유사 문서가 제거되었는가? |
| 5 | **적시성 확인** | 최신 정보인가? 언제 업데이트되었는가? |
| 6 | **관련성 검증** | 해당 Dimension에 적합한 데이터인가? |
| 7 | **보안 조치** | PII, 민감정보가 제거/마스킹되었는가? |
| 8 | **거버넌스 준수** | 저작권, 라이선스 문제는 없는가? |

- [ ] 8-Step 데이터 품질 체크리스트 이해

---

### Phase 3: 기존 RAG 시스템 분석 (Day 1)

#### 3.1 현재 컬렉션 현황 파악

```python
# 컬렉션별 문서 수 확인
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

for collection in client.get_collections().collections:
    info = client.get_collection(collection.name)
    print(f"{collection.name}: {info.points_count} documents")
```

- [ ] 기존 Qdrant 컬렉션 목록 확인
- [ ] 컬렉션별 문서 수 파악
- [ ] 메타데이터 스키마 파악

#### 3.2 NotebookLM 노트북 현황 파악

```bash
# MCP를 통한 노트북 목록 확인
# Claude Code에서 실행
mcp__notebooklm-mcp__notebook_list()
```

- [ ] 기존 NotebookLM 노트북 목록 확인
- [ ] 노트북별 소스 수 파악
- [ ] 노트북 구조 (거장별/도메인별) 파악

#### 3.3 RAG 품질 베이스라인 측정

```bash
# RAG 품질 리포트 실행
cd backend
python scripts/run_rag_quality_report.py --dimension AD --auteur bong
```

| 메트릭 | 현재 값 | 목표 |
|--------|--------|------|
| Recall@10 | ? | > 80% |
| Precision@10 | ? | > 70% |
| NDCG | ? | > 0.75 |

- [ ] 현재 RAG 품질 메트릭 측정
- [ ] 베이스라인 값 기록

---

### Phase 4: 데이터 소스 평가 및 수집 계획 (Day 1-2)

#### 4.1 담당 Dimension 데이터 요구사항 파악

| Dimension | 필요 데이터 유형 | 우선순위 소스 |
|-----------|-----------------|--------------|
| AD | 영화 분석, 미학 이론 | 학술 논문, 감독 인터뷰 |
| 4D | 영상 분석 레퍼런스 | 영화 씬 분석, 기법 설명 |
| Story | 시나리오 작법 | 시나리오 교본, 작가 인터뷰 |
| 3D | 비주얼 스타일 | 촬영 기법, 색보정 가이드 |

- [ ] 담당 Dimension의 데이터 요구사항 파악
- [ ] 수집할 소스 유형 결정
- [ ] 우선순위 소스 목록 작성

#### 4.2 소스 품질 평가 기준

**A등급 (최우선)** - 반드시 포함
- 공식 인터뷰, 학술 논문, 공인 출처
- 원저작자의 직접 발언/문서

**B등급 (권장)** - 검토 후 포함
- 유명 평론가/전문가 분석
- 공인된 미디어 콘텐츠

**C등급 (제한적)** - 신중하게 검토
- 팬 분석, 블로그 콘텐츠
- 검증 필요한 2차 자료

**D등급 (제외)** - 포함 금지
- 익명 게시물, 출처 불명
- 저작권 문제 있는 자료

- [ ] 소스 품질 평가 기준 이해
- [ ] 수집 예정 소스의 등급 분류

---

### Phase 5: 인제스션 파이프라인 테스트 (Day 2)

#### 5.1 테스트 문서로 파이프라인 검증

```python
# 테스트 인제스션 실행
from app.rag.ingestion import RagIngestionService

ingestion = RagIngestionService()

# 1. 소규모 테스트 (1-2개 문서)
await ingestion.ingest_document(
    file_path="test_data/sample_analysis.pdf",
    collection="test_collection",
    dimension="AD",
    metadata={"source": "test", "quality_grade": "B"},
)

# 2. 청킹 결과 확인
# 3. 임베딩 품질 확인
# 4. 검색 테스트
```

- [ ] 테스트 문서 준비 (1-2개)
- [ ] 인제스션 파이프라인 실행
- [ ] 청킹 결과 검증 (청크 크기, 개수)
- [ ] 검색 테스트 실행

#### 5.2 메타데이터 스키마 확정

```python
# 표준 메타데이터 스키마
METADATA_SCHEMA = {
    # 필수
    "dimension": str,       # "AD", "4D", "Story", etc.
    "source_type": str,     # "interview", "paper", "analysis"
    "language": str,        # "ko", "en"

    # 권장
    "auteur_key": str,      # "bong", "nolan", etc. (선택)
    "year": int,            # 작성 연도
    "quality_grade": str,   # "A", "B", "C"

    # 추적용
    "source_url": str,
    "source_title": str,
    "ingested_at": str,     # ISO 8601
    "ingested_by": str,     # 담당자 ID
}
```

- [ ] 메타데이터 스키마 확정
- [ ] 담당 Dimension 특수 필드 정의 (필요시)

---

### Phase 6: 운영 준비 완료 확인

#### 6.1 최종 체크리스트

- [ ] NotebookLM 접근 및 인증 정상
- [ ] Qdrant 연결 및 권한 확인
- [ ] 인제스션 파이프라인 테스트 통과
- [ ] 메타데이터 스키마 문서화 완료
- [ ] 현재 RAG 품질 베이스라인 기록
- [ ] 수집할 소스 목록 및 우선순위 정의
- [ ] RAG_DATA_CURATOR_GUIDE.md 숙지 완료

---

## Part C: UX/UI/디자인 체크리스트 (2026 Best Practices)

### Phase 1: 디자인 시스템 기반 (필수)

#### 1.1 Tailwind CSS + Design Tokens

```javascript
// tailwind.config.js - Design Token 체계
module.exports = {
  theme: {
    extend: {
      colors: {
        // Semantic Colors (Vivid 브랜드)
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        surface: 'var(--color-surface)',
        error: 'var(--color-error)',
      },
      spacing: {
        // 8pt Grid System
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
      },
    },
  },
}
```

- [ ] Design Token 시스템 확인 (`tailwind.config.ts`)
- [ ] 시맨틱 컬러 변수 사용 (하드코딩 금지)
- [ ] 8pt Grid 시스템 준수
- [ ] 다크모드 지원 확인 (`dark:` 클래스)

#### 1.2 컴포넌트 라이브러리

| 라이브러리 | 용도 | 경로 |
|-----------|------|------|
| **DimensionPanel** | Dimension 앱 UI | `frontend/src/components/dimension/` |
| **shadcn/ui** | 기본 UI 컴포넌트 | `frontend/src/components/ui/` |
| **Headless UI** | 접근성 컴포넌트 | (Tailwind 제공) |

- [ ] DimensionPanel Compound Component 구조 이해
- [ ] shadcn/ui 컴포넌트 사용법 확인
- [ ] 재사용 가능한 컴포넌트 우선 사용

---

### Phase 2: 접근성 (WCAG 2.2 AA 준수)

#### 2.1 WCAG 2.2 필수 체크리스트

| 항목 | 기준 | 확인 방법 |
|------|------|----------|
| **색상 대비** | 4.5:1 (일반 텍스트), 3:1 (대형 텍스트) | Chrome DevTools Lighthouse |
| **키보드 탐색** | Tab 순서 논리적, Focus visible | Tab 키 테스트 |
| **포커스 표시** | 2.4.11 Focus Not Obscured | Focus가 다른 요소에 가려지지 않음 |
| **터치 타겟** | 2.5.8 최소 24x24px (권장 44x44px) | 버튼/링크 크기 확인 |
| **대체 텍스트** | 모든 이미지에 alt 속성 | `<img alt="">` 확인 |
| **폼 라벨** | 모든 입력 필드에 label 연결 | `htmlFor` 속성 확인 |

```tsx
// 2026 접근성 Best Practice 예시
<Button
  className="min-h-[44px] min-w-[44px] focus:ring-2 focus:ring-primary focus:outline-none"
  aria-label="생성 시작"
>
  생성하기
</Button>
```

- [ ] Lighthouse Accessibility 점수 90+ 확인
- [ ] 키보드만으로 전체 기능 사용 가능
- [ ] 스크린 리더 기본 테스트 (VoiceOver/NVDA)
- [ ] 색상만으로 정보 전달하지 않음

#### 2.2 WCAG 2.2 신규 기준 (2024 추가)

| 기준 | 설명 | 구현 |
|------|------|------|
| **3.2.6 Consistent Help** | 도움말 위치 일관성 | 헤더/푸터에 Help 링크 고정 |
| **3.3.7 Redundant Entry** | 중복 입력 방지 | 자동 완성, 이전 값 유지 |
| **3.3.8 Accessible Auth** | 인지 테스트 없는 인증 | 비밀번호만 요구하지 않음 |

- [ ] Help/FAQ 링크 일관된 위치에 배치
- [ ] 폼에서 이전 입력값 자동 완성 지원
- [ ] 인증 시 CAPTCHA 대안 제공

---

### Phase 3: 성능 (Core Web Vitals)

#### 3.1 Core Web Vitals 목표 (2026)

| 메트릭 | 기준 (Good) | 현재 | 목표 |
|--------|------------|------|------|
| **LCP** (Largest Contentful Paint) | < 2.5s | ? | < 2.0s |
| **INP** (Interaction to Next Paint) | < 200ms | ? | < 150ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | ? | < 0.05 |

```bash
# Core Web Vitals 측정
npx lighthouse http://localhost:3100 --only-categories=performance --view

# 또는 크롬에서: F12 → Lighthouse → Performance
```

- [ ] LCP < 2.5초 달성
- [ ] INP < 200ms 달성
- [ ] CLS < 0.1 달성

#### 3.2 성능 최적화 체크리스트

**LCP 최적화**
- [ ] 히어로 이미지 `priority` 또는 `fetchpriority="high"` 적용
- [ ] 이미지 WebP/AVIF 포맷 사용
- [ ] Critical CSS 인라인화 (Next.js 자동)
- [ ] `<link rel="preload">` 중요 리소스에 적용

**INP 최적화**
- [ ] 긴 JavaScript 태스크 분할 (50ms 이하)
- [ ] `useTransition` 사용하여 UI 블로킹 방지
- [ ] 서드파티 스크립트 지연 로딩

**CLS 최적화**
- [ ] 이미지/비디오에 `width`/`height` 또는 `aspect-ratio` 명시
- [ ] 폰트 로딩 시 `font-display: swap` 사용
- [ ] 동적 콘텐츠에 Skeleton UI 적용

---

### Phase 4: 로딩/에러 상태 (React 19)

#### 4.1 로딩 상태 패턴

```tsx
// 2026 Best Practice: Suspense + Skeleton
import { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

function DimensionApp() {
  return (
    <Suspense fallback={<DimensionSkeleton />}>
      <DimensionContent />
    </Suspense>
  );
}

// Skeleton 컴포넌트 예시
function DimensionSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-10 w-1/3" />
    </div>
  );
}
```

- [ ] 모든 비동기 영역에 Suspense 경계 설정
- [ ] Skeleton UI로 레이아웃 유지 (CLS 방지)
- [ ] 로딩 시간 3초 초과 시 진행 표시 추가

#### 4.2 에러 경계 패턴

```tsx
// 2026 Best Practice: Error Boundary + Fallback UI
import { ErrorBoundary } from 'react-error-boundary';

function DimensionApp() {
  return (
    <ErrorBoundary
      fallback={<ErrorFallback />}
      onError={(error, info) => logError(error, info)}
    >
      <DimensionContent />
    </ErrorBoundary>
  );
}

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="p-4 border border-error rounded-lg">
      <h2>문제가 발생했습니다</h2>
      <p className="text-sm text-muted">{error.message}</p>
      <Button onClick={resetErrorBoundary}>다시 시도</Button>
    </div>
  );
}
```

- [ ] 각 독립 기능 영역에 Error Boundary 적용
- [ ] 에러 발생 시 복구 버튼 제공
- [ ] 에러 로깅 (텔레메트리) 연동

---

### Phase 5: 반응형 디자인

#### 5.1 브레이크포인트

| 브레이크포인트 | 크기 | 주요 변경 |
|---------------|------|----------|
| **sm** | ≥640px | 2-column 그리드 |
| **md** | ≥768px | 사이드바 표시 |
| **lg** | ≥1024px | 3-column 그리드 |
| **xl** | ≥1280px | 전체 레이아웃 |

```tsx
// 반응형 그리드 예시
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id} />)}
</div>
```

- [ ] 모바일 우선 접근 (base → sm → md → lg → xl)
- [ ] 터치 타겟 44px 이상 (모바일)
- [ ] 가로 스크롤 없음 확인

#### 5.2 모바일 특수 고려사항

- [ ] 햄버거 메뉴 키보드 접근 가능
- [ ] 입력 시 가상 키보드로 인한 레이아웃 shift 방지
- [ ] 긴 텍스트 터치 스크롤 가능

---

### Phase 6: UI 일관성 검증

#### 6.1 Visual QA 체크리스트

| 항목 | 확인 사항 |
|------|----------|
| **타이포그래피** | 폰트 크기, 줄 높이 일관성 |
| **스페이싱** | 마진/패딩 8pt 그리드 준수 |
| **컬러** | 시맨틱 컬러 일관 사용 |
| **아이콘** | 크기, 스타일 통일 (lucide-react) |
| **버튼** | Primary/Secondary 스타일 구분 |
| **폼** | Label, Placeholder, Error 스타일 |

- [ ] Storybook 또는 직접 컴포넌트 시각 검사
- [ ] 다크모드 전환 시 깨짐 없음
- [ ] 다국어(한/영) 전환 시 레이아웃 유지

#### 6.2 크로스 브라우저 테스트

| 브라우저 | 최소 지원 버전 |
|---------|--------------|
| Chrome | 120+ |
| Firefox | 120+ |
| Safari | 17+ |
| Edge | 120+ |

- [ ] Chrome 최신 테스트
- [ ] Safari 테스트 (특히 iOS)
- [ ] Firefox 기본 테스트

---

### Quick Reference: UX/UI 체크 명령어

```bash
# 1. Lighthouse 접근성/성능 측정
npx lighthouse http://localhost:3100 --view

# 2. Bundle 분석
cd frontend && npm run build && npx @next/bundle-analyzer

# 3. TypeScript 타입 체크
npm run typecheck

# 4. 접근성 자동 검사 (axe-core)
npx @axe-core/cli http://localhost:3100
```

---

## Part D: 공통 보안 및 컴플라이언스 체크리스트

### 보안 필수 사항

- [ ] `.env` 파일 `.gitignore`에 포함 확인
- [ ] API 키, 시크릿 코드에 하드코딩 금지
- [ ] PII (개인정보) 포함 데이터 마스킹
- [ ] 저작권 있는 콘텐츠 직접 포함 금지

### 컴플라이언스

- [ ] 데이터 출처 명시 및 라이선스 확인
- [ ] GDPR/개인정보보호법 준수 확인 (필요시)
- [ ] 내부 데이터 거버넌스 정책 확인

---

## Quick Reference: 첫날 필수 완료 항목

### 앱 개발자 Day 1 Must-Do

```bash
# 1. 환경 설정
git clone ... && cd vivid
docker-compose up -d
cd frontend && npm install
cd ../backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# 2. 빌드 검증
cd backend && pytest -q
cd ../frontend && npm run build

# 3. 개발 서버 확인
# Terminal 1: uvicorn app.main:app --reload --port 8100
# Terminal 2: npm run dev
# Browser: http://localhost:3100, http://localhost:8100/docs

# 4. 문서 읽기
# - CLAUDE.md
# - docs/DIMENSION_APP_DEVELOPER_GUIDE.md
```

### 데이터 큐레이터 Day 1 Must-Do

```bash
# 1. 환경 설정
# Chrome CDP 모드, NotebookLM 로그인

# 2. 기존 시스템 파악
# Qdrant: http://localhost:6333/dashboard
# NotebookLM: 노트북 목록 확인

# 3. 문서 읽기
# - docs/RAG_DATA_CURATOR_GUIDE.md
# - 담당 Dimension YAML 설정

# 4. 품질 베이스라인 측정
cd backend && python scripts/run_rag_quality_report.py --dimension {YOUR_DIM}
```

---

## Appendix A: 2026-01-16 실제 검증 결과

> 시니어 디렉터가 체크리스트를 실행하며 발견한 사항

### 환경 설정

| 항목 | 검증 결과 | 비고 |
|------|----------|------|
| **Runtime** | Bun 1.3.5 | Node.js 대신 Bun 사용 |
| **Python** | 3.11.14 (venv) | ✅ 요구사항 충족 |
| **Docker** | 29.1.3 | ✅ 요구사항 충족 |
| **Git** | 2.50.1 | ✅ 요구사항 충족 |

### 프레임워크 버전

| 항목 | 버전 | 상태 |
|------|------|------|
| Next.js | 16.1.0 | ✅ 최신 |
| React | 19.2.3 | ✅ 최신 |
| FastAPI | 0.127.0 | ✅ |
| SQLAlchemy | 2.0.45 | ✅ |
| Pydantic | 2.12.5 | ✅ |

### Docker 서비스

| 서비스 | 포트 | 상태 |
|--------|------|------|
| PostgreSQL (pgvector:pg16) | 5433 | ⚠️ 수동 시작 필요: `docker compose up -d postgres` |
| Redis | 6380 | ✅ 실행중 |
| Qdrant | 6333 | ✅ 실행중 |
| Prometheus | 9090 | ✅ 실행중 |

### 빌드/테스트

| 항목 | 결과 | 비고 |
|------|------|------|
| **Frontend build** | ✅ 성공 | |
| **Backend pytest** | 1079 통과 (98%) | 23 실패, 13 에러 (통합 테스트) |
| **Pydantic v2** | ⚠️ 마이그레이션 수행됨 | `class Config` → `model_config = ConfigDict()` |

### Qdrant 컬렉션 현황

| Dimension | 문서 수 | 상태 |
|-----------|--------|------|
| 1D | 53 | ✅ |
| 2D | 52 | ✅ |
| 3D | 9 | ✅ 적재 완료 |
| 4D | 10 | ✅ 적재 완료 |
| 5D | 11 | ✅ 적재 완료 |
| 6D | 5 | ✅ 적재 완료 |
| AD | 60 | ✅ |
| AI | 8 | ✅ 적재 완료 |
| QC | 52 | ✅ |
| VEO | 52 | ✅ |

**완료**: `backend/scripts/seed_all_dimension_rag.py` 실행으로 3D/4D/5D/6D/AI 컬렉션 적재 완료 (2026-01-16)

### 인제스션 스크립트 (8개)

```bash
backend/scripts/
├── ingest_source_packs.py      # 소스팩 인제스션
├── ingest_video_reference.py   # 비디오 레퍼런스
├── ingest_image_grid.py        # 이미지 그리드
├── ingest_notebook_artifact.py # 노트북 아티팩트
├── ingest_notebook_library.py  # 노트북 라이브러리
├── ingest_raw_assets.py        # Raw 에셋
├── ingest_pattern_candidates.py # 패턴 후보
└── ingest_derived_insights.py  # 파생 인사이트
```

### NotebookLM MCP

- **상태**: ❌ 인증 만료
- **해결**: `notebooklm-mcp-auth` 실행 필요

### 보안 체크

| 항목 | 상태 |
|------|------|
| `.env` in .gitignore | ✅ |
| 시크릿 git 추적 없음 | ✅ |
| 하드코딩 API 키 없음 | ✅ |
| 보안 문서 존재 | ✅ (9개) |

---

## Appendix B: 수정된 파일 목록

### Phase 2에서 수정된 파일 (Pydantic v2 마이그레이션)

| 파일 | 변경 내용 |
|------|----------|
| `backend/pytest.ini` | 신규 생성 - scripts/ 제외 |
| `backend/tests/conftest.py` | 신규 생성 - PYTHONPATH 설정 |
| `app/routers/batch.py` | `min_items` → `min_length` |
| `app/schemas/metrics_collection.py` | `class Config` → `model_config` |
| `app/schemas/tools.py` | `class Config` → `model_config` |
| `app/routers/miniapps.py` | `class Config` → `model_config` |
| `app/rag/query_classifier.py` | `class Config` → `model_config` |
| `app/schemas/rag_feedback_schemas.py` | `class Config` → `model_config` |
| `app/schemas/workflow_session.py` | `class Config` → `model_config` |
| `app/schemas/director_pack.py` | `class Config` → `model_config` |
| `app/routers/mcp.py` | `@validator` → `@field_validator` |
| `app/routers/crebit.py` | `class Config` → `model_config` |
| `app/schemas/telemetry_schemas.py` | `class Config` → `model_config` |
| `app/schemas/settlement_schemas.py` | `class Config` → `model_config` |
| `app/schemas/versioning_schemas.py` | `class Config` → `model_config` |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.2 | 2026-01-16 | Part C: UX/UI/디자인 체크리스트 추가 (WCAG 2.2, Core Web Vitals, React 19 패턴) |
| 1.1 | 2026-01-16 | 실제 검증 결과 추가 (Appendix A, B), Qdrant 컬렉션 적재 완료 |
| 1.0 | 2026-01-16 | 초기 버전 (2026 Best Practices 기반) |
