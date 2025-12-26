# Template System Spec (CODEX v23)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering  
**목표**: 템플릿의 유형, 구조, 수명주기, 학습 루프를 정식 규격으로 정의

---

## 0) 핵심 원칙

- **템플릿은 1급 객체**이며 공유/버전/학습 대상이다.
- **캡슐 노드만 핵심 로직을 보유**하고, 템플릿은 Public Graph로만 구성된다.
- NotebookLM/Opal/DB SoR 역할 정의는 `10_PIPELINES_AND_USER_FLOWS.md`를 따른다.
- 템플릿의 재현성은 `capsule_id@version` + `patternVersion`으로 고정된다.

---

## 1) 템플릿 유형 (Type System)

1. **Auteur Template**
   - 거장/장르 클러스터 노트북 기반
   - 기본 그래프: `Input → Auteur Capsule → Script/Beat → Storyboard → Output`

2. **Creator Self-Style Template**
   - 개인 노트북(자기 작품/레퍼런스) 기반
   - 자기 색깔을 캡슐로 고정하고 입력만 조정 가능

3. **Synapse Template**
   - A+B+D→C 변환 규칙(시냅스 로직)을 캡슐로 패키징
   - 스타일 전이/오마주 시뮬레이션에 최적

4. **Pipeline Template (PD/Writer)**
   - 시나리오/비트시트/스토리보드 흐름을 캡슐+프로세싱 노드로 구성

5. **Production Template (AI Video)**
   - Shot List → Storyboard → Prompt Contract → Gen Run 흐름을 캡슐로 고정
   - Veo/Kling 기반 샷 단위 생성에 최적화
   - 상세 규격: `29_AI_PRODUCTION_PIPELINE_CODEX.md`

6. **Hybrid Template**
   - Auteur + Creator + Synapse를 조합

---

## 2) 템플릿 구성 요소 (Canonical Structure)

- **Graph**: nodes + edges (Public Graph only)
- **Graph Meta**: `graph_data.meta`에 guide_sources / narrative_seeds / evidence_refs 보관
- **Capsule Instances**: capsuleId + capsuleVersion + params
- **Pattern Snapshot**: patternVersion
- **Guide Sources**: notebook_id, guide_type (summary/homage/variation/persona/synapse)
- **Narrative Seeds**: story_beats / storyboard_cards (guide_type=story/beat_sheet/storyboard)
- **Production Contract**: shot_contracts / prompt_contract_version / storyboard_refs
- **UI Metadata**: title, tagline, preview_video_url, badges

```json
{
  "template_id": "tmpl-auteur-bong",
  "title": "Structural Tension",
  "graph": { "nodes": [], "edges": [] },
  "graph_meta": {
    "guide_sources": [{ "notebook_id": "nlb-bong-99", "guide_types": ["homage", "storyboard"] }],
    "narrative_seeds": { "story_beats": [], "storyboard_cards": [] },
    "production_contract": {
      "shot_contracts": [],
      "prompt_contracts": [],
      "prompt_contract_version": "v1",
      "storyboard_refs": []
    },
    "evidence_refs": ["sheet:VIVID_DERIVED_INSIGHTS:42"]
  },
  "capsules": [
    {
      "capsule_id": "auteur.bong-joon-ho",
      "capsule_version": "1.2.0",
      "params": { "style_intensity": 0.7 }
    }
  ],
  "pattern_version": "v3",
  "guide_sources": {
    "notebook_ids": ["nlb-bong-99"],
    "guide_type": "homage"
  },
  "metadata": {
    "tagline": "Precise blocking with sudden genre shifts",
    "preview_video_url": "https://...",
    "badges": ["New", "Verified"]
  }
}
```

---

## 3) 통 데이터셋 레벨 ↔ 템플릿 매핑

- **Lv.1 Raw Visual Set** → Look/Palette 템플릿
- **Lv.2 Persona Set** → Persona 기반 Auteur/Creator 템플릿
- **Lv.3 Pure Homage Logic** → Synapse Template (강제 변환)
- **Lv.4 Reference Mixing** → “A + D” 시뮬레이션 템플릿
- **Lv.5 Synapse Complete** → 자동 변주/학습형 마스터 템플릿

---

## 4) 템플릿 수명주기

1. **Seed**: NotebookLM/Opal 출력 기반 초기 템플릿 생성
2. **Validate**: 캡슐 스펙 + 패턴 근거 검수
3. **Publish**: 공개/비공개 설정 후 캔버스 노출
4. **Learn**: GA/RL로 파라미터 개선
5. **Promote**: evidence 기준 충족 시 버전 승격

---

## 5) 학습/버전 정책

- `template_version`은 **증거 기준 통과 시에만 증가**
- `capsule_version`은 **고정**, 내부 체인 변경 시 새 버전 생성
- `patternVersion`은 패턴 승격 스냅샷을 의미
- 학습 로그는 `template_id + version + evidence_refs`로 추적

---

## 6) UI/UX 규칙

- 메인 진입은 **Template Card** 우선
- 카드에는 `preview_video_url`, `tagline`, `badge` 표시
- 템플릿 선택 → 즉시 캔버스 시드 그래프 생성

---

## 7) 보안/권한

- 템플릿은 **Public Graph만 공유**
- Private Subgraph/Prompt는 서버 전용
- 고가치 템플릿은 `admin_only` 옵션 지원

---

## 8) 연동 문서

- `06_TEMPLATE_CATALOG.md`
- `05_CAPSULE_NODE_SPEC.md`
- `10_PIPELINES_AND_USER_FLOWS.md`
- `12_PATTERN_PROMOTION_CRITERIA_V1.md`
- `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- `29_AI_PRODUCTION_PIPELINE_CODEX.md`
