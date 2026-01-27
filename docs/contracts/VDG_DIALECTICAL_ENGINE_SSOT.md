# VDG 고도화 Single Source of Truth

> **Version**: 4.0 (Data-Verified)
> **Date**: 2026-01-13
> **Status**: 실제 데이터 검증 완료
> **Validation**: 3개 샘플 JSON 전수 검증 + 코드베이스 대조 + 컨설팅 리포트 정합성 확인

---

## Executive Summary

이 문서는 **실제 VDG 출력 데이터 3건을 전수 검증**한 결과를 기반으로 작성되었습니다.

**핵심 발견:**
1. **dopamine_radar**: 프롬프트에는 있으나 **실제 출력은 빈 객체 `{}`**
2. **viral_kicks**: 프롬프트에서 요구하나 **semantic에 빈 배열, 별도 테이블에 저장**
3. **audio**: `semantic.audio_engineering`은 비어있으나, `implementation_layer.audio_engineering`에 **BPM/beat 데이터 존재**
4. **vdg_quality_valid**: 3건 모두 **`false`** (remix_suggestions=0, keyframes=0)

**결론**: 현재 상태로 크롤링 본격 시작은 **불가**. P0 품질 수정 후 재검증 필요.

---

## Part 0: Operational Utilities (Code-backed)

> 이 문서는 **고도화 방향/갭 분석 SSoT**이며, 파이프라인 아키텍처는 `docs/02_VDG.md`에 정리되어 있습니다.

**운영/백필 유틸리티**
- `backend/scripts/audit_vdg_quality.py`: Pass1/2/3 + 패턴 연동 품질 감사
- `backend/scripts/report_comment_evidence_alignment.py`: VDG ↔ DB 정합성 리포트
- `backend/scripts/backfill_viral_kicks_and_comments.py`: ViralKick/CommentEvidence 백필
- `backend/scripts/backfill_hook_attributes.py`: Hook 3축 백필
- `backend/scripts/backfill_replicability_score.py`: R-Score 백필
- `backend/scripts/backfill_dopamine_radar.py`: dopamine_radar heuristic 백필
- `backend/scripts/cleanup_vdg_nodes.py`: 특정 노드 클린업 (재분석 전 정리)
- `backend/scripts/normalize_canonical_urls.py`: 플랫폼 URL 정규화 백필
- `backend/scripts/refresh_materialized_views.py`: MV 최신화

---

## Part 1: 실제 데이터 검증 결과 (3건 전수 분석)

### 1.1 샘플 데이터 개요

| Video | Title | View Count | Hook Type | Quality Score | Valid |
|:------|:------|:-----------|:----------|:--------------|:------|
| video_1 | Emotional Damage | 1.7M | contrast | 0.70 | **false** |
| video_2 | #fyp #ai retail | 5.2M | pov | 0.64 | **false** |
| video_3 | 욕쟁이할머니 돼지국밥 | 1.1M | contrast | 0.64 | **false** |

### 1.2 필드별 상태 (3건 공통)

#### 정상 작동 (데이터 존재)

| 필드 | 상태 | 위치 |
|:-----|:----:|:-----|
| `hook_genome.pattern` | ✅ | semantic.hook_genome |
| `hook_genome.delivery` | ✅ | semantic.hook_genome |
| `hook_genome.strength` | ✅ | 0.85~0.95 |
| `hook_genome.microbeats` | ✅ | 4~5개 |
| `intent_layer.hook_trigger` | ✅ | curiosity_gap |
| `intent_layer.irony_analysis` | ✅ | setup/twist/gap_type |
| `scenes` | ✅ | 3~4개 씬 |
| `capsule_brief.shotlist` | ✅ | 3~4개 |
| `audience_reaction` | ✅ | 5 keys |
| `entity_tracks` | ✅ | 5~8개 (CV Pass) |
| **audio BPM** | ✅ | `implementation_layer.audio_engineering.bpm` |
| **beat_timestamps** | ✅ | `implementation_layer.audio_engineering.beat_timestamps_ms` (14~18개) |

