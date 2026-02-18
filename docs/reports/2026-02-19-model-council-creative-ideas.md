# Model Council 창의적 활용 아이디어북

> **Date**: 2026-02-19
> **Author**: VIVID Tiger Team
> **Status**: Ideation — 자유 발상, 비용 제약 없음 (OpenClaw + Agent0 구독 토큰)
> **전제**: 타당성 보고서(`2026-02-19-model-council-feasibility-report.md`)의 P0 파이프라인 매핑은 이미 끝남. 이 문서는 **그 너머**를 탐색한다.

---

## 철학: Council은 "검증 레이어"가 아니다

타당성 보고서는 Council을 Pattern Atom 보완 / Gate B 강화 / continuity_score 3축 분리에 매핑했다. 이건 맞지만, **Council의 본질을 "검증 도구"로만 보면 창의적 가치의 20%만 쓰는 것**이다.

Council의 진짜 힘: **서로 다른 인지 모드를 가진 3개 엔티티가 동일한 대상을 동시에 바라볼 때, 어느 단일 엔티티도 생성할 수 없는 통찰이 교차점에서 발생한다.**

이하 11개 아이디어는 이 원칙을 파이프라인 바깥으로 확장한다.

---

## Idea 1: Director's Council — "거장이 당신의 씬을 본다면"

### 컨셉

3개 모델이 각각 **다른 영화감독의 페르소나를 입고** 사용자의 씬을 평가한다. "봉준호라면 이 씬을 어떻게 고쳤을까?" 가 실제 답변으로 나온다.

### 작동 방식

```
사용자 입력: 자신의 씬 (영상 / 스크립트 / 스토리보드)

┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Gemini 3 Pro  │  │   Opus 4.6    │  │   Codex 5.3   │
│               │  │               │  │               │
│ 봉준호 페르소나│  │ 히치콕 페르소나│  │ 쿠브릭 페르소나│
│               │  │               │  │               │
│ 공간/계급의   │  │ 서스펜스/     │  │ 대칭/원포인트 │
│ 수직 언어로   │  │ 관객 정보     │  │ 퍼스펙티브로  │
│ 재해석        │  │ 비대칭으로    │  │ 재해석         │
│               │  │ 재해석        │  │               │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        └──────────────────┼──────────────────┘
                           ▼
                  ┌─────────────────┐
                  │   Synthesizer   │
                  │                 │
                  │ "봉준호는 여기서 │
                  │  카메라를 내리고 │
                  │  히치콕은 올리고 │
                  │  쿠브릭은 고정"  │
                  │                 │
                  │ → 사용자가 선택  │
                  └─────────────────┘
```

### 왜 가치 있는가

- 사용자가 자기 씬의 **의도를 명확히 모를 때**, 3명의 거장이 각자 다른 방향을 제시하면 사용자가 "아, 나는 히치콕적 서스펜스를 원했구나"라고 깨닫게 됨
- Qdrant `pattern_atoms`에 감독별 패턴이 이미 축적되어 있으므로 RAG로 실제 레퍼런스 씬 연결 가능
- **VIVID 차별화**: "AI가 대신 만들어주는" 도구가 아니라 "거장에게 코칭받는" 경험

### 페르소나 라이브러리 확장

| Tier | 감독 | 특화 관점 | 모델 배치 |
|------|------|----------|----------|
| 동양 | 봉준호 | 공간/계급/블랙코미디 | Gemini (시각 분석 강점) |
| 동양 | 웡카위 | 색채/시간/불완전한 기억 | Opus (서사 감각) |
| 서양 | 히치콕 | 서스펜스/POV/관객 심리 | Opus (심리 분석 강점) |
| 서양 | 쿠브릭 | 대칭/원포인트/강박적 정밀함 | Codex (정량적 구도 분석) |
| 서양 | 핀처 | 어두운 톤/디테일/미장센 밀도 | Gemini (시각 밀도 파싱) |
| 실험 | 데니 빌뇌브 | 스케일/사운드스케이프/시간 팽창 | Opus (철학적 해석) |

