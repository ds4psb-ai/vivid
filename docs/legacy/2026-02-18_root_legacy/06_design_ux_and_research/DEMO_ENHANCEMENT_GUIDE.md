# Demo Enhancement Guide (투자자 데모 고도화 가이드)

> **목적**: 투자자 시연용 데모를 실제 워크플로우 체험이 가능한 수준으로 고도화
> **작성일**: 2026-01-20
> **대상**: 데모 고도화 담당 개발자

---

## ⚠️ 주요 백엔드 변경사항 (2026-01-20 23:00)

> [!IMPORTANT]
> 아래 변경사항으로 인해 **반드시 백엔드를 재시작**해야 합니다.
> 간편 실행: `/server-demo` 워크플로우 사용

### 변경 내용

| 항목 | 변경 내용 | 영향 |
|------|----------|------|
| **CORS 미들웨어 순서** | `CORSMiddleware`를 `main.py` 가장 아래로 이동 (마지막 add = 첫 번째 실행) | 프론트엔드 API 호출 시 CORS 에러 해결 |
| **데모 IP DB 시드** | `scripts/seed_demo_ips.py` 생성 → DB에 `umbrella-encounter`, `cooking-anime-mv` 삽입 | 백엔드 API가 실제 데이터 반환 |
| **DB 스키마 업데이트** | `ip_catalog`에 `chat_enabled` 등 컬럼 추가, `ip_workflow_presets`에 `workflow_capsule_id` 추가 | Alembic 마이그레이션 불필요 (직접 ALTER TABLE 완료) |
| **Mute 버튼 수정** | `IPRailCard.tsx`에 `useEffect` 상태 동기화 + `stopImmediatePropagation()` 추가 | 호버 시 뮤트 토글 정상 동작 |

### 새 파일

| 파일 | 용도 |
|------|------|
| `backend/scripts/seed_demo_ips.py` | 데모 IP 시드 스크립트 (재실행 가능) |
| `.agent/workflows/server-demo.md` | 데모 서버 원클릭 실행 워크플로우 |

### 실행 방법

```bash
# 1. 워크플로우 실행 (권장)
# Cursor에서 /server-demo 입력

# 2. 또는 수동 실행
cd backend && source venv/bin/activate
python scripts/seed_demo_ips.py  # 데모 IP 시드 (최초 1회)
uvicorn app.main:app --port 8100 --reload

cd frontend && bun run dev  # 별도 터미널
```

---


## 1. 현재 상태 요약

### 완료된 항목 ✅
- 메인 페이지 단순화 (2개 IP Rail + 차원 플로우 CTA)
- 사이드바 단순화 (홈, 숏폼, 애니MV, 플로우)
- IP 상세 페이지 기본 UI (비디오 플레이어 + 워크플로우 카드)
- React Hooks 버그 수정, CSP media-src 설정
- `demo-ip-overrides.ts` 단일 소스 관리

### 핵심 파일
| 파일 | 역할 |
|------|------|
| `frontend/src/lib/demo-ip-overrides.ts` | 데모 IP 데이터 SSoT |
| `frontend/src/app/page.tsx` | 메인 홈페이지 |
| `frontend/src/app/ip/[slug]/_components/IPDetailClient.tsx` | IP 상세 페이지 |
| `frontend/src/components/CollapsibleSidebar.tsx` | 좌측 사이드바 |
| `frontend/src/components/home/IPRailCard.tsx` | IP 카드 컴포넌트 |

---

## 2. 고도화 TODO 목록

### 2.1 사이드바 네비게이션 수정 (P0)

**현재 문제**: 사이드바에서 숏폼/애니MV 클릭 시 바로 상세 페이지로 이동

**수정 방향**:
```
숏폼 웹드라마 → (숏폼) 으로 이름 변경
클릭 시 → /shortform (새 페이지) → IP 카드 레일 표시 → 카드 클릭 시 상세

애니메이션 MV → 클릭 시 → /anime-mv (새 페이지) → IP 카드 레일 표시 → 카드 클릭 시 상세
```