#### 비어있음 (수정 필요)

| 필드 | 상태 | 원인 |
|:-----|:----:|:-----|
| `dopamine_radar` | ❌ **빈 객체 `{}`** | Gemini가 프롬프트 무시 |
| `semantic.audio_engineering` | ❌ **null** | LLM이 출력 안 함 |
| `semantic.viral_kicks` | ❌ **빈 배열** | 별도 테이블 저장, semantic엔 없음 |

### 1.3 품질 이슈 (3건 공통)

```
CRITICAL 이슈:
❌ remix_suggestions 0개 < 최소 2개
❌ high_conf_kicks=0 < 2 required
❌ product_placement_guide 누락

WARNING 이슈:
⚠️ keyframes 총 0개 < 권장 4개
⚠️ focus_windows 0개 < 권장 4개
⚠️ microbeats 4개 < 권장 5개
⚠️ virality_analysis.curiosity_gap 누락
```

---

## Part 2: 컨설팅 리포트 vs 현재 상태

### 2.1 Antigravity 권고사항 대조

| 컨설팅 권고 | 현재 상태 | Gap |
|:-----------|:---------|:----|
| **Hook 3축 (Format/Trigger/Device)** | pattern + delivery 있음, **format 없음** | ⚠️ 부분 |
| **Audio-Visual Sync** | BPM/beats 있음, **beat_sync_score 없음** | ⚠️ 부분 |
| **R-Score (Replicability)** | 계산 함수 없음 | ❌ 없음 |
| **comment_bait_score** | 없음 | ❌ 없음 |
| **예측 vs 실제 RLHF** | 없음 | ❌ 없음 |

### 2.2 컨설팅 권고 (Antigravity)

**Phase 1 (1-2주)**: Hook 3축 매트릭스
```
Format (형식):  pov, skit, listicle, tutorial, challenge
Trigger (유발): curiosity_gap, shock, relatability, satisfaction
Device (장치):  text_on_screen, visual_hook, loud_noise, question
```

**Phase 2 (3-4주)**: Audio Intelligence
- Transcript-Visual Alignment
- Beat-Scene Sync Score
- Voice Tone Analysis

**Phase 3 (2개월)**: R-Score
```
R_Score = (Format_Rigidity × 0.4) + (Asset_Availability × 0.3) + (Skill_Threshold⁻¹ × 0.3)
```

---

## Part 3: Audio 데이터 현황 (정확한 상태)

### 3.1 Audio 데이터는 **존재함** (위치가 다를 뿐)

```python
# ❌ 이전 내 주장 (틀림)
"semantic.audio_engineering": null  # 여기엔 없음

# ✅ 실제 데이터 위치
"implementation_layer.audio_engineering": {
    "bpm": 135.99,
    "beat_timestamps_ms": [116, 557, 952, 1393, ...],  # 18개
    "onset_count": 36,
    "sync_points": [{"t_ms": 116, "event": "static_start", "beat_aligned": true}]
}
```

### 3.2 Audio 관련 올바른 조치

| 이전 내 주장 | 실제 필요한 조치 |
|:-----------|:---------------|
| "Audio 저장 경로 추가" (틀림) | **Beat-Visual Sync Score 계산 추가** |
| P0-1로 제안 (불필요) | P2로 이동, 신규 메트릭 계산만 필요 |

---

## Part 4: 로드맵 (마이그레이션 플랜 정렬)

> 기존 마이그레이션 플랜 (`moonlit-sauteeing-pixel.md`)과 정렬됨

### P0: 데이터 품질 수정 ✅ **구현 완료 (2026-01-13)**

**목표**: `vdg_quality_valid: true` 달성

#### P0-1: dopamine_radar 강제 출력 ✅

**구현 내역:**
- `unified_prompt.py:178-186`: CRITICAL 경고 + 차원별 설명 추가
- `unified_pass.py:280-320`: 빈 객체 fallback 휴리스틱 (경고 로그 포함)