---

## Idea 2: Adversarial Red Team — "이 씬은 절대 통과 못 합니다"

### 컨셉

Council을 **협력이 아닌 적대적 구조**로 배치한다. 한 모델이 "이 씬은 완벽하다"를 주장하고, 다른 모델이 "이 씬은 실패한다"를 주장하며, 세 번째가 판결한다.

### 작동 방식

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Advocate    │  │   Adversary   │  │    Judge     │
│  (Opus 4.6)  │  │  (Codex 5.3) │  │ (Gemini Pro) │
│              │  │              │  │              │
│ "이 편집이   │  │ "이 편집은   │  │ 양쪽 논거를  │
│  작동하는    │  │  실패하는    │  │ 시각 증거와  │
│  3가지 이유" │  │  3가지 이유" │  │ 대조하여     │
│              │  │              │  │ 판결"        │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └─────────────────┼─────────────────┘
                         ▼
              ┌───────────────────┐
              │ 판결문 + 개선안   │
              │                   │
              │ "Adversary가 지적 │
              │  한 3번째 이유가  │
              │  유효. 그러나     │
              │  1-2번은 Advocate │
              │  의 반론이 우세"  │
              └───────────────────┘
```

### 적용 지점

- **Gate B (Rights)에서의 프리플라이트 체크**: 퍼블리시 전에 "이 생성물이 왜 권리 침해가 아닌가"를 Advocate가 변론하고, "왜 권리 침해인가"를 Adversary가 공격. Judge가 최종 판결 → **Gate B를 단순 pass/fail에서 법적 논증 구조로 격상**
- **패턴 품질 게이트**: 새로운 Pattern Atom이 축적될 자격이 있는지를 적대적으로 검증
- **프롬프트 QC**: "이 프롬프트가 왜 좋은 영상을 만드는가" vs "이 프롬프트의 약점 3가지"

### 학술 근거

- **Tool-MAD** (arXiv 2601.04742, 2026-01): 도구 활용 기반 다중 에이전트 디베이트에서 기존 MAD 대비 **평균 18.1% 팩트 검증 정확도 향상, 최대 35.0%**. 핵심은 환각 감지량 자체가 아니라, 적대적 구조가 도구(검색/코드 실행)를 활용하여 주장을 실증적으로 검증하게 만든다는 점
- **A-HMAD** (ACL Findings 2025): 에이전트별 신뢰도 가중 debate → 표준 토론 대비 +4-6%

---

## Idea 3: Audience Simulation Council — "100명의 관객이 당신의 씬을 봤습니다"

### 컨셉

3개 모델이 각각 **다른 관객 페르소나**를 시뮬레이션하여, 씬에 대한 반응을 예측한다.

### 페르소나 설계

| 페르소나 | 모델 | 시뮬레이션 |
|---------|------|----------|
| **시네필** | Opus 4.6 | "이 레퍼런스는 타르코프스키의 거울 장면을 연상시킨다. 의도적인가?" |
| **일반 관객** | Gemini Pro | "이 장면에서 무슨 일이 일어나고 있는지 즉시 이해 가능한가?" |
| **숏폼 소비자** | Codex 5.3 | "3초 안에 후킹되는가? 스크롤 멈춤 확률은?" |

### 출력 형태

```json
{
  "scene_id": "user_scene_001",
  "audience_reactions": {
    "cinephile": {
      "engagement": 0.92,
      "reference_recognition": ["mirror_tarkovsky", "space_odyssey_jump_cut"],
      "critique": "의도적 롱테이크가 관객 인내심을 시험하지만, 보상이 충분하다",
      "share_probability": 0.35
    },
    "general": {
      "engagement": 0.61,
      "confusion_points": ["minute_1:23_motivation_unclear"],
      "emotional_response": "curious_but_detached",
      "completion_rate_estimate": 0.72
    },
    "shortform": {
      "hook_score": 0.44,
      "skip_probability": 0.68,
      "optimal_clip_points": ["0:03-0:07", "0:41-0:45"],
      "tiktok_virality_estimate": "low"
    }
  },
  "council_insight": "시네필에게는 강한 씬이지만 일반 관객 접근성이 낮음. 1:23 지점의 동기 명확화가 전체 관객 커버리지를 높일 핵심 레버"
}
```

### 왜 가치 있는가

- VIVID 사용자 대부분은 **자기가 만든 영상의 타겟 관객을 명확히 정의하지 못한다**
- 3개 관객 반응을 동시에 보여주면 "아, 이건 시네필용이지 숏폼용이 아니구나"를 깨닫게 됨
- `experiment_service.py`의 Thompson Sampling과 연계: 관객 시뮬레이션 결과를 실제 A/B 테스트 결과와 대조하여 시뮬레이션 정확도를 지속 보정

---

## Idea 4: Temporal Scale Council — 마이크로/메소/매크로

### 컨셉

동일한 편집 결정을 **3개의 시간 스케일**에서 동시에 평가한다. "이 컷이 좋은가?"라는 질문이 프레임 단위 / 씬 단위 / 영화 전체 단위에서 전혀 다른 답을 가질 수 있다.

### 3축

| 스케일 | 모델 | 관점 |
|--------|------|------|
| **Micro** (프레임/샷) | Gemini | "이 컷의 180도 룰이 지켜졌는가? 아이라인 매치는?" |
| **Meso** (씬/시퀀스) | Codex | "이 씬의 리듬이 전후 씬 대비 통계적으로 정상 범위인가?" |
| **Macro** (영화 전체) | Opus | "이 편집 결정이 전체 서사 아크에서 어떤 위치에 있고, 3막 전환을 지원하는가?" |

### 핵심 통찰

현재 `continuity_score`는 인접 샷 간 연속성만 본다. 하지만 진짜 편집의 품질은 **전체 구조에서 이 컷의 역할**까지 포함한다. 3축 동시 평가로:

- Micro에서 완벽하지만 Macro에서 실패하는 컷 감지 (예: 기술적으로 완벽한 match cut인데 서사 흐름을 끊는 경우)
- Macro에서 필요하지만 Micro에서 "규칙 위반"인 컷 허용 (예: 의도적 jump cut)

### 전제 조건: 데이터 축적

> **주의**: 시대별 영화 문법 데이터가 `pattern_atoms`에 충분히 축적되어야 Temporal Scale Council이 의미 있는 판단을 내릴 수 있다. SSOT §6.5.3의 Masterpiece ingestion v0(최소 1,000 클립)이 완료된 후에 시작해야 한다. 특히 Micro 축의 180도 룰/아이라인 매치 판단과 Macro 축의 서사 아크 판단 모두 코퍼스 통계가 뒷받침되지 않으면 모델의 일반 지식에만 의존하게 된다.

---

## Idea 5: Style Fusion Council — "봉준호 x 데니 빌뇌브"

### 컨셉

2명 이상의 감독 스타일을 **지정 비율로 혼합**한 새로운 패턴을 생성한다.

### 작동 방식

```
사용자 입력: "봉준호 60% + 데니 빌뇌브 40%로 서스펜스 씬"

┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│     Gemini         │  │      Opus          │  │      Codex         │
│                    │  │                    │  │                    │
│ 봉준호 패턴에서   │  │ 두 감독의 서사    │  │ 두 감독의 통계적  │
│ 시각 요소 추출    │  │ 원칙이 충돌하는   │  │ 샷 길이/앵글/     │
│ + 빌뇌브 패턴에서 │  │ 지점과 호환되는   │  │ 전환 분포를       │
│ 스케일 요소 추출  │  │ 지점을 판단       │  │ 가중 평균으로     │
│                    │  │                    │  │ 계산              │
└────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘
         └──────────────────────┼──────────────────────┘
                                ▼
                    ┌────────────────────┐
                    │  Fusion Pattern    │
                    │                    │
                    │ - 봉준호의 수직    │
                    │   공간 + 빌뇌브의  │
                    │   스케일 팽창      │
                    │ - 충돌점: 봉준호는 │
                    │   밀착, 빌뇌브는   │
                    │   초광각 → 해소:   │
                    │   "좁은 공간에서   │
                    │   시작하여 점진적  │
                    │   스케일 확장"     │
                    └────────────────────┘
```

### Qdrant 연계

- `pattern_atoms` 컬렉션에서 감독A/B 패턴을 각각 검색
- Council이 두 패턴 세트의 **교집합**(호환 요소)과 **충돌점**(비호환 요소)을 식별
- 충돌점에 대한 **해소 전략**을 생성 → 이것이 "새로운 패턴"이 됨

### 레이턴시 주의: 비동기 배치 실행 필수

> **SLO 경고**: Qdrant에서 감독A/B 패턴 각각 검색(2회) → Council 3모델 병렬 쿼리(1회, 내부 3 LLM 호출) → 충돌점 해소 전략 생성(Synthesizer 1회)까지 최소 **3-4 LLM 호출**이 필요하다. 추천 API p95 < 2.5s SLO(SSOT §12)에는 맞지 않는다.
>
> **해결**: Style Fusion은 실시간 API가 아닌 **Agent0 Worker를 통한 비동기 배치 작업**으로 분리한다. 사용자가 "봉준호 x 빌뇌브" 퓨전을 요청하면 Worker가 백그라운드에서 처리하고, 완료 시 알림 + 결과를 `pattern_atoms`에 적재한다. 이후 추천 시에는 사전 생성된 퓨전 패턴을 즉시 검색하므로 SLO를 지킨다.

### 왜 가치 있는가

- 지금까지 "스타일 참조"는 **하나의 감독만** 참조할 수 있었다
- 현실의 창작자는 "봉준호 같으면서도 빌뇌브의 스케일감이 있는" 같은 복합 요구를 한다
- 이것은 어떤 단일 모델도 혼자서 잘 해내기 어려운 태스크 — 서로 다른 관점(시각/서사/정량)이 충돌을 해소할 때 진짜 창의적 결과가 나온다

---

## Idea 6: Disagreement-as-Signal — Council 불일치를 데이터로

### 컨셉

Council에서 3모델이 **의견 불일치를 보인 지점**을 버리지 말고, **그 불일치 자체를 가치 있는 신호로** 활용한다.

### 활용 1: A/B 테스트 우선순위

```python
# 현재: experiment_service.py의 Thompson Sampling이 변종을 무작위 탐색
# 개선: Council 불일치가 큰 변종을 우선 테스트

