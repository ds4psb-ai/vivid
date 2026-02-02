# AI 숏폼 영상 제작 워크플로우

## Step 1: 아이디어 구체화 (5분)

**무엇을 만들 것인가?**

1. 핵심 메시지 1줄로 정리
2. 타겟 감정: 놀람? 공감? 영감?
3. 레퍼런스 영상 1-2개 수집 → `assets/references/`

**예시:**
```
메시지: "새벽 3시, 창업가의 외로운 코딩"
감정: 공감 + 약간의 멋있음
레퍼런스: 기존 인기 Shorts
```

---

## Step 2: Mixboard로 비주얼 설계 (15분)

### 접속
→ [Google Mixboard](https://mixboard.google.com)

### 사용법

1. **프롬프트 입력**
   ```
   Korean male startup founder, 30s, coding alone
   in a Seoul cafe at 3AM, warm laptop glow,
   rain outside, cyberpunk aesthetic, cinematic
   ```

2. **Explore 클릭** → 20개 변형 자동 생성

3. **최고 3개 선택** → 각각 **Expand**로 확장

4. **Refine**으로 디테일 조정
   - 조명 더 따뜻하게
   - 비 이펙트 추가
   - 색감 조정

5. **최종 이미지 다운로드** → `assets/mixboard/`

### 장면 구성 (30초 기준)
- Scene 1 (0-8초): Hook - 시선 끄는 장면
- Scene 2 (8-18초): Build - 스토리 전개
- Scene 3 (18-25초): Peak - 클라이맥스
- Scene 4 (25-30초): Close - 마무리

---

## Step 3: Gemini로 영상 생성 (20분)

### 접속
→ [Gemini](https://gemini.google.com) (Veo 3 활성화)

### 프롬프트 템플릿

```markdown
## 요청: 30초 시네마틱 숏폼 영상

### 첨부 이미지
[Mixboard에서 만든 이미지 업로드]

### 스타일
- 시네마틱 4K 퀄리티
- 부드러운 카메라 무브먼트
- 감성적인 조명
- 9:16 세로 영상

### 장면 구성
Scene 1 (0-8초): [Hook 설명]
Scene 2 (8-18초): [Build 설명]
Scene 3 (18-25초): [Peak 설명]
Scene 4 (25-30초): [Close 설명]

### 음악 분위기
Lo-fi, 잔잔한 피아노, 약간 쓸쓸한

### 절대 하지 말 것
- 텍스트 오버레이
- 급격한 장면 전환
- 인위적인 표정
```

### 리파인 팁

생성 후 마음에 안 들면:
- "좀 더 천천히 움직여줘"
- "조명을 더 따뜻하게"
- "카메라 앵글을 약간 위에서"
- "표정을 더 자연스럽게"

---

## Step 4: Kling Canvas로 보완 (선택)

Gemini 결과가 부족하면 Kling 사용:

### 이미지 → 영상
1. Mixboard 이미지 업로드
2. Motion 추가 (subtle pan, zoom)
3. 5초 클립 여러 개 생성
4. 별도로 편집

### Multi-Shot Expansion
1. 기본 장면 1개 생성
2. Canvas Agent로 앵글 5개 자동 생성
3. 최고 앵글 선택

---

## Step 5: 프로젝트 저장

```
projects/[project-name]/
├── brief.md          # 콘셉트 기록
├── storyboard/
│   ├── scene1.png
│   ├── scene2.png
│   └── ...
└── output/
    ├── final_v1.mp4
    └── final_v2.mp4
```

### brief.md 템플릿
```markdown
# [프로젝트명]

## 콘셉트
- 핵심 메시지:
- 타겟 감정:
- 길이: 30초

## 장면 구성
1. Hook:
2. Build:
3. Peak:
4. Close:

## 사용 프롬프트
[여기에 실제 사용한 프롬프트 기록]

## 결과
- 버전:
- 만족도:
- 개선점:
```

---

## 💡 퀄리티 팁

1. **Mixboard에서 충분히 시간 써라**
   - 이미지 퀄리티 = 영상 퀄리티
   - 20개 변형 중 진짜 좋은 거 1개만 쓴다

2. **프롬프트는 구체적으로**
   - ❌ "멋있게"
   - ✅ "새벽 3시 카페, 노트북 화면 빛만 비추는, 비 내리는 창가"

3. **한 번에 완벽을 기대하지 마라**
   - 3-5번 리파인은 기본
   - 각 버전 저장해두기

4. **레퍼런스 많이 봐라**
   - YouTube Shorts 트렌드
   - Pinterest 무드보드
   - 좋은 영상 캡처해서 `references/`에 저장
