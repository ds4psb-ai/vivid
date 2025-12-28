# PDR: Crebit Node Canvas (2025-12)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering  
**목표**: PD/작가/창작자에게 최고 가치를 제공하는 캔버스 제품 요구사항 정리

---

## 0) 목적

- 거장/명작/자기 자신 스타일을 **NotebookLM 가이드 레이어**로 통일하고,
- **DB SoR + Evidence Loop**로 재현 가능한 창작 규칙을 축적하며,
- 템플릿 기반 캔버스로 **빠른 기획 → 미리보기 → 생성**을 실현한다.
- 역할/흐름 상세 정본: `10_PIPELINES_AND_USER_FLOWS.md`

---

## 1) 문제 정의

- 기존 생성형 도구는 “그럴듯하지만 영혼 없는 결과물” 문제를 해결하지 못함.
- PD/작가/창작자는 **이유가 설명되는 스타일**과 **반복 가능한 퀄리티**를 원함.

---

## 2) 사용자 세그먼트

1. **PD/작가/창작자 (Primary)**
   - 빠른 기획/변주/미리보기
2. **Admin/Curator (Secondary)**
   - 거장/명작/개인 데이터화
3. **Reviewer (Secondary)**
   - 품질 검증/승격
4. **Studio Operator (Secondary)**
   - 실행/배포/운영

---

## 3) 핵심 가치 제안

- **Template-first**: 카드 클릭 → 즉시 캔버스 시작
- **Sealed Capsule**: 핵심 로직은 보호하고, 커스터마이징은 허용
- **Evidence-driven**: 패턴/증거 기반으로 추천/학습
- **Synapse-ready**: Tong Dataset(Visual+Persona+Synapse) 기반 설명 가능

---

## 4) 핵심 사용자 흐름

세부 단계는 `10_PIPELINES_AND_USER_FLOWS.md`에 정본화한다.
요약 흐름:
- Creator: 템플릿 → 캡슐 실행 → 프리뷰 → 생성
- Admin: 수집 → 구조화 → NotebookLM 요약 → Sheets → DB 승격

---

## 5) 기능 요구사항 (MVP)

- 템플릿 카드 갤러리 + 1-클릭 캔버스 생성
- 캔버스 편집(노드/엣지/인스펙터)
- 캡슐 실행 (WS/SSE 스트리밍)
- 프리뷰 패널 (요약/팔레트/씬 힌트)
- NotebookLM 출력 → Sheets → DB 승격
- Evidence/Pattern 기반 추천(프로토타입)

---

## 6) 데이터/아키텍처 요구사항

- 역할 정의/증명 레이어: `10_PIPELINES_AND_USER_FLOWS.md`, `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- 영상 구조화 기준: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- **Tong Dataset**: Visual + Persona + Synapse 규칙 구조화
- **Capsule Spec**: input/output contract + version 고정
- **Observability**: token/latency/cost 기록

---

## 7) UX 요구사항

- Template-first IA
- Empty state: “Create First Canvas” CTA
- 캡슐 노드는 잠금/확장 불가
- 상태 피드백: queued/running/streaming/complete/cancelled
- 미리보기 결과는 요약 + 근거 링크만

---

## 8) 비기능 요구사항

- **보안**: raw prompt, notebook, subgraph 절대 노출 금지
- **재현성**: capsule_id@version + patternVersion 고정
- **성능**: 스트리밍 지연 < 1s, 초기 응답 < 3s 목표
- **운영**: Dev/QA/Prod 분리, 배포 전 품질 리그레션 체크

---

## 9) 범위 제외 (Non-goals)

- 실시간 협업 편집
- 공개 프롬프트/모델 선택 UI
- 원문 데이터 클라이언트 노출

---

## 10) 성공 지표 (KPI)

- 첫 캔버스 생성까지 시간 < 5분
- 템플릿 재사용률 > 30%
- 추천 채택률 > 40%
- 프리뷰 만족도 > 4.2/5

---

## 11) 리스크 & 대응

- **품질 변동** → Evidence 기반 승격 + 휴먼 검수
- **IP 유출** → Sealed Capsule + 요약 반환
- **비용 폭증** → 프리뷰/최종 모델 분리 + 캐시

---

## 12) 연동 문서

- `00_EXECUTIVE_SUMMARY_NODE_CANVAS.md`
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`
- `05_CAPSULE_NODE_SPEC.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`