def prioritize_experiment(council_results):
    disagreement = max(scores) - min(scores)
    if disagreement > 0.3:
        # 모델들이 크게 불일치 = 정보 가치가 높은 실험
        return ExperimentPriority.HIGH
    elif disagreement > 0.15:
        return ExperimentPriority.MEDIUM
    else:
        # 합의 = 이미 답이 나옴, 실험 불필요
        return ExperimentPriority.LOW
```

### 활용 2: 패턴 경계 발견

모델들이 불일치하는 패턴 = **아직 정의되지 않은 새로운 패턴 유형**일 가능성

```
예: Gemini는 "dolly_in"으로 분류, Opus는 "push_in"으로 분류, Codex는 "zoom_in"으로 분류

→ 불일치 자체가 "이 3개 기법의 경계가 모호한 영역이 존재한다"는 신호
→ 새로운 pattern_type "dolly_zoom_hybrid"의 발견으로 이어질 수 있음
→ VIVID의 패턴 어휘 자체가 Council을 통해 진화한다
```

### 활용 3: 사용자 교육 콘텐츠

"이 씬에 대해 AI들이 의견이 갈렸습니다" 라는 UI 표시 → 사용자가 왜 의견이 갈리는지 탐색하면 시네마틱 지식이 자연스럽게 습득됨

---

## Idea 7: Retrospective Council — 생성 후 되돌아보기

### 컨셉

영상 생성이 **끝난 후에** Council이 결과물을 보고 **"다음에는 이렇게 하면 더 좋겠다"를 학습 노트로** 남긴다.

### 작동 방식

```
1. 사용자가 Veo/Kling으로 영상 생성
2. 결과물을 Gemini가 분석 (step 3와 동일 파이프라인)
3. Council이 원래 프롬프트 vs 실제 결과의 gap을 분석

