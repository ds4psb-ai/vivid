# 🍌 NanoBanana Pro Guide

> **Platform**: NanoBanana Pro (Gemini 3 기반)
> **Version**: 2026
> **용도**: 고품질 정적 이미지 생성

---

## 🎯 NanoBanana Pro 특징

| 특징 | 설명 |
|------|------|
| **엔진** | Gemini 3 Pro Image Preview |
| **해상도** | 최대 4K |
| **조명** | 물리 정확 조명 시뮬레이션 |
| **텍스트** | 다국어 텍스트 렌더링 지원 |
| **일관성** | 캐릭터/스타일 유지 기능 |
| **편집** | 이미지 투 이미지 부분 수정 |

---

## 📋 프롬프트 구조

### 기본 구조 (권장 순서)

```
1. [Reference Images] - 구도/캐릭터 레퍼런스
2. [Subject] - 주체 상세 설명
3. [Environment] - 배경/환경
4. [Lighting] - 조명 (Kelvin, 방향, 강도)
5. [Style] - 시각 스타일
6. [Details] - 세부 디테일
7. [Parameters] - --ar, --iw, --cw 등
```

### 예시

```
**[Image 1: COMPOSITION]** [keyframe URL]
**[Image 2: CHARACTER FACE]** [anchor.png]

**From Image 1**: Copy exact composition, lighting angles, camera framing.
**From Image 2**: Copy the character's face exactly - same eyes, nose, lips.

A 7-year-old Korean boy with black bowl-cut hair and single eyelids, 
wearing a striped blue and white t-shirt. Gentle shy smile with closed lips.
Candlelight reflects in both eyes.

Setting: 1990s Korean apartment dining room, evening.
Lighting: Warm tungsten overhead (3200K) with birthday candle fill from below.
Mood: Nostalgic, intimate, warm family moment.

--iw 2.0 --ar 9:16 --v 6.0 --style raw --cw 70 
--no western features, text, watermark, timestamp
```

---

## 🔧 핵심 파라미터

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `--ar` | 9:16 | 세로 영상용 비율 |
| `--iw` | 1.5-2.0 | 이미지 가중치 (높을수록 레퍼런스 유사) |
| `--cw` | 50-100 | 캐릭터 가중치 (얼굴 일관성) |
| `--stylize` | 100-300 | 스타일 강도 (낮을수록 정확) |
| `--style raw` | - | 최소 스타일 적용 (실사용) |
| `--no` | [제외] | Negative prompt |

---

## 🔗 앵커 시스템

### 순서 (반드시 준수!)

```
1️⃣ ANCHOR 씬 먼저 생성
   - 캐릭터 얼굴이 가장 선명한 씬 선택
   - 조명 좋고, 표정 중립적인 것
   - anchor.png로 저장

2️⃣ 나머지 씬 생성
   - [Image 2: CHARACTER FACE] anchor.png 첨부
   - --cw 50-70 설정
```

### 멀티 이미지 퓨전

```
**[Image 1]** composition_reference.png → 구도 복사
**[Image 2]** anchor.png → 얼굴 복사
**[Image 3]** style_reference.png → 스타일 복사 (선택)
```

---

## 👤 한국인 캐릭터 팁

### 필수 키워드

```
Korean [man/woman/boy/girl], single eyelids, natural skin tone,
East Asian features, [specific age], [hair description]
```

### Negative 필수

```
--no western features, double eyelids, caucasian, 
AI-looking face, plastic skin
```

### 얼굴 일관성

| 문제 | 해결책 |
|------|--------|
| 인종 변경됨 | Negative에 "western features" 강조 |
| 눈 모양 변함 | "single eyelids" 명시 |
| 피부톤 불일치 | "natural Korean skin tone" 추가 |
| 나이 변함 | 정확한 나이 숫자 명시 |

---

## 🖐️ 손 처리 가이드

### 문제 예방

```
✅ 손이 화면 밖
✅ 손이 물체 뒤에 가려짐
✅ 주먹 쥔 상태 (손가락 미노출)
✅ 테이블에 놓인 상태

❌ 복잡한 손 포즈
❌ 손가락 펼친 상태
❌ 두 손이 겹치는 상태
```

### 손 문제 발생 시

```
--no distorted hands, extra fingers, malformed hands
```

---

## 💡 조명 묘사 가이드

### 색온도 키워드

| 느낌 | Kelvin | 키워드 |
|------|--------|--------|
| 따뜻함 | 2700-3200K | warm tungsten, candlelight, amber |
| 중립 | 4000-5000K | neutral daylight, overcast |
| 차가움 | 6000-7500K | cold LED, daylight, blue hour |

### 조명 방향

```
- Overhead: 위에서 아래로
- Underlit: 아래에서 위로 (촛불 효과)
- Side-lit: 측면 조명 (드라마틱)
- Backlit: 역광 (실루엣)
```

---

## 🚨 흔한 문제 & 해결

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 얼굴 불일치 | --cw 낮음 | --cw 80-100 |
| 스타일 왜곡 | --stylize 높음 | --stylize 100, --style raw |
| 배경 이상 | 환경 설명 부족 | 구체적 환경 묘사 추가 |
| 조명 이상 | Kelvin 미지정 | 정확한 색온도 명시 |
| 텍스트 왜곡 | 긴 텍스트 | 짧은 텍스트만, 폰트 지정 |

---

## ✅ 체크리스트

생성 전:
- [ ] 레퍼런스 이미지 준비
- [ ] ANCHOR 먼저 생성 (첫 씬이 아닌 경우)
- [ ] 캐릭터 키워드 포함
- [ ] Negative prompt 설정

생성 후:
- [ ] CRITIQUE_IMAGE.md로 품질 평가
- [ ] 버전 폴더에 저장 (v1, v2...)
- [ ] 확정 시 selected/ 폴더로 이동
