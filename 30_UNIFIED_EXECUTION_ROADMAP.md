# Crebit Execution Roadmap (통합본)

**작성**: 2025-12-30 (통합)  
**Updated**: 2026-01-01 (Agent Studio 반영)  
**통합 대상**: `03`, `07`, `19` 로드맵 문서  
**상태**: ACTIVE (현재 코드베이스 기준)

---

## 현재 구현 상태 (2025-12-30)

### ✅ 완료된 핵심 기능

| 영역 | 구현 내용 | 상태 |
|------|----------|------|
| **Flow (Train UI)** | 열차 워크플로우 UI (현재 mock 옵션) | ✅ |
| **Dimension Tools** | 프롬프트/스토리보드/이미지/레퍼런스 미니앱 | ✅ |
| **Agent Chat** | Chat-first UI, SSE 스트리밍, 아티팩트 프리뷰 (Audio Overview 우선) | ✅ |
| **Canvas (Legacy)** | ReactFlow 기반 UI (비노출) | ⚠️ |
| **Dimension Tools** | `/api/dimension/*` 기반 프롬프트/스토리보드/이미지/레퍼런스 실행 | ✅ |
| **Template** | 카탈로그, 버전 관리, 공개/비공개 | ✅ |
| **Credits** | 지갑, 원장, 구독/탑업/프로모 분리 | ✅ |
| **Affiliate** | 리퍼럴 추적, 리워드 지급 (legacy API, 미마운트) | ⚠️ |
| **Auth** | Google OAuth, 세션 관리 | ✅ |
| **Ingest** | Raw/Derive/Pattern 파이프라인 | ✅ |
| **VDG 2-Pass** | SemanticPass, VisualPass, Merger, DirectorCompiler | ✅ |
| **Story-First** | NarrativePanel, HookSelector, DNA Compliance, Metrics | ⚠️ (legacy UI) |
| **Analytics** | 이벤트 추적, 메트릭 집계 | ✅ |

### 🔄 진행 중 / 부분 구현

| 영역 | 내용 | 상태 |
|------|------|------|
| NotebookLM Adapter | 실제 API 연동 (현재 stub) | 🔄 |
| GA/RL 학습 | 프로토타입 존재, 실제 학습 루프 미완성 | 🔄 |
| Event-driven Queue | Redis/Arq 설계됨, 운영용 API는 `_deprecated` | 🔄 |
| Audio Coach | API 설계됨, 통합 진행 중 | 🔄 |
| Teaching Artifact Derivation | Teaching 도구 결과를 Storyboard/Shot List/Data Table로 파생 | 🔄 |

---

## 단기 로드맵 (1~4주)

### Week 1-2: Story-First 완성 (legacy UI)
- [ ] `MetricsDashboard` 백엔드 API 연결 (`/content-metrics`)
- [ ] `SequenceEditor` Canvas 통합 (legacy)
- [ ] `DNAComplianceViewer` 콜백 구현 (regenerateShot, applyAllSuggestions)

### Week 3-4: 안정화 및 최적화
- [ ] Capsule 실행 입력 계약 엄격 검증
- [ ] Evidence refs 필터링 강화
- [ ] 성능 최적화 (Preview < 500ms 목표)

---

## Known Issues (Non-blocking)

- Agent streaming 스레드가 중복 시작되는 코드가 존재 (SSE 중복 이벤트 가능성).
- Global Chokki Accordion은 legacy SSE 파서를 사용하여 `agent.*` 이벤트와 불일치.
- `aiofiles` 의존성이 명시되지 않아 서버 환경에 따라 import 실패 가능.
- Affiliate API 라우터가 `_deprecated`에만 존재하여 `/api/v1/affiliate/*` 호출이 404일 수 있음.

## 중기 로드맵 (1~3개월)

### Phase A: 학습 루프 활성화
- GA/RL 보상 함수 → Pattern Lift 연동
- 템플릿 자동 승격 규칙 적용
- 피드백 수집 → 학습 데이터 적재

### Phase B: 외부 어댑터 실연동
- NotebookLM Enterprise API 연결
- Gemini 3 Pro 구조화 출력 자동화
- Opal 워크플로 도구화

### Phase C: 이벤트 드리븐 전환
- Redis + Arq 워커 배포
- S3 업로드 → 자동 처리 파이프라인
- 장시간 작업 비동기화

---

## 장기 비전 (6~24개월)

### AI Shortform Studio
- Script → Storyboard → Scene 자동 생성
- 샷 단위 Veo/Kling 연동
- 편집/컬러/사운드 자동화

### OTT 고도화
- 개인화 추천 엔진
- 멀티랭귀지 배포
- 라이선스/수익 정산

---

## 폐기된 계획 (현재 방향에 맞지 않음)

| 항목 | 사유 |
|------|------|
| Opal 미니앱 직접 제작 | NotebookLM 중심으로 전환 |
| Sheets Bus 중심 운영 | DB SoR로 완전 전환 완료 |
| 단순 템플릿 마켓플레이스 | Story-First DNA 중심으로 전환 |

---

## 정본 문서 참조

- 아키텍처: `15_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- 파이프라인: `08_PIPELINES_AND_USER_FLOWS.md`
- 캡슐 계약: `04_CAPSULE_NODE_SPEC.md`
- UI 가이드: `10_UI_DESIGN_GUIDE_2025-12.md`