**구현 파일**:
- `CollapsibleSidebar.tsx` - 라우트 변경
- `frontend/src/app/shortform/page.tsx` - 신규 생성
- `frontend/src/app/anime-mv/page.tsx` - 신규 생성

### 2.2 메인 하단 개별 앱 레일 추가 (P0)

**현재 문제**: 차원 앱 그리드가 제거됨

**수정 방향**: 메인 하단에 개별 차원 앱을 한 줄 레일로 표시
```tsx
// page.tsx 하단에 추가
<DimensionAppRail /> // 1D~4D, AD, AI, VEO 등 핵심 앱만
```

**참고**: 기존 `DimensionGrid` 컴포넌트 재활용 또는 단순화

### 2.3 동적 워크플로우 추천 (P1) ⭐ 핵심

**목표**: 사용자가 변주 프롬프트 입력 → 생성 클릭 → 관련 워크플로우 동적 추천

**구현 옵션**:

#### Option A: 하드코딩 (빠른 구현)
```typescript
// demo-ip-overrides.ts
const WORKFLOW_TEMPLATES = {
  "character-variation": [
    { app: "reference-decoder", order: 1 },
    { app: "abyss-mirror", order: 2 },
    { app: "story-architect", order: 3 },
    { app: "video-maker", order: 4 },
  ],
  "style-remix": [
    { app: "reference-decoder", order: 1 },
    { app: "aesthetic-director", order: 2 },
    { app: "visual-realizer", order: 3 },
  ],
};
```

#### Option B: Gemini Flash 기반 (권장)
```typescript
// 간단한 LLM 기반 추천
const response = await fetch("/api/dimension/recommend-workflow", {
  method: "POST",
  body: JSON.stringify({
    user_prompt: "캐릭터를 INTJ로 변주하고 싶어",
    ip_slug: "umbrella-encounter",
    content_type: "vertical-shortform",
  }),
});
// → Gemini Flash가 적합한 워크플로우 템플릿 추천
```

**기존 API 참고**:
- `/api/v1/tools/recommend` - 도구 추천 API (이미 구현됨)
- `backend/app/routers/tool_recommender.py`

### 2.4 세션별 워크플로우 진행 계승 (P1) ⭐ 핵심

**확인 필요**: 이미 구현된 세션 컨텍스트 시스템 존재

**관련 파일**:
- `backend/app/workflow/tiered_context.py` - TieredContext (SessionContext → StepContext → InputContext)
- `backend/app/services/capsule_executor.py` - 캡슐 실행
- `frontend/src/contexts/SessionContext.tsx` - 프론트 세션

**확인 사항**:
```bash
# 세션 컨텍스트 관련 코드 검색
grep -r "TieredContext" backend/
grep -r "SessionContext" frontend/src/
grep -r "step_context" backend/
```

**구현 방향**:
1. Reference Decoder 실행 결과 → 세션에 저장
2. Abyss Mirror 실행 시 → 이전 단계 결과 자동 주입
3. 각 단계 완료 시 → 진행 상태 UI 업데이트

### 2.5 거장 로직 연동 (P2)

**기존 시스템**:
- Tier0: NotebookLM (CDP) - 거장 지식베이스
- Tier1: Qdrant + BM25 - 하이브리드 검색

**관련 파일**:
- `backend/app/rag/hybrid_rag.py`
- `backend/app/rag/tier0_notebooklm.py`
- `backend/app/rag/rag_presets.py` - 거장 스타일 힌트

**사용법**:
```python
from app.rag.hybrid_rag import hybrid_query

result = await hybrid_query(
    query="봉준호 스타일로 변주",
    dimension="AD",
    auteur_key="bong",
)
```

---

## 3. Rail 1: 숏폼 웹드라마 고도화

### IP: umbrella-encounter (우산 속 만남)

**데모 시나리오**:
1. 사용자가 변주 프롬프트 입력: "캐릭터를 INTJ로 변주"
2. 생성 클릭 → 워크플로우 추천:
   - Reference Decoder (영상 분석)
   - Abyss Mirror (캐릭터 변주)
   - Story Architect (스토리 변주)
   - Video Maker (영상 생성)
3. 각 단계 실행 → 결과가 다음 단계로 전달
4. 최종 변주 콘텐츠 출력

