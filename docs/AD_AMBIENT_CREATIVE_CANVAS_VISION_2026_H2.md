# Ambient Creative Canvas OS — Vision Document (2026 H2)

> **Status**: Active Vision (SSOT 상위 참조)
> **Version**: 1.0
> **Date**: 2026-02-23
> **Owners**: VIVID Product / AD Studio / Platform

---

## 1) The Insight — Creation Is Non-Linear

감독의 창작 프로세스는 선형이 아니다.

- 카페에서 걸으며 사진을 찍는다
- 대화 중에 아이디어가 떠오른다
- 새벽 3시에 영상을 보며 18분 지점의 영감을 얻는다
- 출근길에 32분 지점의 전환을 메모한다

100분 장편의 타임라인은 순서대로 채워지지 않는다. **이빨 빠지듯, 비선형적으로 채워진다.**

현재 도구들은 "책상 앞에 앉아 Scene 1부터 순서대로 만든다"는 선형 워크플로를 가정한다. 이것이 근본적 미스매치다.

### 패러다임 전환

```
FROM: continuity_score 중심 조감독 OS
      └─ 선형, 책상 앞 워크플로
      └─ "다음 씬을 추천해줘"

  TO: Ambient Creative Canvas OS
      └─ 비선형, 생활 속 창작
      └─ "아무 때나 영감을 던지면 100분 블루프린트에 자동 배치"
      └─ continuity는 품질 게이트 (인프라 레이어)
```

---

## 2) Blueprint Canvas — The 100-Minute Sparse Timeline

**Blueprint Canvas**는 100분 장편을 5분 단위 20셀 그리드로 표현한 sparse 타임라인이다.

```
[00:00] [05:00] [10:00] [15:00] [20:00] [25:00] [30:00] [35:00] [40:00] [45:00]
  ██      --      ██      --      --      ██      --      --      --      ██
[50:00] [55:00] [60:00] [65:00] [70:00] [75:00] [80:00] [85:00] [90:00] [95:00]
  --      ██      --      --      ██      --      --      ██      --      --

██ = Fragment가 배치된 셀 (filled)
-- = 빈 셀 (gap)
```

### 핵심 속성

| 속성 | 설명 |
|------|------|
| **Sparse** | 대부분 비어 있는 상태에서 시작. 시간이 지나며 채워짐 |
| **Non-sequential** | 어떤 셀이든 먼저 채울 수 있음. 32분부터 시작해도 됨 |
| **Multi-resolution** | 셀 안에서 메모 → 스토리보드 → 키비주얼 → 프롬프트 → 영상으로 점진 구체화 |
| **Persistent** | OpenClaw Workspace Memory에 영구 저장 |

### Canvas State

```python
class CanvasState:
    project_id: str
    total_duration_min: int = 100  # configurable
    cell_size_min: int = 5
    cells: dict[int, list[Fragment]]  # cell_index → fragments
    fill_rate: float  # 0.0 ~ 1.0
    last_updated: datetime
```

---

## 3) Fragment — The Atomic Unit of Inspiration

**Fragment**는 감독이 어떤 채널에서든 던지는 영감의 최소 단위다.

### Fragment Types

| Type | 예시 | 입력 채널 |
|------|------|----------|
| `text_memo` | "32분 지점에서 주인공이 비를 맞으며 걷는 장면" | Telegram, Web |
| `voice_memo` | 음성 메모 (STT 변환) | Telegram |
| `photo` | 거리 사진, 레퍼런스 이미지 | Telegram, Web |
| `video_clip` | 레퍼런스 영상 클립 | Telegram, Web |
| `url_bookmark` | 영감 받은 영상/글 URL | Telegram, Web |
| `sketch` | 손 스케치, 스토리보드 낙서 | Web |
| `prompt_draft` | 엔진 프롬프트 초안 | Web |

### Fragment Schema

```python
class Fragment:
    fragment_id: str
    project_id: str
    fragment_type: FragmentType
    content: str | bytes  # text or media
    metadata: dict  # STT transcript, EXIF, etc.
    source_channel: str  # "telegram" | "web" | "api"
    created_at: datetime
    # Auto-Placement results
    suggested_cell: int | None
    placement_confidence: float  # 0.0 ~ 1.0
    placement_reason: str
    # Progressive Materialization
    materialization_level: int  # 0=memo, 1=storyboard, 2=keyvisual, 3=prompt, 4=video
    # Rights
    rights_status: str  # "unchecked" | "cleared" | "flagged"
```

