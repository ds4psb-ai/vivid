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
│ Structural      │ │ Symmetric       │ │ Luminous Sky    │
│ Tension         │ │ Noir            │ │                 │
│ [Start]         │ │ [Start]         │ │ [Start]         │
└─────────────────┘ └─────────────────┘ └─────────────────┘
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Stage Rhythm    │ │ Gritty Pursuit  │ │ Static          │
│                 │ │                 │ │ Conversation    │
│ [Start]         │ │ [Start]         │ │ [Start]         │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2) 템플릿 공통 구조

- 기본 그래프: `Input → Auteur Capsule → Output`
- 캡슐 노드는 내부 체인을 숨기고 파라미터만 공개
- 템플릿 클릭 시 해당 그래프로 캔버스 시작
- **[New]**: 카드 호버 시 `preview_video_url` 재생 (스타일 미리보기)
- 캡슐 버전은 Pattern Library/Trace 근거로 고정
- 템플릿 메타에 `patternVersion` 표시 (재현성)

---

## 3) 템플릿 카드 정의 (v1) - Style Based Naming

### 3.1 Structural Tension (Bong Style)

- **templateId**: `tmpl-auteur-bong`
- **title**: Structural Tension
- **capsuleId**: `auteur.bong-joon-ho`
- **tagline**: Precise blocking with sudden genre shifts
- **preview**: Tunnel/Stairs metaphor video
- **default params**:
  - `style_intensity`: 0.70
  - `tension_bias`: 0.70

### 3.2 Symmetric Noir (Park Style)

- **templateId**: `tmpl-auteur-park`
- **title**: Symmetric Noir
- **capsuleId**: `auteur.park-chan-wook`
- **tagline**: Obsessive symmetry and high-contrast vengeance
- **preview**: Neon/Wallpaper pattern video
- **default params**:
  - `style_intensity`: 0.75
  - `symmetry_bias`: 0.80

### 3.3 Luminous Sky (Shinkai Style)

- **templateId**: `tmpl-auteur-shinkai`
- **title**: Luminous Sky
- **capsuleId**: `auteur.shinkai`
- **tagline**: Hyper-realistic light, clouds, and emotional longing
- **preview**: Cloud/Sunset timelapse video
- **default params**:
  - `style_intensity`: 0.70
  - `light_diffusion`: 0.75

### 3.4 Stage Rhythm (Lee Style)

- **templateId**: `tmpl-auteur-leejunho`
- **title**: Stage Rhythm
- **capsuleId**: `auteur.lee-junho`
- **tagline**: Music-synced cuts and performance-driven energy
- **preview**: Concert lights/Stage motion video
- **default params**:
  - `style_intensity`: 0.68
  - `music_sync`: 0.70

### 3.5 Gritty Pursuit (Na Style)

- **templateId**: `tmpl-auteur-na`
- **title**: Gritty Pursuit
- **capsuleId**: `auteur.na-hongjin`
- **tagline**: Relentless handheld camera and raw chaos
- **preview**: Running/Chase scene video
- **default params**:
  - `style_intensity`: 0.80
  - `chaos_bias`: 0.80

### 3.6 Static Conversation (Hong Style)

- **templateId**: `tmpl-auteur-hong`
- **title**: Static Conversation
- **capsuleId**: `auteur.hong-sangsoo`
- **tagline**: Long takes, awkward pauses, and sudden zooms
- **preview**: Cafe conversation/Static shot video
- **default params**:
  - `style_intensity`: 0.65
  - `stillness`: 0.85
