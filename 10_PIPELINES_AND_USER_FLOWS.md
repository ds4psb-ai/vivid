# Pipelines & User Flows (2025-12)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering  
**목표**: 데이터화 파이프라인과 캔버스 사용자 흐름을 한 장으로 정리

---

## 1) Dataization Pipeline (Evidence Loop)

```
Admin Ingest
  → NotebookLM/Opal (Ultra)
  → Sheets Bus (Derived)
  → Review/Normalize
  → DB SoR (Pattern Library/Trace)
  → Capsule Spec Update
```

핵심 규칙:
- NotebookLM/Opal은 **요약/라벨**만 담당
- DB에 승격되는 것은 **검증된 패턴**만
- 모든 결과는 **source_id + prompt/model/version**로 추적
- 승격 기준은 `12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 2) Creator Pipeline (Canvas → Preview → Generate)

```
Template Card
  → Canvas Edit
  → Capsule Run (Summary + EvidenceRef)
  → GA/RL Recommend
  → Script/Storyboard Preview
  → Generate (Scene/Audio)
  → Export + Feedback
```

핵심 규칙:
- 캡슐 내부 체인은 숨김, 결과만 노출
- 프리뷰는 저비용, 최종 생성은 고품질

---

## 3) User Roles & Responsibilities

- **Admin/Curator**: 원본 수집, NotebookLM 실행, 승격 판단
- **Creator**: 템플릿 선택, 캡슐 파라미터 조정, 프리뷰/생성
- **Reviewer**: 품질 평가, 재사용/승격 근거 제공

---

## 4) Event Boundaries (확장 시점)

- `ingest.raw` → `derive.summary` → `promote.pattern`
- `capsule.run` → `preview.generate` → `final.generate`
- 모든 이벤트는 trace_id로 연결