---

## 4) Fragment Ingestion Pipeline

감독이 채널에 영감을 던지면, 자동으로 분류하고 Canvas에 배치한다.

```
Director
  │
  ├─ Telegram Bot ──┐
  ├─ Web UI ────────┤
  └─ API ───────────┘
                    │
            ┌───────▼───────┐
            │  Channel      │  ChannelEvent v1 정규화
            │  Adapters     │  (D-08 승격)
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  Fragment     │  타입 분류 + 메타데이터 추출
            │  Classifier   │  (STT, EXIF, URL preview)
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  Rights       │  IP 위험 조기 분류
            │  Pre-screen   │  (Rights Graph §6.4)
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  Auto-        │  Canvas 상태 + Fragment → 배치 결정
            │  Placement AI │  (§5 참조)
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  Blueprint    │  Fragment 저장 + Canvas 업데이트
            │  Canvas       │  (OpenClaw Memory)
            └───────────────┘
```

### SLO

| 단계 | p95 목표 |
|------|---------|
| Fragment Classification | < 1s |
| Auto-Placement | < 3s |
| End-to-end (채널 수신 → Canvas 반영) | < 5s |

---

## 5) Auto-Placement AI

Fragment가 100분 타임라인의 **어디에** 해당하는지 자동 판단한다.

### 입력

1. **Fragment 자체**: 텍스트/이미지/영상의 내용과 메타데이터
2. **Canvas 현재 상태**: 어떤 셀이 채워져 있고, 각 셀의 materialization 수준
3. **Project Context**: 장르, 시놉시스, 캐릭터 설정, 감독 스타일 프로파일
4. **Cinema Grammar KB**: NarrativeTheoryKB 기반 서사 위치 판단 (setup/conflict/payoff 등)
5. **Pattern Atoms**: 패턴 기반 타임라인 배치 (유사 장면이 보통 어디에 오는지)

### 출력

```json
{
  "suggested_cell": 6,
  "cell_time_range": "30:00 ~ 34:59",
  "confidence": 0.82,
  "reason": "주인공의 내적 갈등 묘사 → NarrativeTheoryKB midpoint crisis 패턴 매칭. 기존 25분 셀의 갈등 고조와 서사적으로 연결됨.",
  "alternative_cells": [
    {"cell": 8, "confidence": 0.61, "reason": "climax 직전 긴장 고조 위치로도 적합"}
  ]
}
```

### 학습 루프

1. **명시적 피드백**: 감독이 배치를 수락/이동/거부
2. **암묵적 피드백**: 자동 배치된 Fragment가 Materialization으로 진행하면 수락으로 간주
3. **Flywheel**: 더 많은 Fragment 수집 → 더 풍부한 프로젝트 메모리 → 더 정확한 Auto-Placement → 더 높은 채택률

---

## 6) Gap Detection & Suggestion

Canvas의 빈 구간을 시각화하고, NarrativeTheoryKB 기반으로 무엇이 필요한지 제안한다.

### Gap Types

| Type | 설명 | 제안 방식 |
|------|------|----------|
| **Structural Gap** | 서사 구조상 반드시 있어야 하는 beat가 누락 (setup/inciting incident/climax 등) | NarrativeTheoryKB 기반 필수 beat 제안 |
| **Emotional Gap** | 감정 곡선에 급격한 단절 (고조 후 즉시 해소, 중간 전환 없음) | 감정 브릿지 장면 제안 |
| **Visual Gap** | 시각적 연속성 단절 (공간/시간/조명 점프) | EditingGrammarKB 기반 전환 장면 제안 |
| **Rhythm Gap** | 리듬 단조로움 (장면 길이 변화 없음) | StylePatternKB 기반 리듬 변주 제안 |

### Gap Visualization

```
Canvas Fill Map (30-cell example):
█ █ _ _ █ _ █ _ _ █ _ _ _ █ _ █ _ _ _ █ _ _ █ _ _ _ _ _ █ _

Gap Analysis:
├─ Cell 2-3: STRUCTURAL GAP — Inciting Incident missing
├─ Cell 7-8: EMOTIONAL GAP — tension plateau, needs escalation
├─ Cell 10-12: RHYTHM GAP — uniform 5-min blocks, consider varying
└─ Cell 24-27: STRUCTURAL GAP — pre-climax buildup absent

Suggestions generated: 4
Priority: Cell 2-3 (structural, highest narrative impact)
```

