# Fusion Notebook Protocol (CODEX v34)

**작성**: 2025-12-26  
**대상**: Product / Design / Engineering  
**목표**: NotebookLM 2‑Depth(재노트북) 운용을 **안전한 가드레일**로 정의한다.

---

## 0) Canonical Anchors

- 철학/원칙: `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- 흐름/역할: `10_PIPELINES_AND_USER_FLOWS.md`
- Source Pack/Prompt: `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`
- Claim/Evidence/Trace: `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`
- 승격 규칙: `11_DB_PROMOTION_RULES_V1.md`
- 승격 기준: `12_PATTERN_PROMOTION_CRITERIA_V1.md`

---

## 1) Definition

**Fusion Notebook** = NotebookLM이 **승격된 패턴/페르소나**를 다시 묶어  
**하이브리드 변주 가이드**를 생성하는 **2‑Depth 노트북**.

> 목표는 “증명된 DNA의 조합”이며,  
> **새 증거 없는 규칙의 자동 승격**은 금지한다.

---

## 2) Why It Matters (Value)

- 서로 다른 거장/장르의 **검증된 로직**을 안전하게 결합
- 템플릿 아이디어/변주 폭을 확장
- RL/실험을 통해 **성과 기반 하이브리드 캡슐**로 승격 가능

---

## 3) Guardrails (Non‑negotiable)

1. **Input 제한**: only `promoted` Pattern/Persona (candidate 금지)  
2. **Evidence 고정**: evidenceRefs는 반드시 **원본 DB SoR**로 연결  
3. **승격 금지**: Fusion 결과는 **바로 SoR 승격 불가**  
4. **범위 제한**: 최대 2~3 cluster만 결합  
5. **Phase 유지**: `cluster_id + temporal_phase` 단위 유지  
6. **증명 루프 필수**: 실험/성과 로그 없이는 캡슐 승격 불가

---

## 4) Input Contract (Fusion Source Pack)

**Allowed inputs**
- `pattern_ids[]` (promoted only)
- `persona_ids[]` (promoted only)
- `evidence_refs[]` (db only)
- `temporal_phase`
- `cluster_ids[]` (max 3)

**Forbidden**
- candidate outputs
- raw NotebookLM summaries without evidence
- `sheet:` refs without DB 승격

---

## 5) Output Contract (Fusion Guide)

Fusion 결과는 **가이드 전용**이며, 템플릿 후보로만 사용한다.

```json
{
  "output_spec": "FUSION_GUIDE_V1",
  "fusion_id": "fusion_CL_A12_CL_B07_hook_v1",
  "temporal_phase": "HOOK",
  "logic_blend": ["pattern_A", "pattern_B"],
  "persona_blend": ["persona_A", "persona_B"],
  "variation_rules": ["..."],
  "params_proposal": [{ "key": "pace", "range": [0,1] }],
  "template_fit_notes": ["..."],
  "claims": [{ "claim_id": "c1", "evidence_refs": ["db:shot_102"] }]
}
```

---

## 6) Promotion Policy (Fusion → Capsule)

Fusion 가이드는 **즉시 캡슐 승격 금지**.

승격 조건:
1. **실험 성과 로그** 확보 (Evidence Loop)
2. **Pattern Trace**에 기록
3. **RL/GA 추천**에서 반복적으로 상위권
4. **Claim/Evidence Gate** 통과

모든 조건 통과 시에만 **새 Capsule Version** 생성 가능.

---

## 7) Suggested Rollout

1. **1개 Fusion Notebook**으로 시작 (2 cluster, 1 phase)
2. Fusion Guide → 템플릿 후보 생성
3. 사용자 실행/성과 로그 수집
4. 성과가 명확하면 Capsule 승격

---

## 8) Inference Safety

- Fusion 결과는 **guide 레이어**로만 반환
- 내부 체인/프롬프트는 server‑side only
- UI에는 **요약 + 근거수**만 노출

---

## 9) Integration Points

- Source pack 규칙: `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`
- Evidence gate: `32_CLAIM_EVIDENCE_TRACE_SPEC_V1.md`
- 승격: `11_DB_PROMOTION_RULES_V1.md`
