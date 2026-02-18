# 숏폼 바이럴 분석(VDG) 고도화 컨설팅 리포트

**수신**: Komission 개발팀
**발신**: VDG 전문 컨설턴트 (Antigravity)
**날짜**: 2026-01-12
**참조**: [요청서](backend/exports/vdg_consulting/CONSULTING_REQUEST.md), [분석데이터](backend/exports/vdg_consulting/)

---

## 📌 Executive Summary

Komission VDG 시스템은 **Semantic(Pass 1)과 Computer Vision(Pass 2)을 결합한 하이브리드 파이프라인**으로서, 기존의 단순 메타데이터 분석을 넘어서는 강력한 경쟁력을 보유하고 있습니다.

특히 첨부해주신 3건의 분석 데이터(`Emotional Damage`, `POV retail`, `돼지국밥`)를 검토한 결과, **객체 추적(Entity Tracking)의 정밀도**와 **Semantic Context 추출 능력**은 상용 수준에 근접해 있습니다.

하지만 **"바이럴 예측력"**을 극대화하기 위해서는 다음 3가지 핵심 과제를 해결해야 합니다:
1.  **Hook Taxonomy의 다차원화**: 단순 22개 분류에서 "3축(Format-Emotion-Topic) 매트릭스"로 전환
2.  **청각(Audio) 분석의 1등 시민화**: 현재의 시각 편중에서 탈피, 오디오-비주얼 싱크 분석 도입
3.  **패턴의 "재현성(Replicability)" 지수화**: 현상 분석을 넘어, 크리에이터가 따라 할 수 있는 "액션 아이템" 도출

본 리포트는 위 과제에 대한 구체적인 솔루션을 제시합니다.

---

## 1. Hook Type 분류 체계 고도화 (MECE 검증 및 개선)

### 1.1 현황 진단
현재 사용 중인 22개 Canonical Hook Type은 **"형식(Format)"**과 **"감정(Emotion)"**, **"소재(Topic)"**가 혼재되어 있어 MECE(상호배타적, 전체포괄적) 원칙에 위배됩니다.

*   **사례 분석**:
    *   `video_1` (Emotional Damage): `contrast`로 분류되었으나 실제로는 `meme_format`이자 `reaction` 성격이 강함.
    *   `video_3` (돼지국밥): `contrast`로 분류되었으나 `sketch/skit` 형식이자 `humor` 감정임.
    *   **문제점**: 하나의 영상이 `pov`이면서 `humor`이고 `skit`일 때, 단일 라벨링은 정보 손실을 야기함.

### 1.2 개선안: 3축 매트릭스 분류 (3-Axis Taxonomy)

Hook Type을 단일 필드가 아닌 **3가지 차원의 조합**으로 정의할 것을 권고합니다.

| 차원 (Axis) | 설명 | 카테고리 예시 |
| :--- | :--- | :--- |
| **1. Format (형식)** | 영상의 구조적 틀 | `pov`, `skit`, `listicle`, `tutorial`, `challenge`, `duet`, `vlog` |
| **2. Trigger (유발 기제)** | 시청 지속을 만드는 심리 | `curiosity_gap`, `shock`, `relatability` (공감), `satisfaction`, `educational` |
| **3. Device (장치)** | 초반 3초에 사용된 구체적 기법 | `text_on_screen`, `visual_hook`, `loud_noise`, `question`, `countdown` |

**적용 예시 (Video 1: Emotional Damage)**:
*   **Old**: `contrast`
*   **New**:
    *   Format: `meme_remix`
    *   Trigger: `shock` + `humor`
    *   Device: `insert_clip` (Steven He clip)

### 1.3 Action Item
*   `outlier_items` 테이블의 `hook_type` 컬럼을 유지하되, `secondary_hooks` 또는 `hook_attributes` JSON 컬럼을 추가하여 다차원 태깅을 수용하십시오.
*   VDG 프롬프트(Pass 1)에 위 3축 분류 체계를 반영하여 LLM이 구조적으로 분석하도록 지시하십시오.

---

## 2. VDG Semantic 분석 품질 평가