---

## 7) Progressive Materialization — 5-Level Concretization

Fragment는 5단계를 거쳐 점진적으로 구체화된다. **양방향** — 상위 레벨에서 하위로 되돌아갈 수 있다.

```
Level 0: Memo          "비 오는 거리, 주인공 혼자 걷는다"
    ↕
Level 1: Storyboard    [러프 스케치 + 샷 구성 노트]
    ↕
Level 2: Key Visual    [AI 생성 스틸 이미지 / 컨셉 아트]
    ↕
Level 3: Prompt        [엔진별 컴파일된 프롬프트 세트]
    ↕
Level 4: Video         [생성된 영상 클립 — 최종 산출물]
```

### 양방향 흐름

- **하향 (Materialization)**: 메모 → 스토리보드 → 키비주얼 → 프롬프트 → 영상
- **상향 (Revision)**: 영상 피드백 → 프롬프트 수정 → 키비주얼 재생성 → 스토리보드 수정

### Council 검증 지점

| Level 전환 | Council 역할 |
|-----------|-------------|
| 0→1 | NarrativeTheoryKB: 서사 위치 적절성 검증 |
| 1→2 | EditingGrammarKB: 시각 문법 준수 확인 |
| 2→3 | Prompt Compiler: 엔진별 최적 프롬프트 생성 |
| 3→4 | Gate B: 3모델 OR-gate (시각/서사/법적 검증) |

---

## 8) North Star Metrics

### Primary: `creative_fill_rate` (1순위)

```
creative_fill_rate = filled_cells / total_cells
```

Canvas가 얼마나 채워졌는가. **창작의 진행도를 직접 측정한다.**

- 목표: 30일 내 30%+ (프로젝트당)
- 측정 단위: 프로젝트별 일간/주간 추이

### Quality Gate: `continuity_score` (품질 인프라)

연속성은 당연히 중요하다. 하지만 **1순위 목표가 아니라 품질 게이트**다.

```
continuity_score >= 0.80: 정상
continuity_score 0.60~0.79: 경고 (보정 제안)
continuity_score < 0.60: 차단
```

- continuity는 Fragment가 영상(Level 4)으로 Materialize될 때 검증한다
- Canvas 채우기 단계에서는 continuity를 강제하지 않는다 (창작 자유 보장)

### Supporting Metrics

| Metric | 정의 | 목표 |
|--------|------|------|
| `fragment_capture_rate` | 일 평균 Fragment 수집 수 | 5+/day |
| `auto_placement_accuracy` | 자동 배치 수락률 | 70%+ |
| `materialization_velocity` | Fragment→Video 평균 소요 시간 | < 4h |
| `gap_suggestion_adoption` | Gap 제안 수락률 | 40%+ |

---

## 9) Why This Wins — The Flywheel

```
More Fragments captured
        │
        ▼
Richer Project Memory (OpenClaw)
        │
        ▼
Better Auto-Placement accuracy
        │
        ▼
Higher creative_fill_rate
        │
        ▼
Better Gap Detection (more context)
        │
        ▼
More targeted suggestions
        │
        ▼
Director captures MORE fragments (lower friction, higher value)
        │
        └──────────── back to top ────────────┘
```

**핵심**: 기존 도구는 "결과물(영상)"에서 경쟁한다. VIVID는 **"창작 과정(Blueprint 조립)"**에서 경쟁한다. 결과물은 commodity — 과정이 해자다.

### 데이터 해자 축적

| 자산 | 축적 방식 | 경쟁자 복제 난이도 |
|------|----------|------------------|
| `director_style_profile` | Fragment 패턴 + 배치 선호 학습 | 높음 (감독별 누적 데이터) |
| `blueprint_canvas` | 프로젝트별 100분 구조 지식 | 높음 (장기 사용 필요) |
| `fragment_ingestion_pipeline` | 채널별 영감 분류/배치 노하우 | 중간 (파이프라인은 복제 가능, 학습 데이터는 불가) |
| `continuity_graph` | 씬-샷 연쇄 지식 | 높음 (기존 자산) |
| `rights_graph` | 합법 창작 증빙 체계 | 높음 (기존 자산) |

---

## 10) Channel Priority

### Phase 1: Telegram + Web UI (우선)