```python
# 프롬프트 강화 (unified_prompt.py)
- **dopamine_radar** (REQUIRED - CRITICAL): Rate 0-10 for each dimension.
  * NEVER return empty object `{}` - this causes pipeline failure
  * You MUST provide ALL 5 dimensions with integer values 1-10

# Fallback (unified_pass.py)
if not dopamine_radar or dopamine_radar == {}:
    logger.warning("⚠️ dopamine_radar empty despite CRITICAL prompt - falling back")
    # 휴리스틱으로 5개 지표 계산
```

#### P0-2: viral_kicks 품질 개선 ✅

**구현 내역:**
- `unified_pass.py:509-536`: confidence 계산 로직 추가

```python
# 품질 기반 confidence 계산
conf_score = 0.5  # Base
if len(mechanism) > 50 and not placeholder: conf_score += 0.15  # 상세 mechanism
if title and not title.startswith('Kick '): conf_score += 0.10  # 상세 title
if ranks != [1]: conf_score += 0.15  # 실제 댓글 증거
if kf_desc not in placeholders: conf_score += 0.10  # 상세 keyframe
```

#### P0-3: remix_suggestions 생성 ✅

**구현 내역:**
- `vdg_v4.py:528-543`: `RemixSuggestionV4` 클래스 추가
- `vdg_v4.py:633-637`: VDGv4에 `remix_suggestions` 필드 추가
- `converter.py:120-188`: `_generate_remix_suggestions()` 함수

```python
# 자동 생성 (최소 2개)
remix_suggestions = _generate_remix_suggestions(llm, mise_signals, scenes)
# Sources: hook_genome.pattern → viral_element_to_keep
#          causal_reasoning.replication_recipe → concept
#          mise_en_scene_signals → variable_elements
```

**검증 결과:**
```
✅ VDG Quality: score=0.72, valid=True
✅ 777 tests passed
```

### P1: 3축 Hook + R-Score (1주)

> 마이그레이션 플랜 Phase 1 + Phase 3

#### P1-1: hook_attributes JSONB 추가

```python
# app/models/_all.py - OutlierItem
hook_attributes: Mapped[Optional[dict]] = mapped_column(
    JSONB, nullable=True, index=True
)
# {"format": "skit", "trigger": "shock", "device": "insert_clip"}
```

#### P1-2: extract_hook_attributes() 구현

```python
# app/utils/hook_type_extractor.py
def extract_hook_attributes(vdg_data: Dict) -> Dict[str, str]:
    """3축 Hook 속성 추출 (컨설팅 권고)"""
    normalized = normalize_vdg_schema(vdg_data)  # SSoT 사용
    hook_genome = normalized.get("hook_genome") or {}
    capsule = normalized.get("capsule_brief") or {}

    return {
        "format": _infer_format_from_shotlist(capsule.get("shotlist", [])),
        "trigger": hook_genome.get("pattern"),  # 기존 pattern → trigger
        "device": hook_genome.get("delivery"),  # 기존 delivery → device
    }
```

#### P1-3: R-Score 계산

```python
# app/services/replicability_scorer.py
def calculate_r_score(pattern_dna: Dict, cluster_stats: Dict) -> Tuple[float, str]:
    """
    R-Score 계산 (컨설팅 공식 기반, 실제 데이터 적응)

    입력: PatternDNA (DNAExtractor 결과), NOT raw VDG
    """
    mutation_slots = pattern_dna.get("mutation_slots", [])
    invariant_rules = pattern_dna.get("invariant_rules", [])
    member_count = cluster_stats.get("member_count", 1)
    success_rate = cluster_stats.get("success_rate", 0.5)

    score = (
        0.30 * (len(mutation_slots) / 10)           # 유연성
        + 0.25 * success_rate                        # 검증된 성공률
        + 0.25 * (1 - len(invariant_rules) / 15)    # 규칙 간결함
        + 0.20 * min(member_count / 10, 1.0)        # 샘플 신뢰도
    )

    tier = "EASY" if score >= 0.7 else "MODERATE" if score >= 0.4 else "HARD"
    return round(score, 2), tier
```

