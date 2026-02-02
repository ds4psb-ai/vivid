# DNA Lab UX Migration Strategy

> **목표**: 디자이너 결과물(V5/V6/V7)의 혁신적 UX를 기존 DNA Lab 기능에 손상 없이 적용
>
> **작성일**: 2026-01-31

---

## 1. 디자인 결과물 비교 분석

### 1.1 세 가지 디자인 개요

| 특성 | V5 (Centered Card) | V6 (Split Dashboard) | V7 (Cinematic) |
|------|-------------------|---------------------|----------------|
| **레이아웃** | 중앙 카드 | 사이드바 + 메인 | 중앙 카드 + Aurora |
| **진입 UX** | Quick Start 전용 | 전체 워크플로우 | Quick Start + 시네마틱 |
| **복잡도** | ⭐⭐ (심플) | ⭐⭐⭐⭐ (기능적) | ⭐⭐⭐ (밸런스) |
| **브랜드 정합성** | Light 기본 | Light/Dark 모두 | **Dark 기본 ✅** |
| **한글 라벨** | 영어 중심 | **한글 완벽 ✅** | **한글 완벽 ✅** |
| **Credit 표시** | ✅ | ✅ | ✅ |
| **Evidence** | ❌ | ✅ (배지) | ❌ |
| **Aurora 배경** | ❌ | ❌ | ✅ |

### 1.2 권장 조합 전략

```
┌─────────────────────────────────────────────────────────────┐
│                    권장: 하이브리드 접근                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Quick Mode (master=velvet&mode=quick)                      │
│  └── V7 (Cinematic) 또는 V5 (Centered Card)                │
│      • 심플한 온보딩 경험                                    │
│      • Master 프로필 강조                                    │
│      • Aurora 배경으로 프리미엄 느낌                          │
│                                                             │
│  Full Workflow (step=analysis 등)                           │
│  └── V6 (Split Dashboard)                                   │
│      • 사이드바 컨트롤                                       │
│      • 메인 영역 결과 표시                                   │
│      • 기존 Panel 시스템과 호환                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 현재 DNA Lab 컴포넌트 ↔ 새 디자인 매핑

### 2.1 컴포넌트 매핑 테이블

| 현재 컴포넌트 | 역할 | V5 대응 | V6 대응 | V7 대응 |
|--------------|------|---------|---------|---------|
| `DNALabOnboarding` | 진입점 3가지 옵션 | ✅ 중앙 카드 | ❌ 없음 | ✅ 시네마틱 카드 |
| `DNALabOverview` | 2x2 그리드 | ❌ 불필요 | ❌ 불필요 | ❌ 불필요 |
| `DNALabWorkflowProgress` | 3단계 스테퍼 | ✅ 하단 3-dot | ✅ 상단 3-step | ✅ 하단 3-step |
| `UnifiedWorkflowShell` | 레이아웃 컨테이너 | N/A | ✅ Split | N/A |
| `MegaAppHeader` | 상단 헤더 | ✅ Navbar | ✅ Navbar + Sidebar | ✅ Navbar |
| `MegaAppAurora` | 배경 효과 | ❌ 없음 | ❌ 없음 | ✅ Aurora |
| `DNALabStepPanel` | 단계별 래퍼 | N/A | ✅ 사이드바 | N/A |
| `MissingDataBanner` | 누락 데이터 경고 | ❌ 없음 | ✅ 토스트 형태 | ❌ 없음 |
| `DNALabChainSummary` | 사이드바 요약 | ❌ 없음 | ✅ 메인 영역 | ❌ 없음 |

### 2.2 기능별 매핑

| 기능 | 현재 구현 | 새 디자인 위치 | 마이그레이션 난이도 |
|------|----------|---------------|-------------------|
| **Master 선택** | `DNALabOnboarding` | V5/V7: 중앙 카드 상단 | 🟢 쉬움 |
| **Video URL 입력** | `UnifiedAnalysisPanel` | V5/V7: 중앙 입력 필드 | 🟢 쉬움 |
| **3-Step 진행률** | `DNALabWorkflowProgress` | 모두: 스테퍼 컴포넌트 | 🟡 중간 |
| **Credit 표시** | `DimensionPanel.Header` | 버튼 내부 | 🟢 쉬움 |
| **Chain Data** | `DimensionChainContext` | **변경 없음 (로직)** | ✅ 불필요 |
| **Evidence Refs** | `DNALabChainSummary` | V6: 메인 영역 배지 | 🟡 중간 |
| **Pipeline 실행** | `useDNALabPipeline` | **변경 없음 (로직)** | ✅ 불필요 |
| **Session 복원** | `useIPChainData` | **변경 없음 (로직)** | ✅ 불필요 |

---

## 3. Quick Mode UX 단순화 전략

### 3.1 현재 Quick Mode 흐름 (복잡)

```
/dna-lab?master=velvet&mode=quick
    ↓