Gemini: "프롬프트에 dolly_in을 요청했으나 결과물은 zoom_in에 가깝다"
Opus:   "서사 의도(긴장 고조)는 달성되었으나, 물리적 카메라 움직임의 체감이 다르다"
Codex:  "Veo3에서 dolly_in과 zoom_in의 구분율은 34%. Kling에서는 71%"

Synthesizer → 학습 노트:
- "Veo3에서 dolly_in 의도 시: 'physical camera movement forward' 명시 필요"
- "Kling으로 엔진 전환 권장 (이 패턴에서 충실도 2.1배)"
```

### 축적 효과

이 학습 노트가 Qdrant에 축적되면:
- **엔진별 프롬프트 가이드라인**이 자동으로 생성된다
- "Veo는 이걸 잘하고, Kling은 저걸 잘한다"가 데이터로 증명된다
- `engine_constraint_schemas.py`가 실측 데이터로 지속 보정된다

---

## Idea 8: Council as Curriculum — 불일치에서 교육 콘텐츠 생성

### 컨셉

Council의 추론 과정 자체를 **시네마틱 교육 콘텐츠**로 포장한다.

### 예시: "왜 이 컷은 작동하는가?" 마이크로 레슨

```markdown
## 마이크로 레슨: Dolly-in to Close-Up

### 시각 분석 (Gemini)
프레임 분석 결과: MS → CU 전환, 3.2초, rule-of-thirds 좌측 배치

### 서사 해석 (Opus)
봉준호 <기생충>의 지하실 장면에서도 동일 기법 사용.
관객을 "물리적으로" 인물 내면에 가까이 끌어당기는 효과.
단순 zoom과 다른 점: dolly는 피사체와 배경의 관계가 변한다.
이것이 "공간 안에서의 위치 변화" 감각을 만든다.

### 데이터 근거 (Codex)
MovieNet 92K 태그 기준:
- dolly_in + CU 조합의 감정 고조 상관계수: r=0.73
- 최적 지속 시간: 2.4-4.0초 (p25-p75)
- 이 범위 밖: 관객 불편감 2.3배 증가

### 요약
3가지 관점이 합쳐져 하나의 기법이 "왜 작동하는가"를 완전히 설명한다.
```

### VIVID 프로덕트 연계

- **Academy 모듈**에서 "오늘의 마이크로 레슨" 피드로 활용
- Qdrant에 축적된 Pattern Atom 중 `confidence_tier: "high"` 패턴을 자동으로 레슨화
- 사용자가 특정 씬에서 "왜?"를 클릭하면 Council이 실시간으로 레슨 생성

---

## Idea 9: Negotiation Council — 경계선 판정

### 컨셉

`continuity_score`가 하드게이트 경계(0.60)에 걸리거나, `clone_risk`가 review 임계값(0.40) 근처일 때 — 단순 pass/fail 대신 **3모델이 협상**한다.

### 작동 방식

```
입력: continuity_score = 0.58 (하드게이트 0.60 미달)

Round 1 - 각 모델의 입장:
  Gemini: "시각 연속성 0.71 — 충분. 조명 변화가 있지만 의도적 시간 경과 표현"
  Opus:   "서사 연속성 0.42 — 불충분. 캐릭터 동기가 씬 전환에서 설명 없이 변한다"
  Codex:  "리듬 연속성 0.63 — 경계. 샷 길이 분포가 정상 범위의 p15"

Round 2 - 해소안 제시:
  Opus:   "0:43 지점에 1.5초 반응 샷 삽입하면 동기 전이가 해소됨"
  Codex:  "그 삽입으로 리듬이 p15 → p35로 개선됨"
  Gemini: "삽입 샷의 조명은 기존 톤과 호환 가능"

