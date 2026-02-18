# PDR: PROMPTY.CO.KR 설계 결정 기록

> **Date**: 2026-02-02
> **Version**: 1.1 (Dual AI Update)
> **Status**: 확정

---

## 📋 개요

prompty.co.kr은 **Dual AI 워크플로우 가이드** 플랫폼입니다.

**핵심 철학**: Human-in-the-Loop + Dual AI
- AI API 직접 호출 ❌
- 가이드만 제공 ✅
- **Gemini CLI + Antigravity(Claude Code)** 듀얼 구조
- 같은 프로젝트 폴더를 두 AI가 공유

---

## 🔧 확정된 기술 결정

### PDR-001: 동기화 아키텍처 → 폴링 + WebSocket

| 결정 | 폴링 + WebSocket 이벤트 |
|------|------------------------|
| 대안 | Yjs CRDT, Loro, Automerge |
| 이유 | 워크플로우 상태는 CRDT 충돌 해결 불필요 |
| 비용 | 폴링 구현 1-2일 vs Yjs 2-3주 |

```typescript
// 구현 패턴
useSWR('/api/state', fetcher, { refreshInterval: 5000 });
ws.on('state-updated', () => mutate('/api/state'));
```

---

### PDR-002: 데이터 페칭 → SWR

| 결정 | SWR (4.2KB) |
|------|-------------|
| 대안 | TanStack Query (10KB) |
| 이유 | 단순 CRUD, 번들 크기 중요 |
| 설정 | refreshInterval: 5000, revalidateOnFocus: false |

---

### PDR-003: Feature Flags + 분석 → PostHog

| 결정 | PostHog |
|------|---------|
| 대안 | Unleash + Mixpanel |
| 이유 | 무료 1M 이벤트, Feature Flag + 분석 통합 |
| 설정 | autocapture: false, 객체-동작 네이밍 |

---

### PDR-004: API 설계 → REST 유지

| 결정 | REST (FastAPI) |
|------|---------------|
| 대안 | GraphQL, tRPC, gRPC |
| 이유 | 단순 CRUD, FastAPI + Next.js 조합에서 최적 |

---

### PDR-005: 템플릿 스토리지 → JSONB

| 결정 | PostgreSQL JSONB |
|------|-----------------|
| 대안 | Markdown 원본 저장 |
| 이유 | 풍부한 쿼리, 런타임 파싱 불필요 |
| 인덱싱 | GIN + 표현식 인덱스 필수 |

```sql
CREATE INDEX idx_stages_category ON prompty_template ((stages->>'category'));
CREATE INDEX idx_stages_gin ON prompty_template USING GIN (stages jsonb_path_ops);
```

---

### PDR-006: 완전 자동화 거부

| 결정 | End-to-End 파이프라인 거부 |
|------|--------------------------|
| 이유 | Human-in-the-Loop 철학 |
| 예외 | 없음 |
| 대신 | AI 가이드 + 인간 판단 |

---

### PDR-007: 격리된 백엔드 복원 전략

| 결정 | backup/routers/ → 필요 시 Feature Flag로 복원 |
|------|---------------------------------------------|
| Phase 1 | 현재 격리 유지 |
| Phase 2 | PostHog Feature Flag로 점진적 활성화 |
| 6개월 후 | 미사용 코드 완전 삭제 |

---

### PDR-008: PWA → 현재 불필요

| 결정 | 온라인 전용 |
|------|-----------|
| 이유 | Dual AI(Gemini+Antigravity) 로컬 공유 폴더 모델 |
| 재검토 | 6개월 후 |

---

## ⚡ 성능 최적화 필수 항목

| 항목 | 예상 효과 | 구현 시간 |
|------|----------|----------|
| asyncpg + uvloop | 처리량 2-4x | 4시간 |
| JSONB GIN 인덱스 | 쿼리 10x 빠름 | 2시간 |
| Next.js Suspense | TTFB 78% 단축 | 4시간 |
| PostHog 통합 | 사용자 행동 추적 | 2시간 |

---

## 🚫 피할 것

| 기술 | 이유 |
|------|------|
| Yjs CRDT | 오버엔지니어링 |
| GraphQL | 단순 CRUD에 불필요 |
| TanStack Query | 번들 크기 3배 |
| 마이크로서비스 | 모놀리스가 적합 |
| PWA (현재) | 필요 없음 |

---

## 📚 참고 문서

- `legacy_vivid/` - 피벗 전 레거시 문서
- `ARCHITECTURE_PROMPTY.md` - 신규 아키텍처
- `backup/routers/` - 격리된 백엔드 코드
