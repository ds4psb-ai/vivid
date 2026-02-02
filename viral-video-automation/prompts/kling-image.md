# Kling Canvas 이미지/영상 프롬프트

## 이미지 생성 (Image to Video 베이스용)

### 캐릭터 기본
```
Photorealistic portrait of Korean male in his 30s,
startup founder aesthetic, black casual shirt,
confident yet approachable expression,
soft studio lighting, clean background,
4K, high detail
```

### 환경 기본
```
Modern Seoul cafe interior, night time,
warm ambient lighting, rain visible through large windows,
minimalist design, cozy atmosphere,
cinematic composition, 4K
```

---

## 영상 생성 (Kling Video O1)

### 기본 세팅
- Duration: 5초 (연결해서 사용)
- Quality: High
- Aspect Ratio: 9:16
- Motion: Subtle

### 프롬프트 템플릿
```
[첨부 이미지 기반]
Gentle camera movement, slight push in,
subtle ambient motion (rain, steam, screen flicker),
cinematic color grading, smooth 24fps
```

### 모션 타입별

**정적 + 미세 움직임**
```
Static camera, subtle motion only:
- breathing movement
- gentle eye blink
- slight head tilt
- ambient elements moving
```

**슬로우 줌인**
```
Slow dolly in movement,
maintaining focus on subject,
background gradually blurs,
dreamlike transition
```

**패닝**
```
Slow horizontal pan left to right,
revealing environment gradually,
smooth continuous motion,
cinematic pacing
```

---

## Multi-Shot Expansion

Canvas Agent 프롬프트:
```
Generate 5 angle variations:
1. Close-up face, emotional focus
2. Medium shot, context visible
3. Wide shot, full environment
4. Side profile, dramatic lighting
5. Over shoulder, POV feeling

Maintain:
- Same character appearance
- Same lighting mood
- Same time of day
- Consistent color grade
```

---

## Elements 저장용 프롬프트

### 캐릭터 Element
```
[저장 이름: StartupFounder_Korean_V1]
Korean male, early 30s, startup founder,
black casual shirt, confident posture,
professional yet approachable,
consistent lighting setup
```

### 환경 Element
```
[저장 이름: SeoulCafe_Night_V1]
Seoul cafe, night time, rain outside,
warm interior lighting, minimalist design,
cyberpunk touches, Lo-fi atmosphere
```

---

## 퀄리티 팁

1. **이미지가 70%, 영상이 30%**
   - Mixboard/Kling 이미지 퀄리티가 중요
   - 좋은 베이스 이미지 = 자연스러운 모션

2. **모션은 최소화**
   - 과한 움직임 = 아티팩트 증가
   - 미세한 움직임이 더 자연스러움

3. **5초 클립으로 쪼개기**
   - 30초 한 번에 ❌
   - 5초 × 6개 → 편집 ✅

4. **Same Seed 활용**
   - 일관된 캐릭터/환경 유지
   - Elements 저장 적극 활용