**워크플로우 (4단계)**:
```
Reference Decoder (4D) → Abyss Mirror (AI) → Story Architect (2D) → VEO/Kling
```

---

## 4. Rail 2: 애니메이션 MV 고도화

### IP: cooking-anime-mv (흑백요리사2 애니 오프닝)

**데모 시나리오** (복잡):
1. 영상 업로드 → 씬별 프레임 분석 (Reference Decoder)
2. 캐릭터 DNA 추출 (Abyss Mirror)
3. 스타일 가이드 생성 (Aesthetic Director)
4. BGM 생성 (Suno V5)
5. 씬별 영상 생성 (VEO/Kling) - Character Consistency 유지
6. 씬 합성 + 오디오 싱크

**워크플로우 (8단계)**:
```
Reference Decoder → Abyss Mirror → Aesthetic Director → Character Consistency Setup
    → Suno → [Loop: 씬별 VEO 생성] → 씬 합성 → Final Output
```

**핵심 기술**:
- Veo Ingredients (최대 3개 참조 이미지)
- Scene Extension (씬 연결)
- Kling Elements (최대 4개 참조 이미지)

**관련 플랜**: `/Users/ted/.claude/plans/zazzy-sparking-moon.md`

---

## 5. 기술 참고 사항

### Gemini API 설정
```bash
# backend/.env
GOOGLE_API_KEY=...  # 이미 설정됨
```

### 주요 엔드포인트
| 엔드포인트 | 용도 | 크레딧 |
|------------|------|--------|
| `/api/dimension/4d/analyze-video` | Reference Decoder | 8 |
| `/api/dimension/mirror/chat` | Abyss Mirror | 5/턴 |
| `/api/dimension/aesthetic/direct` | Aesthetic Director | 10 |
| `/api/dimension/veo/generate/stream` | VEO Video | 200 |
| `/api/dimension/kling/generate` | Kling Video | 50 |
| `/api/dimension/suno/generate` | Suno Music | 20 |

### 크레딧 충전 (로컬 테스트용)
```bash
docker exec crebit-postgres psql -U crebit_user -d crebit_canvas -c \
  "UPDATE user_credits SET balance = 100000;"
```

---

## 6. 테스트 체크리스트

### UI 동작
- [ ] 사이드바 (숏폼) 클릭 → 레일 페이지 → 카드 클릭 → 상세
- [ ] 사이드바 애니MV 클릭 → 레일 페이지 → 카드 클릭 → 상세
- [ ] 메인 하단 차원 앱 레일 표시
- [ ] IP 상세에서 프롬프트 입력 → 생성 → 워크플로우 추천
- [ ] 워크플로우 각 단계 클릭 → 해당 앱으로 이동 → 세션 컨텍스트 유지

### API 연동
- [ ] Reference Decoder 영상 분석 정상
- [ ] Abyss Mirror 캐릭터 변주 정상
- [ ] 세션 컨텍스트 계승 정상
- [ ] 거장 RAG 연동 정상

### 빌드
```bash
cd frontend && npm run build
cd backend && pytest --tb=short -q
```

---

## 7. 참고 문서

- `/docs/DEMO_OVERLAY_MIGRATION_POST_HARDENING.md` - 데모 제거 가이드
- `/docs/DIMENSION_APP_DEVELOPER_GUIDE.md` - 앱 개발 가이드
- `/Users/ted/.claude/plans/zazzy-sparking-moon.md` - 투자자 데모 플랜
- `/docs/13_CREDITS_AND_BILLING_SPEC_V1.md` - 크레딧 시스템

---

## 8. 알려진 이슈

### 생성하기 버튼 JSON 파싱 에러
```
SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON
```
**위치**: `IPDetailClient.tsx:287 handleGenerate`
**원인**: 백엔드 `/api/v1/ip/{slug}/generate` 엔드포인트 미구현 또는 에러 응답
**해결**: 데모용 mock 응답 또는 실제 엔드포인트 구현 필요

---

> 이 문서는 데모 고도화 개발자를 위한 가이드입니다.
> 질문: Slack #vivid-dev 또는 CLAUDE.md 참조