DNALabOnboarding (조건부 스킵)
    ↓
DNALabOverview (2x2 그리드)
    ↓
UnifiedWorkflowShell (step=analysis)
    ↓
UnifiedAnalysisPanel (복잡한 사이드바)
```

### 3.2 제안: Quick Mode 전용 컴포넌트

```
/dna-lab?master=velvet&mode=quick
    ↓
┌─────────────────────────────────────────────────────────────┐
│  DNALabQuickStart (새 컴포넌트)                              │
│  ├── V7 시네마틱 레이아웃                                    │
│  ├── Master 프로필 카드                                      │
│  ├── Video URL 입력 (선택)                                   │
│  ├── "Start Analysis" CTA (50 credits)                      │
│  └── 3-Step 인디케이터 (하단)                                │
└─────────────────────────────────────────────────────────────┘
    ↓ (CTA 클릭)
기존 UnifiedWorkflowShell로 라우팅 (step=analysis)
```

### 3.3 조건부 렌더링 로직 수정

```typescript
// 현재 page.tsx 로직
if (!step && !ipSlug && !hasSession && !manuallyDismissed) {
  return <DNALabOnboarding />;
}

// 제안: Quick Mode 분기 추가
if (mode === "quick" && masterKey && !step) {
  return <DNALabQuickStart masterKey={masterKey} />;
}
```

---

## 4. 사전 작업 체크리스트

### Phase 0: 준비 (1일)

- [ ] **디자인 토큰 추출**: V7에서 사용된 색상, 스페이싱, 타이포 정리
- [ ] **Tailwind 설정 확장**: `aurora-dark`, `neon` 등 커스텀 클래스 추가
- [ ] **아이콘 통일**: Material Symbols Outlined 사용 확인
- [ ] **폰트 설정**: Inter + Noto Sans KR 로드 확인

### Phase 1: 컴포넌트 분리 (2일)

- [ ] **DNALabQuickStart.tsx 생성**: V7 기반 Quick Mode 전용 컴포넌트
- [ ] **DNALabProgressStepper.tsx 리팩터링**: 디자인별 변형 지원
- [ ] **AuroraBackground.tsx 추출**: 재사용 가능한 배경 컴포넌트

### Phase 2: 로직 보존 검증 (1일)

- [ ] **Chain Data 흐름 테스트**: 기존 흐름 유지 확인
- [ ] **URL 파라미터 호환성**: master, mode, step, ip 모두 작동
- [ ] **Session 복원 테스트**: localStorage 키 호환성
- [ ] **Credit 차감 테스트**: API 연동 정상 작동

### Phase 3: 통합 (2일)

- [ ] **page.tsx 수정**: Quick Mode 분기 추가
- [ ] **기존 컴포넌트와 공존**: Overview, WorkflowShell 유지
- [ ] **반응형 테스트**: 모바일/태블릿/데스크톱
- [ ] **다크 모드 기본 설정**: `class="dark"` 기본 적용

---

## 5. 핵심 로직 보존 영역 (건드리지 말 것)

### 5.1 절대 수정 금지

```typescript
// 1. Chain Data Context
useDimensionChainOptional()
chain.setChainData(...)
chain.getInputData(...)

// 2. DNA Lab Hooks
useDNALabWorkflow()     // 단계 상태 관리
useDNALabPipeline()     // 파이프라인 실행
useIPChainData()        // IP 데이터 로딩

// 3. API 연동
/api/dimension/vpe/...
/api/dimension/ad/...
/api/dna-lab/run-pipeline

// 4. Session Storage 키
"dna-lab-session-*"
"chain-data-dna-lab-*"
```

### 5.2 UI만 교체 (로직 유지)

```typescript
// 변경 전
<DNALabOnboarding
  onSelectIP={handleSelectIP}
  onQuickStart={handleQuickStart}
/>

// 변경 후 (V7 스타일)
<DNALabQuickStart
  masterKey={masterKey}
  onStart={handleQuickStart}  // 동일한 핸들러
