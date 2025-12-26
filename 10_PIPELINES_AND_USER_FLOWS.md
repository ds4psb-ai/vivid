# Pipelines & User Flows (2025-12)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering  
**목표**: 데이터화 파이프라인과 캔버스 사용자 흐름을 한 장으로 정리

---

## 0) Canonical Scope

이 문서는 **흐름/역할의 단일 기준**입니다.  
다른 문서는 이 내용을 반복하지 않고 링크로 참조합니다.
원칙/철학은 `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`에서 고정한다.
E2E 상세 파이프라인은 `27_AUTEUR_PIPELINE_E2E_CODEX.md`를 참조한다.
프로덕션(샷 생성/후반) 상세는 `29_AI_PRODUCTION_PIPELINE_CODEX.md`를 참조한다.

---

## 0.1 System Roles (Gemini / NotebookLM / Opal / DB SoR)

- **Gemini 3 Pro/Flash**: 영상 구조화(JSON Schema) 전용 엔진  
  - ASR + 샷/키프레임 기반의 **scene/shot schema** 생성  
  - 결과는 **DB SoR(Video Schema)**에 적재 (NotebookLM 소스는 DB 요약본)  
  - 상세 스펙: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- **NotebookLM**: 지식/가이드 레이어 (Light RAG)  
  - 거장/장르 **클러스터 노트북** 운영  
  - 요약/오마주/변주/템플릿 적합도 가이드 출력  
  - Persona/Synapse Logic은 guide_type=persona/synapse로 축적  
  - Studio 다중 출력(Video/Audio/Mind Map) + 출력 언어 선택은 가이드 강화에 사용  
  - 업로드 소스는 SoR가 아니며, 결과는 Sheets Bus → DB 승격 규칙을 따른다  
  - Ultra 구독 기준 다중 출력/대량 처리에 유리  
  - Mega-Notebook은 **발굴/집계/운영 레이어**로만 사용하며, 캡슐은 **phase-locked pack**에서만 승격  
  - 출력 규격: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
  - 소스팩/프롬프트 프로토콜: `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`
- **Opal**: 템플릿 시드 + 내부 워크플로 자동화  
  - 라벨링/QA/프롬프트 체인 도구화  
  - 캡슐 노드 내부 서브그래프로만 실행
- **Sheets Bus**: 운영/검수용 스테이징  
  - DB SoR가 **증명/학습의 정본**  
  - 승격 규칙: `11_DB_PROMOTION_RULES_V1.md`

---

## 1) Dataization Pipeline (Evidence Loop)

```
Admin Ingest
  → Preprocess (ASR/Shot/Keyframe)
  → Gemini Structured Output (Video Schema)
  → DB SoR (Video Schema)
  → (Optional) Mega-Notebook (Discovery/Ops)
  → NotebookLM Source Pack Builder (cluster_id + temporal_phase)
  → NotebookLM/Opal (Guide)
  → Notebook Library (Private)
  → Notebook Assets (Private)
  → Sheets Bus (Derived)
  → Review/Normalize
  → DB SoR (Pattern Library/Trace)
  → Capsule Spec Update
```

핵심 규칙:
- NotebookLM/Opal은 **요약/라벨**만 담당
- 원본 영상은 NotebookLM에 직접 넣지 않고 **구조화 데이터(DB SoR)**로 변환 후 사용
- Notebook Library는 **비공개 지식 베이스**이며 사용자에게 직접 노출하지 않음
- Notebook Assets는 **노트북이 참조하는 자산 링크**이며 관리자 전용
- NotebookLM은 **지식/가이드 레이어**로서 클러스터 요약, 오마주/변주 가이드, 템플릿 적합도 제안을 제공
- Mega-Notebook은 **발굴/집계/운영 전용**이며, 캡슐 승격은 **phase-locked pack**으로만 수행
- Persona/Profile 및 Synapse Logic은 **guide_type=persona/synapse**로 구분해 축적
- Story/Beat/Storyboard는 **guide_type=story/beat_sheet/storyboard**로 구분하고 `story_beats`/`storyboard_cards`에 저장
- DB에 승격되는 것은 **검증된 패턴**만
- `evidence_refs`는 `sheet:` 또는 `db:` 포맷만 허용 (서버에서 필터링)
- 모든 결과는 **source_id + prompt/model/version**로 추적
- 승격 기준은 `12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 2) Creator Pipeline (Canvas → Preview → Generate)

```
Template Card
  → Canvas Edit
  → Capsule Run (Streaming: queued/started/progress/completed)
  → GA/RL Recommend
  → Script/Storyboard Preview
  → Generate (Scene/Audio)
  → Export + Feedback
```

핵심 규칙:
- 캡슐 내부 체인은 숨김, 결과만 노출
- 프리뷰는 저비용, 최종 생성은 고품질
- 캡슐 실행은 WS/SSE 스트리밍으로 진행 상태와 부분 메시지를 전달

### 2.1 Production Pipeline (AI Video)

```
Beat Sheet
  → Shot List
  → Storyboard (Nano-banana Pro)
  → Prompt Contract (Shot Contract 기반)
  → Gen Run (Veo 3.1 / Kling)
  → Continuity QC
  → Edit / Sound / Color / Final Export
```

운영 규칙:
- **샷 단위 생성**이 기본이며, Scene/Sequence는 Shot을 묶어 구성
- 프롬프트는 **5~10개 묶음**으로 병렬 실행 후 선별
- **일관성 우선**이면 Image-to-Video, **역동성 우선**이면 Text-to-Video
- 상세 규격은 `29_AI_PRODUCTION_PIPELINE_CODEX.md`를 따른다

---

## 3) User Roles & Responsibilities

- **Admin/Curator**: 원본 수집, NotebookLM 실행, 승격 판단
- **Librarian**: Notebook Library 정리 및 소스 연결 관리
- **Creator (Self-Style)**: 개인 자료를 노트북으로 축적, 자기 색깔 가이드 생성
- **Creator**: 템플릿 선택, 캡슐 파라미터 조정, 프리뷰/생성
- **Reviewer**: 품질 평가, 재사용/승격 근거 제공
- **Ops**: Pipeline Ops 화면에서 상태/Sheets 동기화/쿼런틴/패턴 승격/템플릿 시드/실행 로그 점검

---

## 4) Event Boundaries (확장 시점)

- `ingest.raw` → `derive.summary` → `promote.pattern`
- `capsule.run` → `capsule.stream` → `preview.generate` → `final.generate`
- `capsule.cancel` → `run.cancelled` (사용자 중단)
- 모든 이벤트는 trace_id로 연결