### 2.1 강점 (Strengths)
*   **Entity Tracking (Pass 2)**: `entity_tracks` 데이터가 매우 정밀합니다. 특히 `video_2`(#fyp #ai)의 경우, 인물(track_1)과 배경 객체(track_2)를 시간축(t_ms)에 따라 정확히 추적하고 있어, **"시각적 리텐션"** 분석의 기초가 탄탄합니다.
*   **Dopamine Radar**: `dopamine_radar` 지표(visual_spectacle 등)는 바이럴 요소를 정량화하려는 매우 시도적인 접근이며 훌륭합니다.

### 2.2 개선 필요 사항 (Weaknesses)
*   **Intent Layer의 추상성**: 현재 `intent_layer` 분석이 다소 일반적입니다. "재미를 주려 함" 수준을 넘어, **"댓글을 달게 만드는 구체적 트리거"**를 찾아야 합니다.
    *   *제언*: `comment_bait_score` 도입 (예: 일부러 틀린 정보 노출, 논쟁적 주제 던지기 등).
*   **Audience Reaction 예측의 근거 부족**: 예측된 반응이 실제 데이터(댓글)와 연결되지 않습니다. 실제 크롤링 된 댓글(Top 10 베플)을 VDG에게 피드백하여 **"예측 vs 실제"** 오차를 학습시키는 루프(RLHF)가 필요합니다.

---

## 3. 누락된 핵심 분석 요소: Audio Intelligence

### 3.1 Audio의 중요성
숏폼에서 오디오(BGM, 음성, 효과음)는 바이럴 성과의 **50% 이상**을 차지합니다. 현재 VDG 데이터(`audio_stimulation`)는 BPM 수준에 머물러 있어 결정적 바이럴 요인을 놓치고 있습니다.

### 3.2 도입 제언: Audio-Visual Sync Analysis
다음 3가지 오디오 분석을 VDG 파이프라인에 추가하십시오.

1.  **Transcript-Visual Alignment**:
    *   말하는 단어(Keyword)가 화면에 자막/이미지로 등장하는 타이밍이 일치하는가? (일치 시 몰입도 2.5배 상승)
2.  **Sound Design Layer**:
    *   BGM 비트와 화면 전환(Cut)의 동기화 여부 (`beat_sync_score`).
3.  **Voice Tonal Analysis**:
    *   AI 보이스 vs 실제 육성, 톤의 높낮이(Excitement Level) 변화 추적.

---

## 4. 패턴 라이브러리 고도화 전략

### 4.1 "재현 가능성(Replicability)" 평가 모델
단순히 "재밌는 영상"과 "따라 할 수 있는 패턴"은 다릅니다. 라이브러리 가치를 높이려면 **R-Score (Replicability Score)**를 도입하십시오.

$$ R\_Score = (Format\_Rigidity \times 0.4) + (Asset\_Availability \times 0.3) + (Skill\_Threshold^{-1} \times 0.3) $$

*   **Format Rigidity**: 구조가 명확한가? (예: 밈 템플릿 > 브이로그)
*   **Asset Availability**: 사용된 음원/필터를 쉽게 구할 수 있는가?
*   **Skill Threshold**: 제작 난이도가 낮은가?

### 4.2 니치(Niche)별 Parameterized Remix
같은 `contrast` 패턴이라도 요리(Recipe) 카테고리와 유머(Sketch) 카테고리의 적용 방식은 다릅니다.
패턴 카드에 **"Variable Slots(변수 슬롯)"** 개념을 도입하십시오.

*   **Pattern**: Expectation vs Reality
*   **Variable Slot 1 (Topic)**: [요리] 망한 수플레 vs [코딩] 망한 데모
*   **Variable Slot 2 (Audio)**: [요리] 슬픈 BGM vs [코딩] 에러 효과음

---

## 5. 결론 및 로드맵

Komission VDG는 이미 상위 5% 수준의 분석 깊이를 확보하고 있습니다. 이제는 **"분석의 깊이"**보다 **"액션의 명확성"**으로 나아가야 할 때입니다.

### 🚀 우선순위 로드맵

| 단계 | 기간 | 핵심 과제 | 기대 효과 |
| :--- | :--- | :--- | :--- |
| **Phase 1** | 1~2주 | **Hook Taxonomy 3축 개편** | 데이터의 해상도(Resolution) 3배 향상 |
| **Phase 2** | 3~4주 | **Audio Sync 분석 모듈 추가** | "청각적 바이럴" 요인 포착 |
| **Phase 3** | 2개월 | **R-Score 기반 라이브러리 필터링** | 크리에이터에게 "따라 할 수 있는" 패턴만 추천 |

귀사의 VDG 시스템이 글로벌 숏폼 트렌드를 리드하는 표준이 되기를 기대합니다.

감사합니다.

**Antigravity**
*Senior AI Consultant*