/>
```

---

## 6. 파일별 변경 계획

### 6.1 새로 생성할 파일

| 파일 | 용도 | 기반 디자인 |
|------|------|------------|
| `DNALabQuickStart.tsx` | Quick Mode 전용 UI | V7 |
| `AuroraBackground.tsx` | 배경 효과 컴포넌트 | V7 |
| `MinimalStepper.tsx` | 3-dot 스테퍼 | V5/V7 |
| `MasterProfileCard.tsx` | Master 프로필 표시 | V5/V7 |

### 6.2 수정할 파일

| 파일 | 변경 내용 | 영향도 |
|------|----------|-------|
| `page.tsx` | Quick Mode 분기 추가 | 🟡 중간 |
| `globals.css` | Aurora, neon 토큰 추가 | 🟢 낮음 |
| `tailwind.config.ts` | 커스텀 클래스 확장 | 🟢 낮음 |

### 6.3 유지할 파일 (변경 없음)

| 파일 | 이유 |
|------|------|
| `useDNALabWorkflow.ts` | 핵심 로직 |
| `useDNALabPipeline.ts` | 파이프라인 로직 |
| `useIPChainData.ts` | 데이터 로딩 로직 |
| `constants.ts` | 단계 정의 |
| `UnifiedWorkflowShell.tsx` | Full Workflow용 |
| `UnifiedAnalysisPanel.tsx` | 분석 패널 로직 |

---

## 7. 테스트 시나리오

### 7.1 Quick Mode 테스트

```bash
# 1. Quick Mode 진입
GET /dna-lab?master=velvet&mode=quick
→ DNALabQuickStart 렌더링 확인
→ Velvet 프로필 표시 확인
→ "50 credits" 표시 확인

# 2. 분석 시작
Click "통합분석 시작하기"
→ /dna-lab?step=analysis&master=velvet 라우팅
→ UnifiedAnalysisPanel 정상 로드
→ Credit 차감 정상

# 3. Chain Data 흐름
분석 완료 후
→ chain.chainData["analysis"] 저장 확인
→ 다음 단계(mirror)에서 데이터 주입 확인
```

### 7.2 기존 흐름 호환성 테스트

```bash
# 1. IP 선택 흐름
GET /dna-lab?ip=bong-joon-ho
→ 기존 Overview 또는 WorkflowShell 렌더링

# 2. URL 직접 진입
GET /dna-lab?step=mirror&ip=bong-joon-ho
→ MissingDataBanner 정상 표시
→ AI 추론값 제안 정상

# 3. Pipeline 실행
Click "전체 파이프라인 실행"
→ 모든 단계 순차 실행
→ 결과 Chain에 저장
```

---

## 8. 위험 요소 및 대응

### 8.1 위험 요소

| 위험 | 영향 | 대응 |
|------|------|------|
| Chain Data 키 불일치 | 데이터 손실 | 기존 키 매핑 유지 |
| URL 파라미터 변경 | 기존 링크 깨짐 | 파라미터 추가만, 삭제 금지 |
| Session 키 변경 | 세션 복원 실패 | 기존 키 유지 |
| Credit API 변경 | 결제 오류 | API 레이어 변경 금지 |

### 8.2 롤백 계획

```typescript
// Feature Flag 사용
const USE_NEW_QUICK_MODE = process.env.NEXT_PUBLIC_NEW_QUICK_MODE === "true";

// 조건부 렌더링
if (mode === "quick" && masterKey && USE_NEW_QUICK_MODE) {
  return <DNALabQuickStart />;
}

// 기존 흐름 유지
return <DNALabOnboarding />;
```

---

## 9. 타임라인 (예상)

| Phase | 작업 | 기간 | 담당 |
|-------|------|------|------|
| 0 | 디자인 토큰 추출 + 설정 | 0.5일 | Frontend |
| 1 | DNALabQuickStart 컴포넌트 생성 | 1일 | Frontend |
| 2 | Aurora + Stepper 컴포넌트 추출 | 0.5일 | Frontend |
| 3 | page.tsx 분기 로직 추가 | 0.5일 | Frontend |
| 4 | 로직 보존 테스트 | 1일 | QA |
| 5 | 반응형 + 다크모드 테스트 | 0.5일 | Frontend |
| **Total** | | **4일** | |

---

## 10. 결론 및 권장사항

### 10.1 권장 접근법

1. **V7을 Quick Mode 기본으로 채택**
   - 시네마틱 Aurora 배경
   - Master 프로필 강조
   - 심플한 CTA

2. **기존 WorkflowShell은 유지**
   - Full Workflow용
   - 사이드바 기반 상세 설정

3. **로직 레이어 절대 보존**
   - Hooks, Context, API 연동 변경 금지
   - UI 컴포넌트만 교체/추가

### 10.2 즉시 실행 가능한 첫 단계

```bash
# 1. V7 디자인 토큰 추출
# 2. DNALabQuickStart.tsx 스켈레톤 생성
# 3. Feature Flag 설정
# 4. 기존 테스트 통과 확인
```

---

**Document Version**: 1.0
**Author**: Claude Code
**Status**: Ready for Review
