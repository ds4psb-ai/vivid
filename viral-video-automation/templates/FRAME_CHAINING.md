# 🔗 Frame-to-Frame Chaining Guide

> **Purpose**: 영상 클립 간 끊김 없는 전환
> **Version**: 2026 (Kling / Sora / Pika 공통)

---

## 🎯 왜 필요한가?

### 문제

```
Scene 1 마지막 프레임: 아이가 왼쪽을 보고 있음
Scene 2 첫 프레임: 아이가 정면을 보고 있음
→ 편집 시 눈에 띄는 점프컷!
```

### 해결

```
Scene 1 마지막 프레임 추출 → Scene 2 첫 프레임으로 사용
→ 자연스러운 연결!
```

---

## 🔧 워크플로우

```
Step 1: Scene N 영상 생성
        ↓
Step 2: 마지막 프레임 추출
        ↓
Step 3: Scene N+1의 Reference로 사용
        ↓
Step 4: 반복
```

---

## 📋 프레임 추출 방법

### FFmpeg (권장)

```bash
# 마지막 프레임 추출
ffmpeg -sseof -0.1 -i scene01.mp4 -vframes 1 scene01_last.png

# 또는 정확한 시간 지정
ffmpeg -i scene01.mp4 -ss 00:04.90 -vframes 1 scene01_last.png
```

### Kling 내장

```
1. 생성된 영상 다운로드
2. 편집 도구에서 마지막 프레임 캡처
3. 다음 씬 생성 시 Reference로 업로드
```

---

## 📝 프롬프트 패턴

### Scene N+1 시작 프롬프트

```
Reference: [scene_N_last.png 첨부]

Continue from this exact frame.
Maintain same:
- Character position
- Lighting
- Camera angle

Beat Timing:
- 0.0–0.5s: [다음 동작 시작]
- 0.5–end: [동작 완료]
```

### 핵심 키워드

```
✅ "Continue from this exact frame"
✅ "Maintain same position"
✅ "Seamless transition"

❌ "Start fresh"
❌ "New scene"
```

---

## 🎬 씬 타입별 적용

### 연속 동작 (Clapping → Blow)

```
Scene 4 (Clapping) 마지막: 박수 중
Scene 5 (Transition): 박수 → 촛불 보기
Scene 6 (Blow): 촛불 끄기

Chain: scene04_last → scene05 → scene05_last → scene06
```

### 점프컷 (Glitch)

```
Scene 7 (과거) 마지막: 촛불 꺼진 직후
Scene 8 (Glitch): 의도적 단절
→ Chaining 불필요, 의도된 점프
```

### 감정 전환 (Isolation)

```
Scene 8 (Glitch) 마지막: 현재 케이크
Scene 9 (Isolation) 첫: 같은 케이크, 다른 조명
→ 케이크 위치 유지, 조명만 변경
```

---

## ✅ Chaining 체크리스트

생성 전:
- [ ] 이전 씬 마지막 프레임 추출
- [ ] Reference로 첨부
- [ ] "Continue from" 키워드 포함

생성 후:
- [ ] 첫 프레임이 이전 마지막과 연결되는지 확인
- [ ] 점프/워핑 없는지 확인
- [ ] 조명 연속성 확인

---

## 💡 팁

1. **마지막 0.5초는 버릴 수 있음** - AI 영상 끝이 불안정할 때
2. **편집 트랜지션 활용** - Dissolve로 작은 불일치 가리기
3. **의도적 점프컷도 OK** - Glitch 씬처럼 의도된 경우
4. **오디오로 커버** - 사운드 연결이 시각 불일치 가림

---

## 🚨 흔한 문제

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 캐릭터 위치 이동 | Reference 누락 | 마지막 프레임 첨부 |
| 조명 급변 | Kelvin 미지정 | 동일 색온도 명시 |
| 의상 변경 | 일관성 누락 | Multi-Entity 적용 |
| 카메라 점프 | 앵글 미지정 | "Same angle" 추가 |
