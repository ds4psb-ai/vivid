# 🎬 GEMINI ONE-SHOT VIDEO ANALYSIS v3.0

> **사용법**: 이 프롬프트를 Gemini에 영상과 함께 업로드하세요.
> ONE-SHOT으로 완벽한 JSON 출력 → Claude에서 도구별 프롬프트 분기

---

## 🎯 역할 부여

You are a **forensic video analyst** and **cinematography expert** specializing in video parody production. 

Your task: Analyze this video and output a **perfectly structured JSON** that enables ONE-SHOT prompt generation for AI image/video tools.

---

## 📋 분석 요청

아래 영상을 분석해서 **정확히 아래 JSON 형식**으로 출력해줘.

### 필수 분석 항목:

1. **씬 분할** (컷 변경 기준, 1/100초 정밀도)
2. **Visual Forensic** (shot type, camera angle, lighting)
3. **ALL PEOPLE 식별** (흐릿한 배경 인물 포함!)
4. **의상 색깔** (정확한 색상명)
5. **ANCHOR 씬 선정** (얼굴이 가장 잘 보이는 씬)
6. **도구 추천** (NanoBanana / MJ V7 / Kling / Veo)
7. **Visual Rhyme** (대비되는 씬 쌍)

---

## 📤 출력 형식 (이 형식 정확히 따라해!)

```json
{
  "video_title": "Birthday Paradox (가제)",
  "total_duration": "00:15",
  "anchor_scene_id": 2,
  "target_ethnicity": "Korean",
  
  "scenes": [
    {
      "id": 1,
      "timestamp": "00:01.15",
      "duration_sec": 3,
      "name": "The Arrival",
      
      "visual_forensic": {
        "shot_type": "Wide Shot",
        "camera_angle": "Slight High Angle",
        "camera_height": "Above adult eye level",
        "composition": "Reverse triangle, boy centered",
        "focus": "Boy sharp, parents soft bokeh"
      },
      
      "all_people": [
        {
          "position": "center",
          "role": "boy",
          "clothing_color": "blue striped t-shirt",
          "visibility": "clear"
        },
        {
          "position": "left_background",
          "role": "dad",
          "clothing_color": "green shirt",
          "visibility": "blurred"
        },
        {
          "position": "right_background",
          "role": "mom",
          "clothing_color": "red sweater",
          "visibility": "blurred"
        }
      ],
      
      "lighting": {
        "type": "tungsten",
        "color_temp_k": 3200,
        "direction": "front",
        "special": null
      },
      
      "mood": "nostalgic",
      "era": "1990s",
      
      "tool_recommendation": {
        "image": "NanoBanana Pro",
        "image_reason": "3+ people, complex composition",
        "video": "Kling 2.6",
        "video_reason": "no dialogue"
      },
      
      "special_notes": [
        "Table should be empty - cake not yet placed"
      ]
    }
  ],
  
  "visual_rhymes": [
    {
      "source_scene_id": 3,
      "target_scene_id": 6,
      "same_composition": true,
      "contrast": "clapping hands → holding smartphones",
      "lighting_flip": "warm 3200K → cold 6500K"
    }
  ],
  
  "korean_adaptation": {
    "child": {
      "hair": "black bowl cut (1990s Korean style)",
      "eyes": "single eyelids",
      "skin": "Korean skin tone"
    },
    "adults": {
      "style": "Korean family look",
      "skin": "Korean skin tones"
    },
    "environment": "1990s Korean apartment"
  },
  
  "error_prevention": {
    "global_no_list": [
      "western features",
      "caucasian skin",
      "blonde hair",
      "blue eyes",
      "modern furniture",
      "LED lights",
      "smartphones in 1990s scenes"
    ],
    "scene_specific_no": {
      "1": ["cake on table", "duplicate cake"],
      "5": []
    }
  }
}
```

---

## ⚠️ 중요 규칙

### ALL PEOPLE Rule
> 프레임에 보이는 **모든 사람** 식별해야 함!
> 흐릿하게 보이는 배경 인물도 반드시 포함
> 각 인물의 위치, 역할, 의상 색깔 명시

### 도구 추천 기준

| 조건 | 이미지 도구 | 영상 도구 |
|------|------------|----------|
| ANCHOR (얼굴 고정 중요) | MJ V7 | - |
| 3명 이상 인물 | NanoBanana | Kling |
| 클로즈업 | MJ V7 | Kling |
| 대사 있음 | - | Veo 3.1 |

### Visual Rhyme
> 대비되는 씬 쌍 식별
> 같은 구도, 다른 분위기 (예: 과거 따뜻함 ↔ 현재 차가움)

---

## 🎯 출력 완료 후

이 JSON을 Claude에 전달하면:
1. 도구별 프롬프트 자동 분기
2. ALL PEOPLE 규칙 적용
3. error_prevention으로 --no 파라미터 생성
4. 최소 수정으로 FINAL_PROMPTS_MINIMAL 완성!
