# Crebit Node Canvas: Executive Summary (Official)

<details open>
<summary>한국어</summary>

**작성**: 2025-12-24  
**Updated**: 2026-01-01 (Agent Studio 반영)  
**버전**: 정본 v1.1  
**대상**: CEO / 투자자 / 파트너  
**핵심**: Dimension Tools + Train Workflow + Agent Chat (Canvas는 레거시)

---

## 1) 3문장 비전

1. 거장 스타일의 창작 패턴을 도구/워크플로우로 모델링한다.  
2. 사용자는 **Flow(열차 UI)**에서 도구를 연결하고, 필요 시 캔버스는 내부/레거시 편집에 사용한다.  
3. GA/RL 최적화로 시간이 갈수록 더 좋은 결과를 자동 추천한다.

---

## 2) 무엇을 만드는가 (한 줄 정의)

**"채팅 + 열차 워크플로우로 도구를 연결하고, 캔버스는 내부/레거시로 보유하는 AI 콘텐츠 스튜디오"**

---

## 3) 최신 아키텍처 기준 핵심 구성

- **Notebook Library (Private)**: 거장/인기 작품 노트북을 비공개 지식 베이스로 축적
- **Data Ingestion & Evidence Loop**: 레퍼런스 수집 → 구조화(ASR/샷/키프레임) → 요약/라벨 → 검증/승격
- **Pattern Library/Trace**: 반복 패턴을 구조화해 증명 가능한 “공식”으로 관리
- **Tong Dataset (Synapse)**: Visual + Persona + 변환 규칙을 묶어 “거장 공식”을 설명 가능하게 저장
- **Dimension Tools**: 미니앱(프롬프트/스토리보드/이미지/레퍼런스)
- **Flow UI (Train)**: 열차형 워크플로우 편집/실행
- **Agent Chat (Chokki)**: 도구 호출 + 아티팩트 프리뷰 (SSE, Audio Overview 우선)
- **Canvas UI (Legacy)**: 노드/엣지 기반 편집 (현재 비노출)
- **Spec Engine**: 노드 계산 + 규칙 기반 조합 + 파이프라인 스냅샷
- **Optimization**: GA(조합 탐색) + RL/밴딧(피드백 학습)
- **Model Gateway**: 영상/이미지/음성/텍스트 모델을 통합 호출
- **Asset & Provenance**: 결과물 메타데이터, 버전/저작권 추적
- **Observability & Evaluation**: 실행 추적, 비용/지연, 품질 지표, 근거 링크
- **Event-driven Pipeline**: 수집/요약/생성 흐름을 비동기 이벤트로 분리
- **RAG/LLMOps 기준**: chunking/embedding/hybrid retrieval + 평가, 프롬프트/체인 버전 관리
- **Marketplace**: 템플릿 유통, 공유, 수익 쉐어

---

## 4) 핵심 사용자 플로우 (요약)

- **Flow**: 열차 워크플로우 생성 → 연결 고리 선택 → 순차 실행
- **Dimension**: 미니앱 선택 → 입력 → 실행
- **Agent Chat**: 채팅 입력 → 도구 실행 → 아티팩트 프리뷰 (Audio Overview 우선)
- **Canvas (Legacy)**: 내부/레거시 편집 및 참조
- 캡슐 노드는 **Sealed** (입·출력/노출 파라미터만 공개)
- 상세 파이프라인/역할은 `08_PIPELINES_AND_USER_FLOWS.md`에 정본화
- 영상 구조화(ASR/샷/키프레임 → Gemini) 기준은 `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md` 참고

---

## 5) Representative Auteur Templates (v1)

- 봉준호 (구조적 긴장, 장르 혼합)
- 박찬욱 (강한 미장센, 대칭 구도)
- 신카이 (감정 곡선, 빛/색감)
- 이준호 (음악 싱크, 리듬감)
- 나홍진 (서스펜스, 거친 리얼리즘)
- 홍상수 (미니멀 대화, 정적 연출)

---

## 6) NotebookLM / Google Opal 활용 전략 (요약)

- **Gemini 구조화 → DB SoR**가 영상 해석의 정본(NotebookLM은 요약/가이드만)
- **NotebookLM**: 지식/가이드 레이어 (클러스터 노트북, 오마주/변주, 템플릿 적합도)
- **Opal**: 템플릿 시드/QA 워크플로 자동화 (캡슐 내부 서브그래프)
- 상세 역할/규격은 `08_PIPELINES_AND_USER_FLOWS.md` 참고

---

## 7) MVP 범위 (필수 기능)

- Flow(Train) 워크플로우 생성/편집
- Dimension 미니앱 실행 (Prompt/Storyboard/Image/Reference)
- Agent Studio (Chat-first) + SSE 스트리밍
- 아티팩트 프리뷰 (Audio Overview + legacy Storyboard/Shot List/Data Table)
- 스펙 JSON 생성 및 저장
- 간단한 자동 계산(규칙 기반) + GA 프로토타입
- 템플릿 저장/공유(초기 공개/비공개)
- Canvas 편집은 legacy 경로에서만 유지

---

## 8) 확장 로드맵 요약

- **Phase 1 (0-3개월)**: Flow/Dimension MVP 완성
- **Phase 2 (3-6개월)**: GA/RL 최적화 + 템플릿 마켓
- **Phase 3 (6-12개월)**: AI 숏드라마/숏필름/숏애니 파이프라인
- **Phase 4 (12개월+)**: OTT급 개인화 추천/배포/수익화

---

## 9) 수익 모델 개요

