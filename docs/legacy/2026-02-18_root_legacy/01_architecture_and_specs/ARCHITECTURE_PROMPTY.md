# PROMPTY.CO.KR 아키텍처 2026

> **Date**: 2026-02-02
> **Version**: 1.1 (Dual AI Update)
> **Philosophy**: Human-in-the-Loop + Dual AI

---

## 🏗️ 시스템 아키텍처 (Dual AI)

```
┌──────────────────────────────────────────────────────────┐
│              🖥️ 사용자 로컬 (공유 프로젝트 폴더)           │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │        projects/{project-name}/ (공유!)           │   │
│  │  ┌────────────┐              ┌────────────┐      │   │
│  │  │ Gemini CLI │◄────────────►│ Antigravity│      │   │
│  │  │ (분석/평가)│   파일 동기화  │(Claude Code)│      │   │
│  │  └────────────┘              └────────────┘      │   │
│  │         │                          │             │   │
│  │         ▼                          ▼             │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  STATE.md     ← 상태 (둘 다 읽기/쓰기)    │   │   │
│  │  │  PROMPTS.md   ← Antigravity가 정제        │   │   │
│  │  │  ANALYSIS.md  ← Gemini가 분석             │   │   │
│  │  └──────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────┘
                            │ 동기화
                            ▼
┌─────────────────────────────────────────────────────┐
│                prompty.co.kr                        │
│  ┌─────────────────────────────────────────────┐   │
│  │              Next.js 15 App                  │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │ Guide   │ │ Critique│ │ Template│       │   │
│  │  │ Workflow│ │ Viewer  │ │ Market  │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────┘   │
│                        │                            │
│                   REST API                          │
│                        ▼                            │
│  ┌─────────────────────────────────────────────┐   │
│  │           FastAPI Backend                    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │projects │ │templates│ │critique │       │   │
│  │  │ router  │ │ router  │ │ router  │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────┘   │
│                        │                            │
│                        ▼                            │
│  ┌─────────────────────────────────────────────┐   │
│  │         PostgreSQL (Railway)                 │   │
│  │  JSONB: stages, steps, critique_checklist   │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 📦 기술 스택

| 레이어 | 기술 | 버전 |
|--------|------|------|
| **Frontend** | Next.js | 15 |
| **State** | SWR | 2.x |
| **Backend** | FastAPI | 0.100+ |
| **Database** | PostgreSQL | 17+ |
| **Driver** | asyncpg | 0.29+ |
| **ORM** | SQLAlchemy | 2.0 |
| **Deploy** | Railway Pro | - |
| **Analytics** | PostHog | Cloud |

---

## 🔄 데이터 흐름

### 1. 워크플로우 가이드 조회

```
User → /prompty/guide/[id] → SWR fetch
                              ↓
                    GET /api/prompty/guide/{id}
                              ↓
                    PostgreSQL (JSONB stages)
                              ↓
                    Response: steps, prompts, checklists
```

### 2. 상태 동기화 (폴링 + WebSocket)

```typescript
// SWR 폴링 (5초)
const { data } = useSWR('/api/state', { refreshInterval: 5000 });

// WebSocket 즉시 반영
ws.on('state-updated', () => mutate('/api/state'));
```

---

## 📊 데이터베이스 스키마

### prompty_template

| Column | Type | Description |
|--------|------|-------------|
| id | INT | PK |
| name | VARCHAR | 템플릿 이름 |
| stages | JSONB | 워크플로우 단계 |
| critique_checklist | JSONB | 평가 항목 |
| creator_id | INT | FK → users |

**필수 인덱스:**
```sql
CREATE INDEX idx_stages_category ON prompty_template ((stages->>'category'));
CREATE INDEX idx_stages_gin ON prompty_template USING GIN (stages jsonb_path_ops);
```

---

## 🚀 성능 최적화

### Backend (FastAPI)

```python
# ✅ 비동기 일관성
stmt = select(PromptyTemplate).where(...)
result = await db.execute(stmt)

# ✅ 병렬 쿼리
project, guides = await asyncio.gather(
    db.execute(select(PromptyProject)...),
    db.execute(select(PromptyGuideLog)...)
)
```

### Frontend (Next.js 15)

```typescript
// ✅ Suspense 경계
<Suspense fallback={<Skeleton />}>
  <TemplateList />
</Suspense>
```

---

## 📈 모니터링 (PostHog)

### 핵심 이벤트

```typescript
posthog.capture('template_viewed', { template_id, category });
posthog.capture('guide_step_completed', { step, duration });
posthog.capture('critique_submitted', { score, verdict });
```

### Feature Flags

```typescript
if (posthog.isFeatureEnabled('new_critique_ui')) {
  return <NewCritiqueUI />;
}
```

---

## 🔐 보안

- Railway Private Networking (내부 DB 연결)
- Environment Variables (시크릿 관리)
- CORS: prompty.co.kr 도메인만 허용

---

## 📁 프로젝트 구조

```
vivid/
├── backend/
│   └── app/
│       ├── routers/
│       │   └── prompty/       ← 신규
│       │       ├── projects.py
│       │       ├── templates.py
│       │       ├── critique.py
│       │       └── guide.py
│       └── models_prompty.py  ← 신규
│
├── frontend/
│   └── src/app/
│       └── prompty/           ← 신규
│           ├── page.tsx
│           ├── projects/
│           ├── guide/
│           └── templates/
│
├── backup/
│   └── routers/               ← 격리된 레거시
│
└── docs/
    ├── PDR_PROMPTY.md         ← 설계 결정
    ├── ARCHITECTURE_PROMPTY.md ← 이 문서
    └── legacy_vivid/          ← 피벗 전 문서
```

---

## 🎯 핵심 원칙

1. **Human-in-the-Loop**: AI는 가이드, 사람이 최종 판단
2. **Dual AI 공유 폴더**: Gemini CLI(분석) + Antigravity/Claude(정제) 협업
3. **AI API 직접 호출 ❌**: 플랫폼이 아닌 로컬에서 AI 실행
4. **가이드만 제공**: 프롬프트 복사 + Critique 체크리스트
5. **점진적 고도화**: backup/routers/ 필요 시 복원
