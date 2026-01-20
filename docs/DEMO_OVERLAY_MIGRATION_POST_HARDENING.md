# Demo Overlay → Production Migration Guide (Post‑Hardening)

> **목적**: Hardening 완료 직후, 데모용 Soft Overlay를 실제 데이터 흐름으로 안전하게 전환한다.
> **대상 문서**: `HARDENING_MASTER_PLAN_2026.md`, `SSOT_DECISIONS_LOG.md`, `ip-first-coordination-roadmap.md`
> **작성일**: 2026-01-20

---

## 0) 전제 조건 (Hardening 완료 체크)

Hardening이 완료되었는지 **반드시 확인** 후 진행한다.

### ✅ 완료 기준 (필수)
- H1.1 CORS allow_headers 최소화 (명시 8개)
- H1.2 WebSocket JWT 인증
- H1.3 SecretStr 마이그레이션
- H1.3b encryption fallback 제거
- H1.4 RLS 마이그레이션
- H1.4b get_db_with_rls 도입
- H1.5 TenantMiddleware 활성화

> **완료 확인**: `docs/HARDENING_MASTER_PLAN_2026.md` H1 체크리스트

---

## 1) Demo Overlay 구조 요약 (현재)

Soft Overlay는 다음 원칙으로 구성된다.

- **글로벌 DEMO_MODE 플래그 사용 금지**
- **slug 기반 오버라이드**만 사용
- **단일 소스 파일**에서 demo 데이터 관리

### 핵심 파일
- `frontend/src/lib/demo-ip-overrides.ts`
- `frontend/src/app/page.tsx`
- `frontend/src/app/ip/[slug]/_components/IPDetailClient.tsx`
- `frontend/src/components/home/IPRailCard.tsx`

---

## 2) 마이그레이션 전략 (데모 → 프로덕션)

### ✅ 원칙
1. **실데이터 우선, 데모는 fallback**
2. **demo 파일 하나만 제거하면 제거 완료** 상태로 유지
3. UI 구조는 유지하고 **데이터만 교체**

---

## 3) 실제 마이그레이션 단계

### Step 1 — Demo 오버레이 비활성화

- 파일 제거 또는 비활성화
  - `frontend/src/lib/demo-ip-overrides.ts` 삭제
  - 또는 `getDemoIPOverride()`가 항상 `null` 반환하도록 처리

### Step 2 — IP 상세 비디오 소스 전환

`IPDetailClient.tsx`에서 demo fallback 제거

**Before**
```ts
const demoOverride = getDemoIPOverride(ip.slug);
const videoSrc = demoOverride?.detailVideoUrl || ip.preview_video_url || ip.banner_url || ip.thumbnail_url;
```

**After**
```ts
const videoSrc = ip.preview_video_url || ip.banner_url || ip.thumbnail_url;
```

### Step 3 — 워크플로우 카드 전환

IP 상세 페이지에서 demo workflows 제거

**Before**: demo override workflows
**After**: 실제 추천 결과 `recommendations` 기반 렌더링

권장 우선순위
1. Tool Recommender 결과
2. Preset 기반 default fallback

### Step 4 — Home 카드 데이터 전환

`page.tsx`에서 demo 카드 제거

**Before**: `DEMO_IP_LIST`
**After**: `/api/v1/ip/home/rails` 결과만 사용

### Step 5 — IPRailCard hover video 제거 (선택)

- 실제 데이터에 `preview_video_url`이 안정적으로 존재할 때만 유지
- 없다면 video hover는 제거하고 이미지 hover만 사용

---

## 4) 회귀 테스트 체크리스트

### UI 동작
- [ ] 홈 IP 레일 정상 표시
- [ ] IP 카드 hover 시 썸네일 유지 or preview 동작
- [ ] IP 상세 진입 시 video 정상 로딩
- [ ] 우측 추천 카드 정상 렌더링
- [ ] 각 워크플로우 링크 정상 이동

### API
- [ ] `/api/v1/ip/home/rails` 정상
- [ ] `/api/v1/ip/catalog/{slug}` 정상
- [ ] `/api/v1/tools/recommend` 정상

### 빌드
```bash
cd frontend && npm run build
```

---

## 5) 롤백 플랜

문제 발생 시 다음 중 하나 선택:

1. `demo-ip-overrides.ts` 복원
2. `videoSrc` fallback에 demo URL 복구
3. 워크플로우 카드 demo grid 재활성화

---

## 6) 권장 PR 단위

- **PR 1**: demo-ip-overrides 제거 + IPDetailClient video 정상화
- **PR 2**: workflow 카드 실데이터 전환
- **PR 3**: 홈 demo 카드 제거

---

## 7) 참고 문서

- `/docs/HARDENING_MASTER_PLAN_2026.md`
- `/docs/SSOT_DECISIONS_LOG.md`
- `/Users/ted/.claude/plans/ip-first-coordination-roadmap.md`

---

## 8) 완료 기준 (Definition of Done)

✅ Demo 파일 제거 후 **빌드 통과**
✅ Home/IP Detail/Workflow 카드가 **실데이터로 정상 동작**
✅ Hardening 이후에도 **권한/보안/테넌트 정책 정상 유지**

---

> 이 문서는 Hardening 완료 직후 바로 실행 가능한 **데모 제거 + 실데이터 전환 가이드**다.