| 채널 | 역할 | 이유 |
|------|------|------|
| **Telegram** | Fragment 캡처 주력 채널 | 생활 속 즉시 전송. 사진/음성/텍스트 모두 지원. 봇 API 성숙도 높음 |
| **Web UI** | Canvas 시각화 + Materialization 작업 | 복잡한 타임라인 조작은 큰 화면 필요 |

### Phase 2: KakaoTalk (후순위)

- 한국 시장 도달률은 높지만, 봇 API 제약이 큼 (메시지 타입/크기/빈도)
- Fragment 캡처 용도로는 Telegram이 우월
- KakaoTalk은 알림/요약 전송 채널로 활용

### 채널 아키텍처

모든 채널은 **Channel Adapter 계층** (D-08)으로 격리한다. AD Core는 채널명을 모른다.

```
Telegram Adapter ──┐
Web Adapter ───────┤──→ ChannelEvent v1 ──→ Fragment Ingestion Pipeline
KakaoTalk Adapter ─┘
```

---

## 11) Engine Strategy — 3-Engine (Sora Removed)

### 2026 현실: 멀티샷 일관성은 Commodity

| 엔진 | 핵심 능력 | 2026 현황 |
|------|----------|----------|
| **Seedance 2.0** | 4-modal input, Director Control (lens switch, camera path), multi-shot | 15초, 1080p, 이미지/비디오/오디오 참조 입력 |
| **Kling 3.0** | 6-shot storyboard, 완벽한 캐릭터 일관성 | 멀티모달, 고품질 움직임 |
| **Veo 3** | 네이티브 오디오 생성, 4/6/8초 duration | 음향까지 통합된 유일한 엔진 |

### Sora 제거 사유

1. **멀티샷 미지원**: 2026-02 기준 단일 샷 생성만 가능. Blueprint Canvas 워크플로와 근본적 비호환
2. **권리 거부 과잉**: 저작권 캐릭터/음악 거부 정책이 Original-IP Foundry의 합법 재창조 워크플로에서도 과도하게 발동. 창작 자유도 제한
3. **비용 대비 효용**: 멀티샷 일관성이 commodity된 상황에서 Sora만의 차별 가치 부재

### Prompt Compiler 영향

```python
# Before: 4 engines
DEFAULT_ENGINES = ["kling", "veo", "seedance", "sora"]

# After: 3 engines
DEFAULT_ENGINES = ["kling", "seedance", "veo"]
```

> **코드 참조**: `backend/app/features/original_ip_foundry/prompt_compiler.py` — Sora adapter deprecation 필요

---

## 12) Relationship to Other Documents

본 문서는 "Why"를 정의한다. 다른 문서들은 "How"를 정의한다.

```
AD_AMBIENT_CREATIVE_CANVAS_VISION_2026_H2.md  ← 본 문서 (Why)
    │
    ├── AD_CO_DIRECTOR_OS_SSOT_2026_H2.md     (How — 전체 설계)
    ├── AD_STUDIO_MASTERPIECE_PATTERN_2026_H2.md (How — 품질 패턴)
    ├── AD_30DAY_TIGER_RUNBOOK_2026-02.md      (How — 30일 실행)
    └── ORIGINAL_IP_FOUNDRY_OPERATIONS_RUNBOOK_2026-02.md (How — 운영)
```

### 문서 간 용어 통일

| 용어 | 정의 | 첫 등장 |
|------|------|--------|
| **Blueprint Canvas** | 100분 sparse 타임라인 그리드 (5분×20셀) | §2 |
| **Fragment** | 영감의 최소 단위 (텍스트/사진/음성/영상/URL/스케치/프롬프트) | §3 |
| **Fragment Ingestion Pipeline** | 채널→분류→배치 파이프라인 | §4 |
| **Auto-Placement AI** | Fragment의 Canvas 위치를 자동 판단하는 지능 | §5 |
| **Gap Detection** | Canvas 빈 구간 감지 + NarrativeTheoryKB 기반 제안 | §6 |
| **Progressive Materialization** | Memo→Storyboard→KeyVisual→Prompt→Video 5단계 구체화 | §7 |
| **`creative_fill_rate`** | filled_cells / total_cells — North Star Metric | §8 |
| **`continuity_score`** | 시퀀스 연속성 — Quality Gate (not North Star) | §8 |

---

## 13) Summary — One Line

**VIVID의 승부처는 "어떤 샷을 만들까"가 아니라, "일상의 영감을 어떻게 100분 블루프린트로 조립하는가"다.**