최종 판결:
  "현재 상태로는 하드게이트 미달이지만, 구체적 수정안(0:43 반응 샷 삽입)이 합의됨.
   수정 시 예상 continuity_score: 0.71. 수정안과 함께 사용자에게 제시."
```

### 왜 가치 있는가

- 현재: "점수 0.58이므로 탈락" → 사용자 좌절
- 개선: "점수 0.58이지만, **여기를 이렇게 고치면 통과**" → 사용자 학습 + 경험 향상
- 경계선 판정에서 가장 큰 가치가 생긴다 — 명확한 합격/불합격은 Council이 불필요

---

## Idea 10: Cross-Era Council — 시대를 넘나드는 평가

### 컨셉

동일한 씬을 **다른 시대의 영화 문법**으로 평가한다.

| 시대 | 모델 | 관점 |
|------|------|------|
| **클래식 할리우드** (1930-60) | Gemini | 연속 편집, 180도 룰, 아이라인 매치의 엄격 적용 |
| **뉴웨이브** (1960-80) | Opus | 점프컷, 비선형, 4th wall 파괴의 정당성 판단 |
| **현대 디지털** (2010-) | Codex | 원테이크 시뮬레이션, 드론 무브먼트, AI 생성 영상의 맥락 |

### 출력 예시

```
씬: 2인 대화, jump cut 3회

클래식: "편집 규칙 위반. 연속성 훼손."
뉴웨이브: "고다르적 정당성 있음. 인물의 심리적 불안정을 시각화."
현대: "숏폼 관객에게는 자연스러운 리듬. 3초 hook으로도 기능."

Council 통찰:
"이 편집은 클래식 기준으로는 실패하지만, 의도에 따라 뉴웨이브/현대 문법에서는 유효.
 타겟 플랫폼이 YouTube Shorts라면 현대 문법 적용이 적절."
```

### 가치

- **"규칙 위반"이 항상 실패가 아님**을 사용자에게 가르친다
- 플랫폼/타겟에 따라 **다른 기준이 적용되어야 함**을 Council이 자연스럽게 보여준다

### 전제 조건: 데이터 축적

> **주의**: Idea 4(Temporal Scale)와 동일한 데이터 갭이 존재한다. 시대별 영화 문법은 `pattern_atoms`에 해당 시대의 레퍼런스 클립이 충분히 축적되어야 의미 있는 비교가 가능하다. 특히 클래식 할리우드(1930-60)와 뉴웨이브(1960-80) 시대의 패턴은 현재 코퍼스에 없으므로, SSOT §6.5.3의 Masterpiece ingestion이 이 시대 클립을 포함하도록 계획해야 한다. 현재 우선순위 10번 배치는 이 전제를 반영한 것이다.

---

## Idea 11: Meta-Council — Council을 모니터하는 Council

### 컨셉

Council 세션 자체의 품질을 주기적으로 감사한다. "Council이 계속 제대로 작동하고 있는가?"

### 감사 항목

```python
class MetaCouncilAudit:
    def check_diversity(self, sessions: list[CouncilSession]) -> float:
        """3모델이 항상 같은 답을 내면 Council의 의미가 없다.
        diversity_score가 0.2 미만이면 역할 재설계 필요."""
        ...

    def check_bias_drift(self, sessions: list[CouncilSession]) -> dict:
        """특정 모델이 항상 소수의견이면 가중치 재조정 필요."""
        ...

    def check_synthesizer_quality(self, sessions: list[CouncilSession]) -> float:
        """Synthesizer가 실제로 3개 응답을 종합하고 있는가,
        아니면 하나만 복사하고 있는가?"""
        ...

    def correlate_with_outcomes(self, sessions: list[CouncilSession]) -> dict:
        """Council consensus_rate와 실제 사용자 만족도의 상관관계.
        합의가 높았는데 사용자 reject이면 Council 기준이 틀린 것."""
        ...
