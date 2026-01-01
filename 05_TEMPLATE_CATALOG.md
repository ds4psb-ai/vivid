# Auteur Template Catalog (v1)

**작성**: 2025-12-24  
**대상**: Product / Design / Engineering  
**목표**: 메인 카드 UI에 노출될 거장 템플릿 정의  

---

## 1) 카드 UI 와이어프레임 (개념)

```
[ Hero ]
┌───────────────────────────────────────────────┐
│  Choose an Auteur Template                    │
│  Start from a sealed style capsule            │
└───────────────────────────────────────────────┘

[ Card Grid ]
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 구조적 긴장     │ │ 대칭 누아르     │ │ 빛의 하늘       │
│ [Start]         │ │ [Start]         │ │ [Start]         │
└─────────────────┘ └─────────────────┘ └─────────────────┘
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 무대 리듬       │ │ 거친 추격       │ │ 정적 대화       │
│ [Start]         │ │ [Start]         │ │ [Start]         │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2) 템플릿 공통 구조

- 기본 그래프: `Input → Auteur Capsule → Script/Beat → Storyboard → Output`
- 캡슐 노드는 내부 체인을 숨기고 파라미터만 공개
- 템플릿 클릭 시 해당 그래프로 캔버스 시작
- **[New]**: 카드 호버 시 `preview_video_url` 재생 (스타일 미리보기)
- 캡슐 버전은 Pattern Library/Trace 근거로 고정
- 템플릿 메타에 `patternVersion` 표시 (재현성)

### 2.1 템플릿 패밀리 (확장 기준)

- **Auteur Templates**: 거장 클러스터 노트북 기반
- **Creator Self-Style**: 개인 노트북(자기 작품/참조) 기반
- **Synapse Templates**: A+B+D→C 변환 규칙을 캡슐로 패키징
- **Pipeline Templates**: PD/작가용 시나리오 → 스토리보드 파이프라인

Ref: `23_TEMPLATE_SYSTEM_SPEC_CODEX.md`

---

## 3) 템플릿 카드 정의 (v1) - Style Based Naming

### 3.1 구조적 긴장 (봉준호)

- **templateId**: `tmpl-auteur-bong`
- **title**: 구조적 긴장
- **capsuleId**: `auteur.bong-joon-ho`
- **tagline**: 정교한 동선과 장르 전환의 긴장감
- **preview**: Tunnel/Stairs metaphor video
- **default params**:
  - `style_intensity`: 0.70
  - `tension_bias`: 0.70

### 3.2 대칭 누아르 (박찬욱)

- **templateId**: `tmpl-auteur-park`
- **title**: 대칭 누아르
- **capsuleId**: `auteur.park-chan-wook`
- **tagline**: 강박적 대칭과 강한 대비
- **preview**: Neon/Wallpaper pattern video
- **default params**:
  - `style_intensity`: 0.75
  - `symmetry_bias`: 0.80

### 3.3 빛의 하늘 (신카이)

- **templateId**: `tmpl-auteur-shinkai`
- **title**: 빛의 하늘
- **capsuleId**: `auteur.shinkai`
- **tagline**: 현실적인 빛과 구름, 감정의 여운
- **preview**: Cloud/Sunset timelapse video
- **default params**:
  - `style_intensity`: 0.70
  - `light_diffusion`: 0.75

### 3.4 무대 리듬 (이준호)

- **templateId**: `tmpl-auteur-leejunho`
- **title**: 무대 리듬
- **capsuleId**: `auteur.lee-junho`
- **tagline**: 음악 싱크 컷과 퍼포먼스 에너지
- **preview**: Concert lights/Stage motion video
- **default params**:
  - `style_intensity`: 0.68
  - `music_sync`: 0.70

### 3.5 거친 추격 (나홍진)

- **templateId**: `tmpl-auteur-na`
- **title**: 거친 추격
- **capsuleId**: `auteur.na-hongjin`
- **tagline**: 거친 핸드헬드와 긴박한 추격
- **preview**: Running/Chase scene video
- **default params**:
  - `style_intensity`: 0.80
  - `chaos_bias`: 0.80

### 3.6 정적 대화 (홍상수)

- **templateId**: `tmpl-auteur-hong`
- **title**: 정적 대화
- **capsuleId**: `auteur.hong-sangsoo`
- **tagline**: 롱테이크와 어색한 침묵, 돌연한 줌
- **preview**: Cafe conversation/Static shot video
- **default params**:
  - `style_intensity`: 0.65
  - `stillness`: 0.85

### 3.7 프로덕션: 무대 리허설 (스튜디오)

- **templateId**: `tmpl-production-stage`
- **title**: 프로덕션: 무대 리허설
- **capsuleId**: `production.stage-rehearsal`
- **tagline**: 샷 리스트 → 프롬프트 → 생성 워크플로
- **preview**: Stage rehearsal cinematic still
- **default params**:
  - `style_intensity`: 0.70
  - `music_sync`: 0.60
  - `render_quality`: preview
  - `aspect_ratio`: 2.39:1
  - `lens`: 50mm anamorphic
  - `film_stock`: Kodak Vision3 250D
  - `time_of_day`: night
  - `mood`: anticipation
