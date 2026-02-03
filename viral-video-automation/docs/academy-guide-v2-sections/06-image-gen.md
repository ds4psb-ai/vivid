# 🖼️ 이미지 생성 도구

> Builder 프롬프트 → 이미지 생성

---

## 도구 비교

| 도구 | 언어 | 강점 | 추천 용도 |
|------|------|------|----------|
| **NanoBanana Pro** | 한글 | 빠른 속도, 캐릭터 일관성 | 입문자, 빠른 테스트 |
| **Midjourney V7** | 영문 | 예술적 스타일 | 고품질 결과물 |

---

# NanoBanana Pro (추천)

> 🇰🇷 **한글 프롬프트 지원!**

---

## 특징

| 항목 | 내용 |
|------|------|
| 언어 | 한글 프롬프트 OK |
| 해상도 | 4K 이미지 |
| 속도 | 약 3~8초 |
| 강점 | 캐릭터 일관성 우수 |

**접속**: [nanobanana-pro.com](https://nanobanana-pro.com) 또는 AI Studio 내장

---

## 사용 순서

☐ **Step 1**: 레퍼런스 이미지 업로드 (기준 프레임)

☐ **Step 2**: Builder 프롬프트 붙여넣기

☐ **Step 3**: Generate 클릭

☐ **Step 4**: 4K 이미지 다운로드

---

# Midjourney V7

> 🎨 **예술적 스타일 강점**

---

## 특징

| 항목 | 내용 |
|------|------|
| 언어 | 영문 프롬프트 전용 |
| 강점 | 예술적 표현, 스타일 커스터마이징 |
| 접속 | Discord 또는 midjourney.com |

---

## 핵심 파라미터

### 기본 설정

```
--v 7         # 버전 7
--ar 9:16     # 세로 영상 비율
--style raw   # 원본 스타일
```

### 이미지 가중치

```
--iw 2.0      # 높을수록 레퍼런스 충실
```

### 캐릭터 레퍼런스

```
--cref [이미지URL]   # 캐릭터 일관성 유지
```

### 스타일 강도

```
--stylize 250   # 1막 (과거) - 따뜻하게
--stylize 400   # 2막 (현재) - 선명하게
```

### 제외 요소

```
--no text, watermark, logo
```

---

## 전체 프롬프트 예시

```
A 40-year-old woman holding a birthday cake in a cozy living room,
warm tungsten lighting, sepia tones,
a 7-year-old boy wearing a party hat smiling brightly,
medium shot, heartwarming family moment
--ar 9:16 --v 7 --iw 2.0 --stylize 250 --cref [URL]
```

---

## 체크리스트

☐ 기준 프레임 이미지 준비

☐ Builder 프롬프트 준비 (한글 또는 영문)

☐ 도구 선택 (NanoBanana / Midjourney)

☐ 이미지 생성 완료

☐ 결과물 다운로드

---

> **다음**: [🎥 영상 생성](./07-video-gen.md)