### P2: Audio-Visual Sync (2주)

#### P2-1: Beat-Scene Sync Score

```python
# app/services/vdg_2pass/beat_sync_analyzer.py
def calculate_beat_sync_score(
    beat_timestamps_ms: List[int],   # implementation_layer.audio_engineering에서
    scene_start_ms: List[int],       # scenes[].time_start에서
    tolerance_ms: int = 150
) -> float:
    """비트-씬 전환 동기화 점수"""
    if not beat_timestamps_ms or not scene_start_ms:
        return 0.0

    aligned = sum(
        1 for s in scene_start_ms
        if any(abs(s - b) <= tolerance_ms for b in beat_timestamps_ms)
    )
    return round(aligned / len(scene_start_ms), 2)
```

### P3: 고도화 (MVP 이후)

- comment_bait_score
- 예측 vs 실제 댓글 RLHF
- Voice Tone Analysis

---

## Part 5: normalize_vdg_schema SSoT

> **모든 VDG 읽기는 이 함수를 통해야 함**

```python
# app/services/vdg_schema_normalizer.py
from app.services.vdg_schema_normalizer import normalize_vdg_schema

# ❌ 절대 하지 말 것
hook = vdg_data.get("semantic", {}).get("hook_genome", {})

# ✅ 반드시 이렇게
normalized = normalize_vdg_schema(vdg_data)
hook = normalized.get("hook_genome") or {}
```

**지원 버전:**
- v3: `root.hook_genome`
- v4/v5: `semantic.hook_genome`
- experimental: `semantic_output.hook_genome`

---

## Part 6: 크롤링 시작 전 체크리스트

### 필수 조건 (P0 완료 후)

```bash
□ dopamine_radar가 빈 객체가 아님 (5개 필드 모두 값 있음)
□ vdg_quality_valid = true (최소 60% 이상의 신규 분석)
□ remix_suggestions >= 2
□ high_conf_kicks >= 2
□ 백필 스크립트로 기존 데이터 품질 업그레이드 완료
```

### 권장 조건 (P1 완료 후)

```bash
□ hook_attributes 3축 저장
□ R-Score 계산 및 tier 분류
□ 3개 샘플로 E2E 테스트 통과
```

### 검증 스크립트

```bash
# P0 검증
python -c "
from app.services.vdg_2pass.quality_gate import VDGQualityGate
# 최근 10개 분석 결과 품질 체크
"

# P1 검증
python scripts/audit_hook_attributes.py --sample 50
python scripts/audit_r_scores.py --sample 50
```

---

## Part 7: 이전 문서 오류 정정

| 이전 주장 (v3.1) | 실제 | 수정 |
|:----------------|:-----|:-----|
| "dopamine_radar IMPLEMENTED" | **빈 객체 `{}`** | P0-1로 수정 필요 |
| "P0-1: Audio 저장 누락" | `impl_layer.audio_engineering`에 **있음** | 삭제, P2로 sync score만 |
| "3축 Hook Taxonomy" | 문서에 없었음 | P1-1~2 추가 |
| "R-Score" | 문서에 없었음 | P1-3 추가 |
| "viral_kicks IMPLEMENTED" | semantic에 **빈 배열** | P0-2 품질 개선 |

---

## Part 8: 파일 참조

### 핵심 수정 대상

| 파일 | 변경 | 우선순위 |
|:-----|:-----|:--------:|
| `vdg_2pass/unified_pass.py` | dopamine_radar 후처리 | P0 |
| `vdg_2pass/quality_gate.py` | viral_kicks 품질 기준 | P0 |
| `vdg_pipeline/converter.py` | remix_suggestions 매핑 | P0 |
| `models/_all.py` | hook_attributes JSONB | P1 |
| `utils/hook_type_extractor.py` | 3축 추출 함수 | P1 |
| `services/replicability_scorer.py` | R-Score 계산 (신규) | P1 |
| `services/vdg_2pass/beat_sync_analyzer.py` | Sync score (신규) | P2 |