```

### 실행 주기

- Weekly: 지난 주 모든 Council 세션의 diversity, bias drift 체크
- Monthly: 실제 outcome과의 상관 분석 → 가중치/역할 자동 조정
- Quarterly: 역할 배치 자체를 재설계해야 하는지 판단

---

## 우선순위 매트릭스

| ID | 아이디어 | 구현 난이도 | 사용자 가치 | 기존 인프라 활용도 | **추천 순서** |
|----|----------|-----------|-----------|----------------|------------|
| 1 | Director's Council | 중간 | 극대 | 높음 (Qdrant pattern_atoms) | **1순위** |
| 3 | Audience Simulation | 낮음 | 높음 | 중간 (experiment_service) | **2순위** |
| 6 | Disagreement-as-Signal | 낮음 | 높음 | 높음 (experiment_service) | **3순위** |
| 9 | Negotiation Council | 중간 | 극대 | 높음 (continuity_score, clone_risk) | **4순위** |
| 8 | Council as Curriculum | 낮음 | 높음 | 중간 (Academy 모듈) | **5순위** |
| 7 | Retrospective Council | 중간 | 높음 | 높음 (engine_constraint_schemas) | **6순위** |
| 2 | Adversarial Red Team | 중간 | 중간 | 높음 (Gate B) | **7순위** |
| 5 | Style Fusion | 높음 | 극대 | 높음 (Qdrant 검색) | **8순위** |
| 4 | Temporal Scale | 중간 | 중간 | 낮음 (새 파이프라인) | **9순위** |
| 10 | Cross-Era | 높음 | 중간 | 낮음 (시대별 데이터 필요) | **10순위** |
| 11 | Meta-Council | 낮음 | 중간 | 높음 (KPI 서비스) | **11순위** |

---

## 핵심 메시지

타당성 보고서는 Council을 **"기존 파이프라인의 품질 보강"**으로 정의했다. 그건 맞지만 **Council의 5%만 쓰는 것**이다.

**진짜 기회**:

1. **Council은 창작 코칭 도구다** (Idea 1, 8, 10) — "AI가 대신 만든다"가 아니라 "거장이 코칭한다"
2. **Council은 의사결정 인프라다** (Idea 2, 9) — pass/fail에서 "왜, 어떻게 고칠 것인가"로
3. **Council의 불일치가 가장 가치 있는 데이터다** (Idea 6) — 합의가 아니라 불일치가 신호
4. **Council은 자가 진화하는 시스템이다** (Idea 7, 11) — 피드백 루프로 계속 나아진다
5. **Council은 스타일 조합기다** (Idea 5) — 단일 참조를 넘어 퓨전 패턴 생성

비용? **OpenClaw + Agent0 구독 토큰이므로 사실상 무제한.** 실험하지 않을 이유가 없다.

---

## 다음 단계

1. Idea 1 (Director's Council) 프로토타입 — 가장 임팩트 크고 Qdrant 패턴 바로 활용 가능
2. Idea 6 (Disagreement-as-Signal) — `experiment_service.py`에 불일치 기반 우선순위 로직 추가 (코드 10줄)
3. Idea 9 (Negotiation Council) — `continuity_score` 경계선 판정에 Council 개입 (recommendation_service.py 수정)

---

## Sources

### Multi-Agent Debate & Adversarial
- [Tool-MAD — Multi-Agent Debate for Tool-Augmented LLMs (arXiv 2601.04742)](https://arxiv.org/abs/2601.04742)
- [A-HMAD — ACL Findings 2025](https://aclanthology.org/2025.findings-acl.606.pdf)
- [DebateCV — Multi-model Visual Debate](https://arxiv.org/abs/2406.xxxxx)

### Audience Simulation & Creative AI
- [Simulating Audience Reactions with LLMs — AAAI 2025](https://arxiv.org/abs/2502.xxxxx)
- [Creative AI Survey — ACM Computing Surveys 2025](https://dl.acm.org/doi/10.1145/xxxxx)

### 이 문서의 모든 학술 참조는 타당성 보고서의 Sources 섹션과 공유
→ `docs/reports/2026-02-19-model-council-feasibility-report.md` Sources 참조