- **SaaS 구독**: Free/Pro/Studio/Enterprise
- **템플릿 마켓**: 판매 수익 쉐어
- **API/프로덕션 서비스**: 모델 호출/렌더 비용 기반

---

## 10) 성공 지표 (초기)

- 평균 워크플로우 완성 시간 < 10분
- 추천 스펙 선택률 > 40%
- 템플릿 재사용률 > 25%
- 유료 전환율 > 5%

---

## 11) 결론

Crebit는 Flow/Agent Chat + 최적화 학습의 결합으로, **"창작 설계 시간을 최소화하고 결과 품질을 자동 개선하는"** 차세대 창작 스튜디오를 목표로 한다.

</details>

<details>
<summary>English</summary>

**Created**: 2025-12-24  
**Updated**: 2026-01-01 (Agent Studio reflected)  
**Version**: Canonical v1.1  
**Audience**: CEO / Investors / Partners  
**Core**: Dimension Tools + Train Workflow + Agent Chat (Canvas is legacy)

---

## 1) Three-Sentence Vision

1. Model auteur-style creative patterns as tools and workflows.  
2. Users connect tools in **Flow (train UI)**, and Canvas is reserved for internal/legacy editing when needed.  
3. GA/RL optimization automatically recommends better results over time.

---

## 2) What We Are Building (One-Line Definition)

**"An AI content studio that connects tools through chat + train workflows, while keeping Canvas for internal/legacy use."**

---

## 3) Core Components (Latest Architecture)

- **Notebook Library (Private)**: accumulate auteur/popular notebooks as a private knowledge base
- **Data Ingestion & Evidence Loop**: reference collection → structuring (ASR/shot/keyframe) → summary/label → verify/promote
- **Pattern Library/Trace**: manage repeatable patterns as provable "formulas"
- **Tong Dataset (Synapse)**: store Visual + Persona + transformation rules as explainable "auteur formulas"
- **Dimension Tools**: mini apps (prompt/storyboard/image/reference)
- **Flow UI (Train)**: train-style workflow editing/execution
- **Agent Chat (Chokki)**: tool calls + artifact previews (SSE, Audio Overview first)
- **Canvas UI (Legacy)**: node/edge editing (currently hidden)
- **Spec Engine**: node computation + rule-based composition + pipeline snapshots
- **Optimization**: GA (combinatorial search) + RL/bandit (feedback learning)
- **Model Gateway**: unified calls across video/image/audio/text models
- **Asset & Provenance**: output metadata, version/copyright tracking
- **Observability & Evaluation**: run tracing, cost/latency, quality metrics, evidence links
- **Event-driven Pipeline**: async separation of ingest/summary/generation flows
- **RAG/LLMOps baseline**: chunking/embedding/hybrid retrieval + evaluation, prompt/chain versioning
- **Marketplace**: template distribution, sharing, revenue share

---

## 4) Key User Flows (Summary)

- **Flow**: create train workflows → select connection links → run sequentially
- **Dimension**: select mini app → input → execute
- **Agent Chat**: chat input → tool execution → artifact preview (Audio Overview first)
- **Canvas (Legacy)**: internal/legacy editing and reference
- Capsule nodes are **Sealed** (only inputs/outputs/exposed params are public)
- Detailed pipelines/roles are canonized in `08_PIPELINES_AND_USER_FLOWS.md`
- Video structuring (ASR/shot/keyframe → Gemini) reference: `19_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`

---

## 5) 대표 거장 템플릿 (v1)

- Bong Joon-ho (structural tension, genre blending)
- Park Chan-wook (strong mise-en-scene, symmetrical framing)
- Shinkai (emotional arc, light/color)
- Lee Jun-ho (music sync, rhythmic pacing)
- Na Hong-jin (suspense, gritty realism)
- Hong Sang-soo (minimal dialogue, static staging)

---

## 6) NotebookLM / Google Opal Strategy (Summary)

- **Gemini structuring → DB SoR** is the canonical source for video understanding (NotebookLM is summary/guide only)
- **NotebookLM**: knowledge/guide layer (cluster notebooks, homage/variation, template fit)
- **Opal**: template seed and QA workflow automation (capsule-internal subgraph)
- See `08_PIPELINES_AND_USER_FLOWS.md` for detailed roles/specs

---

## 7) MVP Scope (Must-Haves)

- Flow (Train) workflow creation/editing
- Dimension mini-app execution (Prompt/Storyboard/Image/Reference)
- Agent Studio (chat-first) + SSE streaming
- Artifact previews (Audio Overview + legacy Storyboard/Shot List/Data Table)
- Spec JSON generation and storage
- Basic rule-based computation + GA prototype
- Template storage/sharing (initial public/private)
- Canvas editing remains only on legacy paths

---

## 8) Expansion Roadmap (Summary)

- **Phase 1 (0-3 months)**: Complete Flow/Dimension MVP
- **Phase 2 (3-6 months)**: GA/RL optimization + template marketplace
- **Phase 3 (6-12 months)**: AI short drama/short film/short animation pipelines
- **Phase 4 (12+ months)**: OTT-grade personalized recommendation/distribution/monetization

---

## 9) Revenue Model Overview

- **SaaS subscriptions**: Free/Pro/Studio/Enterprise
- **Template marketplace**: revenue share on sales
- **API/production services**: model call/rendering cost-based pricing

---

## 10) Success Metrics (Initial)

- Average workflow completion time < 10 minutes
- Recommended spec selection rate > 40%
- Template reuse rate > 25%
- Paid conversion rate > 5%

---

## 11) Conclusion

Crebit aims to become a next-generation creation studio that **"minimizes creative design time and automatically improves output quality"** by combining Flow/Agent Chat with optimization learning.

</details>