### 참조 문서

| 문서 | 역할 |
|:-----|:-----|
| `~/.claude/plans/moonlit-sauteeing-pixel.md` | 마이그레이션 플랜 (정렬됨) |
| `exports/vdg_consulting/VDG_CONSULTING_REPORT.md` | Antigravity 컨설팅 리포트 |
| `docs/02_VDG.md` | VDG 파이프라인 문서 |

---

## Part 9: 질문에 대한 답변

### Q: 이 로드맵대로 고도화 후 3개 데이터셋 재테스트하면 더 나은 결과 보장?

**A: "보장"은 아니지만 "높은 확률로 개선"**

개선 근거:
- dopamine_radar 채워지면 바이럴 요소 정량화 가능
- 3축 Hook으로 단일 라벨 정보 손실 해결 (컨설팅 지적)
- R-Score로 "따라할 수 있는" 패턴 필터링 가능

불확실성:
- Gemini의 프롬프트 준수 일관성 (dopamine_radar 빈 객체 문제)
- viral_kicks confidence 향상 여부

### Q: 크롤링/적재 준비 끝났나?

**A: 아니오. P0 완료 전까지 불가.**

현재 상태:
- `vdg_quality_valid: false` (3/3)
- `dopamine_radar: {}` (3/3)
- `remix_suggestions: 0` (3/3)
- `high_conf_kicks: 0` (3/3)

P0 완료 후 재검증 필수:
```bash
# 신규 분석 10건 이상에서
# vdg_quality_valid: true 비율 >= 70%
```

---

## Appendix A: 실제 데이터 구조 (video_3 샘플)

```json
{
  "outlier_item": {
    "hook_type": "contrast",
    "vdg_quality_score": 0.64,
    "vdg_quality_valid": false,
    "vdg_quality_issues": [
      "CRITICAL: remix_suggestions 0개 < 최소 2개",
      "product_placement_guide 누락",
      "WARNING: keyframes 총 0개 < 권장 4개"
    ]
  },
  "vdg_analysis": {
    "semantic": {
      "hook_genome": {
        "pattern": "expectation_vs_reality",  // ✅ 있음
        "delivery": "visual_gag",              // ✅ 있음
        "strength": 0.85                       // ✅ 있음
      },
      "intent_layer": {
        "hook_trigger": "curiosity_gap",       // ✅ 있음
        "dopamine_radar": {},                  // ❌ 비어있음!
        "irony_analysis": {                    // ✅ 있음
          "setup": "욕쟁이 할머니 식당...",
          "twist": "손님이 '신고할게요'로 응수",
          "gap_type": "expectation_subversion"
        }
      },
      "audio_engineering": null                // ❌ 비어있음
    },
    "implementation_layer": {
      "audio_engineering": {
        "bpm": 135.99,                         // ✅ 있음 (여기에!)
        "beat_timestamps_ms": [116, 557, ...]  // ✅ 있음 (여기에!)
      }
    }
  }
}
```

---

## Appendix B: P0 실행 순서

```bash
# Day 1 Morning
1. unified_pass.py에 dopamine_radar 후처리 추가
2. 테스트 영상 1개로 dopamine_radar 채워지는지 확인

# Day 1 Afternoon
3. converter.py에 remix_suggestions 매핑 추가
4. quality_gate.py viral_kicks 기준 조정 (필요시)

# Day 2
5. 3개 샘플로 재분석 실행
6. vdg_quality_valid: true 달성 확인
7. 백필 스크립트 작성 (기존 데이터 보정)

# 검증
pytest tests/test_vdg_quality.py -v
python scripts/audit_vdg_quality.py --sample 20
```

---

> **문서 끝**
>
> 이 문서는 실제 VDG 출력 데이터 3건을 직접 검증하여 작성되었습니다.
> 모든 "빈 필드" 주장은 `python3` 스크립트로 확인된 사실입니다.
> 이전 버전(v3.0, v3.1)의 오류가 Part 7에 명시되어 있습니다.
