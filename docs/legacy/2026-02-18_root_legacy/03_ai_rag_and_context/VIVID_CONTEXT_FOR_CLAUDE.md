# 🎨 Vivid 프로젝트 통합 컨텍스트

> **목적:** Claude Code가 Vivid 작업 시 참조할 전체 맥락
> **마지막 업데이트:** 2026-02-05

---

## 📌 Quick Reference

| 항목 | 값 |
|------|-----|
| **프로젝트 경로** | `/Users/ted/vivid` |
| **서비스 URL** | crebit.studio |
| **Frontend** | Next.js 16, React 19 (port 3100) |
| **Backend** | FastAPI, Python 3.11 (port 8100) |
| **AI** | Google Gemini API |
| **DB** | PostgreSQL 5433, Redis 6380, Qdrant 6333 |

---

## 🚀 현재 상태 (2026-01)

### 완료된 UX 혁신

| Innovation | 효과 |
|------------|------|
| Smart Onboarding | 3가지 진입 옵션 |
| Value Before Step | 어느 단계든 진입 가능 |
| Parallel Preview Grid | 4단계 동시 미리보기 |
| Story Intelligence | 생성 12분→6분 (-50%) |
| Smart Render Pipeline | 비용 50% 절감 |
| Mobile Carousel | 모바일 최적화 |
| Intent-Driven Entry | 자연어 명령 진입 |

### 성과 지표

| 지표 | Before | After | 개선 |
|------|:------:|:-----:|:----:|
| UX Score | 7.2/10 | **9.2/10** | +28% |
| 첫 영상 제작 시간 | 25분 | **7분** | -72% |
| 이탈률 | 40% | **8%** | -80% |
| 모바일 이탈률 | 60% | **15%** | -75% |

---

## 🧩 13개 Dimension Apps

| App | 기능 |
|-----|------|
| 1D~4D | 차원별 콘텐츠 생성 |
| Abyss Mirror | 창작 DNA 분석 |
| Reference Decoder | 레퍼런스 분석 |
| Scenario Generator | 시나리오 생성 |
| Sound Crafter | 사운드 생성 |
| Storyboard Sketcher | 스토리보드 |
| Prompt Alchemy | 프롬프트 최적화 |
| Visual Realizer (3D) | 이미지 생성 |
| Video Maker (VEO) | 비디오 생성 |
| Quality Director | 품질 검증 |
| Aesthetic Director | 미학 가이드 |

---

## 📋 P0 백로그 (Activation 최적화)

> **Activation 정의:** DNA Lab에서 첫 영상 업로드 → 분석 완료 → 결과 확인

### P0-1: 온보딩/진입

| 티켓 | 제목 | 컴포넌트 | 설명 |
|------|------|----------|------|
| VIV-001 | Intent-driven Entry | `Landing.tsx` | 목적별 버튼 3개: "영상 분석 / 스토리 만들기 / 바로 제작" |
| VIV-002 | Value-before-signup | `DNALab.tsx` | 로그인 전 샘플 분석 결과 미리보기 |

### P0-2: 업로드/분석 플로우

| 티켓 | 제목 | 컴포넌트 | 설명 |
|------|------|----------|------|
| VIV-003 | 업로드 정보 표시 | `UploadArea.tsx` | 포맷/길이/예상시간 표시 |
| VIV-004 | 분석 진행률 표시 | `AnalysisProgress.tsx` (신규) | progress bar + 남은 단계 |
| VIV-005 | 에러 복구 UI | `AnalysisError.tsx` (신규) | 1클릭 재시도 + 에러 가이드 |

### P0-3: 결과 화면

| 티켓 | 제목 | 컴포넌트 | 설명 |
|------|------|----------|------|
| VIV-006 | Next Action 제한 | `AnalysisResult.tsx` | 버튼 2개: "DNA 변주 / 스토리로" |
| VIV-007 | 결과 요약 카드 | `DNASummaryCard.tsx` (신규) | 핵심 DNA 5~7개 불릿 |

### P0-4: 크레딧/과금

| 티켓 | 제목 | 컴포넌트 | 설명 |
|------|------|----------|------|
| VIV-008 | 크레딧 소모 표시 | `CreditIndicator.tsx` (신규) | "이 작업에 3 크레딧" |
| VIV-009 | 맥락형 페이월 | `PaywallModal.tsx` | 크레딧 부족 시 인라인 충전 |

### 구현 권장 순서

```
1. VIV-003 (업로드 정보) ← 빠르게 적용 가능
2. VIV-004 (진행률) ← 사용자 경험 즉시 개선
3. VIV-005 (에러 복구) ← 이탈 방지
4. VIV-006 + VIV-007 (결과 화면)
5. VIV-001 + VIV-002 (온보딩)
6. VIV-008 + VIV-009 (크레딧)
```

---

## 🎬 데모 시나리오

### 추천 시나리오 A: DNA Lab 풀 플로우 (5분)

1. 홈 → IP 선택 (umbrella-encounter)
2. DNA Lab 진입
3. Reference Decoder 실행 (영상 분석)
4. Abyss Mirror (캐릭터 변주 "INTJ로")
5. 결과 확인 + 체인 요약 사이드바

### 추천 시나리오 B: 메가앱 쇼케이스 (3분)

1. 홈페이지 히어로 + 네비게이션
2. 차원 앱 레일 데모
3. 각 차원 앱 빠른 둘러보기

---

## 📁 핵심 파일

| 파일 | 역할 |
|------|------|
| `CLAUDE.md` | 메인 설정 (먼저 읽기!) |
| `backend/CLAUDE.md` | Backend 가이드 |
| `frontend/CLAUDE.md` | Frontend 가이드 |
| `docs/DIMENSION_APP_DEVELOPER_GUIDE.md` | 앱 개발 가이드 |
| `backend/app/generation_client.py` | Shot/Prompt Contract |
| `frontend/src/lib/api.ts` | Typed API Client |

---

## 🔧 개발 명령어

```bash
# Backend 테스트
cd /Users/ted/vivid/backend && source .venv/bin/activate && pytest --tb=short -q

# Frontend 빌드
cd /Users/ted/vivid/frontend && npm run build

# Backend 실행
cd /Users/ted/vivid/backend && source .venv/bin/activate && uvicorn app.main:app --port 8100 --reload

# Frontend 실행
cd /Users/ted/vivid/frontend && npm run dev
```

---

## ⚠️ 알려진 이슈

| 이슈 | 상태 | 영향 |
|------|:----:|------|
| `/api/v1/ip/{slug}/generate` 미구현 | ⚠️ | 생성 버튼 에러 가능 |
| Auth bypass 임시 비활성화 | ℹ️ | 로컬 데모용 OK |

---

## 📊 다음 단계

1. **VIV-003~005** 구현 (업로드/분석 플로우)
2. **VIV-006~007** 구현 (결과 화면)
3. 데모 테스트 후 피드백 반영

---

*이 문서는 소미 🐱가 정리한 Vivid 프로젝트 전체 컨텍스트입니다.*
