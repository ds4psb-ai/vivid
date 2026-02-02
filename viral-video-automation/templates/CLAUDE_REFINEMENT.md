# 🔄 Claude 정제 규칙 (JSON → 프롬프트)

> **사용법**: Gemini ONE-SHOT JSON을 받아서 도구별 프롬프트로 변환
> **목표**: 1회 정제로 FINAL_PROMPTS_MINIMAL 수준 달성

---

## 📥 입력: Gemini JSON

```json
{
  "scenes": [...],
  "korean_adaptation": {...},
  "error_prevention": {...}
}
```

---

## 📤 출력 변환 규칙

### 1. 도구 분기

| tool_recommendation.image | 사용 템플릿 |
|---------------------------|------------|
| "NanoBanana Pro" | 대화형 한글 프롬프트 |
| "MJ V7" | 영어 + 파라미터 |

| tool_recommendation.video | 사용 템플릿 |
|---------------------------|------------|
| "Kling 2.6" | Elements + Motion |
| "Veo 3.1" | Dialogue + Lip-sync |

---

### 2. NanoBanana Pro 변환

```
입력 JSON:
{
  "all_people": [
    {"position": "center", "role": "boy", "clothing_color": "blue striped"},
    {"position": "left_background", "role": "dad", "clothing_color": "green shirt", "visibility": "blurred"}
  ]
}

출력 프롬프트:
**Image 1 (구도)**: [scene.png]
**Image 2 (얼굴)**: [anchor.png]

Image 1의 구도 유지:
- [composition 필드값]
- [lighting.color_temp_k]K [lighting.type] 조명

Image 2에서 아이 얼굴 복사

모든 인물을 한국인으로:
- 중앙: [role] (Image 2 얼굴) - [clothing_color]
- 왼쪽 배경: 한국인 [role] ([clothing_color], 흐릿해도 한국인 피부톤)

금지: [error_prevention.global_no_list 병합]
```

---

### 3. Midjourney V7 변환

```
입력 JSON:
{
  "visual_forensic": {"shot_type": "Medium Close-up", "camera_angle": "High Angle"},
  "lighting": {"type": "under-lighting", "color_temp_k": 3200}
}

출력 프롬프트:
[scene.png URL]

[shot_type], [camera_angle] looking down at Korean::2 boy.
[korean_adaptation.child 필드들 나열]
[lighting.type] [lighting.color_temp_k]K, [mood] atmosphere.

--iw 2.0 --ar 9:16 --v 7 --style raw
--no [error_prevention.global_no_list + scene_specific_no 병합]
```

---

### 4. --no 파라미터 자동 생성

```javascript
function generateNoParams(json, sceneId) {
  const global = json.error_prevention.global_no_list;
  const specific = json.error_prevention.scene_specific_no[sceneId] || [];
  return [...global, ...specific].join(", ");
}
```

**예시 출력:**
```
--no western features, caucasian skin, blonde hair, blue eyes, cake on table
```

---

### 5. Multi-Reference 라벨링

복수 이미지 사용 시 반드시:

```
**[Image 1: COMPOSITION]** [URL]
**[Image 2: CHARACTER FACE]** [URL]

**From Image 1**: Copy exact [visual_forensic 필드들]
**From Image 2**: Copy [korean_adaptation.child 필드들]
```

---

## ✅ 변환 체크리스트

- [ ] all_people 전원 한국인으로 명시됐는가?
- [ ] 흐릿한 배경 인물도 "한국인 피부톤" 포함?
- [ ] clothing_color 원본 유지 명시?
- [ ] error_prevention → --no 변환 완료?
- [ ] 도구별 올바른 형식 사용?
