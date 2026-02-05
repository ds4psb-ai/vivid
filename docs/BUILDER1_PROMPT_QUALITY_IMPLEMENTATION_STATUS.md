# 통합 빌더 프롬프트 품질 개선 - 구현 상태

## ✅ Phase 1: constants.ts 시스템 프롬프트 개선 (완료)

### Task #1: 듀얼 레퍼런스 패턴 강화 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 207-237

**구현 내용**:
```markdown
**[Image 1: COMPOSITION]** [scene_XX.png]
**[Image 2: CHARACTER FACE]** [MALE_ANCHOR.png 또는 FEMALE_ANCHOR.png]

**From Image 1**: Copy exact composition, lighting, camera angle, character positions.
**From Image 2**: Copy the [타겟 문화권] [character]'s face (hair, eyes, expression).

⚠️ CRITICAL: 아래 프롬프트는 **변경사항만** 기술하세요.
레퍼런스에 이미 있는 요소(구도, 조명, 카메라 앵글 등)를 다시 기술하지 마세요.
```

**효과**:
- AI가 레퍼런스와 변경점을 명확히 구분
- 중복 기술로 인한 AI 혼란 방지
- "Copy exact..." 명시로 구도 유지 강화

---

### Task #2: 캐릭터 프로필 템플릿 세부화 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 141-165

**구현 내용**:
```markdown
👨 MALE ANCHOR (Scene XX: [제목]):
  나이: [씬에서 추출된 나이대]
  얼굴 특징:
    - 한국: "black hair, monolid/single eyelids, warm skin tone, natural Korean features"
    - 일본: "straight black hair, soft features, pale skin, delicate jawline"
    - 서양: "varied hair color, double eyelids, Caucasian features"
  헤어스타일: [구체적 스타일 - e.g., "1990s Korean bowl cut", "side-parted business cut"]
  표정: [기본 표정 - e.g., "shy gentle smile (lips closed)", "confident grin"]
  체형: [필요시 - e.g., "slim build", "athletic"]
  의상: [색상, 질감, 스타일 - e.g., "청자켓 (denim jacket), 흰 티셔츠"]
  특징: [고유 특징 - e.g., "손에 붉은 장미 꽃다발"]

⚠️ 각 요소를 **구체적으로** 기술하세요. "한국 남성"만으로는 불충분합니다.
```

**효과**:
- 캐릭터 일관성 극대화
- 디테일 부족 문제 해결
- 문화권별 구체적 가이드 제공

---

### Task #3: 배경 문화권 변환 규칙 명시화 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 122-145

**구현 내용**:
```markdown
| 문화권 | --no 기본값 | 배경 변환 규칙 | 캐릭터 스타일 |
|--------|------------|---------------|--------------|
| 한국/Korean | western features, caucasian skin, blonde hair, blue eyes, double eyelids (unless specified) | "미국 주택" → "1990s Korean apartment, warm tungsten lighting" | Korean, black hair, monolid eyes, warm skin |
| 일본/Japanese | western features, caucasian skin, korean style | "suburban house" → "Japanese home, tatami, shoji screens" | Japanese, straight black hair, soft features |

⚠️ 배경 변환 규칙:
- 원본 영상의 배경이 "미국 교외 주택"이면 → "[타겟 문화권] 주거 환경"으로 자동 변환
- 예: "suburban house with lawn" → "1990s Korean apartment building, narrow street"
- 시대감 유지: 원본이 90s면 → 타겟도 90s 스타일
```

**효과**:
- 배경 문화권 변환 자동화
- 시대감 일관성 유지
- 명확한 변환 규칙 제공

---

### Task #4: 씬별 --no 동적 생성 규칙 강화 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 253-274

**구현 내용**:
```markdown
씬별 --no 동적 생성 규칙 (문화권 기본값에 추가):

1. **오브젝트 상태**:
   - 손에 들고 있음 → --no [오브젝트] on table/floor
   - 케이크 들고 있음 → --no cake on table
   - 꽃다발 들고 있음 → --no flowers on ground

2. **캐릭터 상태**:
   - 눈 뜬 상태 → --no eyes closed
   - 입 다문 상태 → --no mouth open, speaking
   - 정면 응시 → --no looking away, profile view

3. **동작 상태**:
   - 숨 들이쉬는 중 → --no blowing, exhaling
   - 박수 중 → --no static hands, hands down
   - 걷는 중 → --no standing still, sitting

4. **Visual Rhyme Phase**:
   - Phase 1-2 (과거/빈티지) → --no modern objects, LED lighting, smartphones, flat colors
   - Phase 3-4 (현재/사실) → --no vintage, film grain, warm colors, nostalgia

⚠️ 각 씬마다 씬 설명을 분석하여 해당되는 모든 --no를 추가하세요.
```

**효과**:
- AI 환각 최소화
- 씬 상태 정확도 향상
- 포괄적인 --no 규칙 제공

---

### Task #5: MJ V7 파라미터 전환 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 239-265, 601-611

**구현 내용**:
```markdown
Midjourney V7 파라미터 (2026 Best Practices):

기본 구조:
--iw 2.0 --ar 9:16 --v 7 --style raw
--oref [ANCHOR_URL]  (V7에서 --cref 대체)
--ow [동적]          (V7에서 --cw 대체)
--stylize [동적]
--no [문화권 기본값], [씬별 동적]

--ow (omni-weight) 동적 결정 (V7 기준, 0-1000):
- 앵커 씬 본인: --oref 없음
- 클로즈업 (얼굴 중심): --ow 400-600 (얼굴/의상 강력 보존)
- 미디엄 샷 (상반신): --ow 200-300 (밸런스)
- 와이드 샷 (전신): --ow 100-150 (구도 우선)
- 배경만 (인물 없음): --oref 생략

⚠️ V7에서는 --cref → --oref, --cw → --ow로 전환되었습니다.
```

**효과**:
- 2026년 MJ V7 표준 적용
- 캐릭터 일관성 향상
- 샷 타입별 최적 --ow 값 제공

---

### Task #6: Veo 3.1 프롬프트 패턴 개선 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 389-423

**구현 내용**:
```markdown
Veo 3.1 프롬프트 구조 (2026 Best Practices):

⚠️ CRITICAL: 레퍼런스 이미지가 있으면 프롬프트는 **간결하게**!
레퍼런스 이미지가 이미 구도, 조명, 인물 외모를 정의하므로 중복 기술 불필요.

프롬프트는 다음만 집중:
1. Cinematography: [카메라 무브먼트 - dolly, tracking, crane, POV 등]
2. Subject: [레퍼런스에 없는 변경사항만]
3. Action: [명확한 단일 동작 - "within first second" 타이밍 명시]

예시 (레퍼런스 이미지 사용 시):
Cinematography: Static medium shot, slight handheld movement
Subject: Same character (레퍼런스 참조)
Action: Looking around nervously, then fixes gaze to the right, within first second

⚠️ 레퍼런스 이미지에 이미 있는 요소(구도, 조명, 인물 외모)를 프롬프트에 다시 기술하지 마세요.
```

**효과**:
- Veo 3.1 레퍼런스 활용 최적화
- 프롬프트 간결화
- 중복 제거로 AI 혼란 방지

---

### Task #7: Kling Motion Control 패턴 적용 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 362-395

**구현 내용**:
```markdown
Kling 3.0 Beat System (2026 Motion Control Best Practices):

⚠️ CRITICAL: 레퍼런스 이미지 기반 생성 시 모션을 프롬프트에 기술하지 마세요!
레퍼런스 이미지가 이미 캐릭터 포즈와 동작을 정의합니다.

프롬프트는 다음만 집중:
1. 캐릭터 외모 (레퍼런스와의 변경점)
2. 환경/배경 (문화권 변환)
3. 조명/분위기

⚠️ 레퍼런스 이미지 사용 시:
- 프롬프트: "Character in denim jacket (레퍼런스 참조). Korean style apartment background."
- 모션 기술 금지: ❌ "walking forward", "turning head" 등 제거
```

**효과**:
- Kling 2.6/3.0 레퍼런스 기반 생성 최적화
- 모션 기술 중복 제거
- 캐릭터 외모와 환경에만 집중

---

### Task #11: 앵커 이미지 섹션 강화 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 519-543

**구현 내용**:
```markdown
### 👨 MALE ANCHOR (Scene XX: [제목])

**[Image 1: COMPOSITION]** [scene_XX.png]

⚠️ 이 씬은 앵커 씬입니다. --oref 없이 먼저 생성하세요.
생성된 이미지 URL을 복사하여 다른 씬의 --oref에 사용합니다.

[📋 COPY] NanoBanana Pro:
[상세한 한글 프롬프트 - STEP 1의 캐릭터 프로필 기반]
- 나이: [나이대]
- 얼굴: [구체적 특징 - e.g., "검은 단발머리(90년대 한국 스타일), 쌍꺼풀 없는 눈, 수줍은 미소(입 다문 채)"]
- 의상: [세부사항]
- 배경: [문화권 변환 적용 - e.g., "1990s 한국 아파트, 따뜻한 백열등 조명"]

[📋 COPY] Midjourney V7 (앵커용 - --oref 없음):
[영문 프롬프트 - 한글 프롬프트와 동일 내용]
--iw 2.0 --ar 9:16 --v 7 --style raw --stylize [동적]
--no [문화권 기본값], [씬별 동적]

💾 **생성 후**: 이미지 URL을 복사 → 아래 모든 씬의 [ANCHOR_URL]에 붙여넣기
```

**효과**:
- 앵커 생성 프로세스 명확화
- URL 복사 가이드 제공
- STEP 1 캐릭터 프로필과 연동

---

### Task #12: 씬별 프롬프트 템플릿 개선 ✅
**파일**: `viral-video-automation/builder1-temp/constants.ts`
**위치**: lines 546-628

**구현 내용**:
```markdown
## 📍 Scene 01: [제목]
**타임코드:** 00:00.00~00:01.67
**레퍼런스**: scene_01.png
**캐릭터**: 👨 MALE (ANCHOR 참조)

### 🖼️ IMAGE

**[Image 1: COMPOSITION]** [scene_01.png]
**[Image 2: CHARACTER FACE]** [MALE_ANCHOR.png 또는 입력한 ANCHOR URL]

**From Image 1**: Copy exact composition, lighting, camera angle, character positions.
**From Image 2**: Copy the Korean man's face (hair style, eyes, expression).

⚠️ 아래 프롬프트는 **변경사항만** 기술합니다.

[📋 COPY] NanoBanana Pro:
[변경사항 중심 한글 프롬프트]
- 인물: [ANCHOR와의 차이점만 - e.g., "걷는 동작", "한 손에 장미 꽃다발"]
- 배경: [COMPOSITION과의 차이점만 - e.g., "배경은 1990s 한국 주택가로 변환"]
- 분위기: [추가 요소만]

[📋 COPY] Midjourney V7:
[변경사항 중심 영문 프롬프트]
--iw 2.0 --ar 9:16 --v 7 --style raw
--oref [MALE_ANCHOR_URL] --ow [120-400 동적]
--stylize [동적]
--no [문화권 기본값], [씬별 동적]

### 🎥 MOTION

⚠️ 레퍼런스 이미지 사용 시 모션을 프롬프트에 기술하지 마세요.

[📋 COPY] Kling 3.0:
[캐릭터 외모 + 환경만]
- Character: Same as Image (Korean man in denim jacket)
- Environment: 1990s Korean suburban street

[📋 COPY] Veo 3.1:
Cinematography: Static wide shot, symmetrical composition
Subject: Same character (레퍼런스 참조)
Action: Walking steadily towards camera, within first second
Setting: 1990s Korean suburban street (문화권 변환)
Audio: "Ambient: suburban nature sounds. SFX: footsteps."

| Camera | Motion Score | Duration |
|--------|-------------|----------|
| Static | 5 (Walking) | ~2s |
```

**효과**:
- 레퍼런스 활용 최적화
- 중복 제거, 변경점 명확화
- 2026 Best Practices 적용

---

## 📦 Phase 1 빌드 결과

```bash
$ cd /Users/ted/vivid/viral-video-automation/builder1-temp && npm run build
✓ 1715 modules transformed.
✓ built in 806ms
```

**상태**: ✅ 성공
**파일 크기**: 520.59 kB (gzip: 133.26 kB)

---

## 🔧 Phase 2: Academy 파서 패치 (구현 대기)

다음 작업들은 더 복잡한 UI 통합이 필요하며, 별도 구현이 권장됩니다:

### Task #8: 키프레임 레퍼런스 자동 참조 UI
**파일**: `frontend/src/app/academy/page.tsx`
**예상 위치**: lines 400-500

**구현 가이드**:
1. 키프레임 업로드 UI 추가 (각 씬별 파일 업로드)
2. 업로드된 이미지를 클라우드에 업로드하여 URL 생성
3. 프롬프트에 자동으로 `[scene_XX.png]` 참조 추가
4. "From Image 1" 지시어 자동 삽입

**UI 스케치**:
```tsx
// 새로운 상태 추가
const [uploadedKeyframes, setUploadedKeyframes] = useState<{[sceneId: string]: File}>({});

// 키프레임 업로드 섹션
<div className="mb-6 p-4 border rounded">
  <h3>키프레임 이미지 업로드 (선택)</h3>
  <p className="text-sm text-gray-600 mb-2">
    각 씬의 추출된 이미지를 업로드하면 프롬프트에 자동 참조됩니다.
  </p>
  {parsedScenes.map(scene => (
    <div key={scene.id} className="flex items-center gap-2 mb-2">
      <label>Scene {scene.number}:</label>
      <input
        type="file"
        accept="image/*"
        onChange={(e) => handleKeyframeUpload(scene.id, e.target.files?.[0])}
      />
      {uploadedKeyframes[scene.id] && (
        <span className="text-green-600">✓ {uploadedKeyframes[scene.id].name}</span>
      )}
    </div>
  ))}
</div>
```

---

### Task #9: 앵커 이미지 URL 입력 UI
**파일**: `frontend/src/app/academy/page.tsx`
**예상 위치**: lines 500-600

**구현 가이드**:
1. 앵커 URL 입력 필드 추가 (MALE, FEMALE)
2. "앵커 URL 적용" 버튼 클릭 시 모든 씬에 --oref 자동 추가
3. 샷 타입 기반 --ow 값 자동 계산 (클로즈업: 400-600, 미디엄: 200-300, 와이드: 100-150)

**UI 스케치**:
```tsx
// 앵커 URL 상태
const [anchorUrls, setAnchorUrls] = useState<{
  male: string;
  female: string;
}>({ male: '', female: '' });

// 앵커 URL 입력 섹션
<div className="bg-yellow-50 border border-yellow-200 p-4 rounded mb-4">
  <h4 className="font-bold mb-2">⭐ 앵커 이미지 URL 입력</h4>

  {anchorScenes.male && (
    <div className="mb-2">
      <label className="block text-sm font-medium mb-1">👨 MALE ANCHOR URL:</label>
      <input
        type="text"
        placeholder="https://..."
        value={anchorUrls.male}
        onChange={(e) => setAnchorUrls({...anchorUrls, male: e.target.value})}
        className="w-full px-3 py-2 border rounded"
      />
    </div>
  )}

  <button
    onClick={() => applyAnchorUrls(anchorUrls)}
    className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
  >
    앵커 URL 적용
  </button>
</div>
```

**자동 적용 로직**:
```typescript
function applyAnchorUrls(urls: {male: string; female: string}) {
  const updatedScenes = parsedScenes.map(scene => {
    if (scene.isAnchor) return scene;

    let orefValue = '';
    if (scene.characters.includes('male') && urls.male) {
      orefValue += `--oref ${urls.male} `;
    }

    // --ow 값 결정 (샷 타입 기반)
    let owValue = '';
    if (scene.shotType === 'close-up') owValue = '--ow 400';
    else if (scene.shotType === 'medium') owValue = '--ow 250';
    else if (scene.shotType === 'wide') owValue = '--ow 120';

    scene.imagePrompts.midjourney = scene.imagePrompts.midjourney.replace(
      /--iw 2\.0/,
      `--iw 2.0 ${orefValue}${owValue}`
    );

    return scene;
  });

  setParsedScenes(updatedScenes);
}
```

---

### Task #10: 파싱 후 프롬프트 자동 보강
**파일**: `frontend/src/app/academy/page.tsx`
**예상 위치**: lines 300-350

**구현 가이드**:
1. 파싱된 프롬프트에서 레퍼런스 중복 기술 제거
2. "same composition", "exact lighting" 등 제거
3. 레퍼런스 이미지가 있으면 "변경사항만" 남김

**자동 클린업 함수**:
```typescript
function removeRedundantDescriptions(prompt: string, hasReference: boolean): string {
  if (!hasReference) return prompt;

  const redundantPatterns = [
    /구도.*유지/gi,
    /same composition/gi,
    /exact.*lighting/gi,
    /camera angle/gi,
  ];

  let cleaned = prompt;
  redundantPatterns.forEach(pattern => {
    cleaned = cleaned.replace(pattern, '');
  });

  return cleaned.trim();
}

// 파싱 후 적용
parsedScenes.forEach(scene => {
  const hasReference = uploadedKeyframes[scene.id] !== undefined;
  scene.imagePrompts.nanobanana = removeRedundantDescriptions(
    scene.imagePrompts.nanobanana,
    hasReference
  );
});
```

---

## 📊 구현 완료 요약

| Phase | Task | 상태 | 파일 |
|-------|------|------|------|
| **Phase 1** | **constants.ts 개선** | ✅ **완료** | `builder1-temp/constants.ts` |
| 1.1 | 듀얼 레퍼런스 패턴 강화 | ✅ | lines 207-237 |
| 1.2 | 캐릭터 프로필 템플릿 세부화 | ✅ | lines 141-165 |
| 1.3 | 배경 문화권 변환 규칙 명시화 | ✅ | lines 122-145 |
| 1.4 | 씬별 --no 동적 생성 규칙 강화 | ✅ | lines 253-274 |
| 1.5 | MJ V7 파라미터 전환 | ✅ | lines 239-265, 601-611 |
| 1.6 | Veo 3.1 프롬프트 패턴 개선 | ✅ | lines 389-423 |
| 1.7 | Kling Motion Control 패턴 적용 | ✅ | lines 362-395 |
| 1.11 | 앵커 이미지 섹션 강화 | ✅ | lines 519-543 |
| 1.12 | 씬별 프롬프트 템플릿 개선 | ✅ | lines 546-628 |
| **Phase 2** | **Academy 파서 패치** | 📝 **가이드 작성 완료** | `frontend/src/app/academy/page.tsx` |
| 2.1 | 키프레임 레퍼런스 자동 참조 UI | 📝 | 구현 가이드 제공 |
| 2.2 | 앵커 이미지 URL 입력 UI | 📝 | 구현 가이드 제공 |
| 2.3 | 파싱 후 프롬프트 자동 보강 | 📝 | 구현 가이드 제공 |

---

## 🎯 핵심 개선 사항

### 1. 레거시 수준 프롬프트 품질 복원
- ✅ 듀얼 레퍼런스 명확화 ("From Image 1", "From Image 2")
- ✅ 디테일한 캐릭터 묘사 (헤어스타일, 얼굴, 표정, 의상)
- ✅ 배경 문화권 변환 자동화
- ✅ 강력한 --no 규칙

### 2. 2026년 Best Practices 적용
- ✅ **Veo 3.1**: 레퍼런스 이미지 사용 시 프롬프트 간결화
- ✅ **Kling 2.6/3.0**: Motion Control 패턴 (모션 기술 제거)
- ✅ **MJ V7**: --oref, --ow 파라미터 전환
- ✅ **NanoBanana Pro**: 한국어 6요소 구조

### 3. 중복 제거 및 명확화
- ✅ "변경사항만 기술" 지시어 추가
- ✅ 레퍼런스 요소 재기술 금지
- ✅ AI 환각 방지 --no 규칙 강화

---

## 📚 참고 자료

- [Veo 3.1 Ultimate Guide](https://cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1)
- [Veo 3.1 Ingredients to Video](https://blog.google/innovation-and-ai/technology/ai/veo-3-1-ingredients-to-video/)
- [Kling 2.6 Motion Control Guide](https://higgsfield.ai/blog/Kling-2-6-Motion-Control-Full-Guide)
- [MJ V7 Omni-Reference](https://updates.midjourney.com/omni-reference-oref/)
- [NanoBanana Pro Prompting Tips](https://blog.google/products/gemini/prompting-tips-nano-banana-pro/)

---

## 🚀 다음 단계

### 즉시 사용 가능
Phase 1의 모든 개선사항이 `builder1-temp` 빌드에 적용되었습니다:
```bash
cd /Users/ted/vivid/viral-video-automation/builder1-temp
npm run dev
```

### Phase 2 구현 시
위의 구현 가이드를 참고하여 `frontend/src/app/academy/page.tsx`에 UI 추가:
1. 키프레임 업로드 섹션
2. 앵커 URL 입력 섹션
3. 자동 프롬프트 보강 로직

---

## 📝 테스트 시나리오

### 빌더1 테스트
1. 영상 업로드 + 씬 테이블 입력
2. 오마주 스타일: "한국인 20대 커플" 입력
3. STEP 1-4 진행
4. 생성된 워크플로우 검증:
   - [ ] 듀얼 레퍼런스 라벨 확인
   - [ ] "From Image 1", "From Image 2" 명시 확인
   - [ ] 캐릭터 디테일 충분한지 확인 (헤어, 얼굴, 표정)
   - [ ] 배경 문화권 변환 확인 ("미국 주택" → "한국 아파트")
   - [ ] --oref, --ow 파라미터 확인 (V7 표준)
   - [ ] --no 값 충분한지 확인

### 실제 생성 테스트
1. **NanoBanana Pro**: 생성된 한글 프롬프트로 이미지 생성, 레거시 vs 개선 버전 비교
2. **Midjourney V7**: 앵커 이미지 생성 (--oref 없이) → 앵커 URL 복사 → 다른 씬에 --oref 적용 → 캐릭터 일관성 평가
3. **Kling/Veo**: 생성된 이미지로 모션 생성 → 레퍼런스 기반 생성 품질 평가

---

## 예상 결과 비교

### Before (현재 빌더)
```markdown
## Scene 01: 설레는 발걸음

[📋 COPY] Midjourney V7:
A wide shot of a Korean man in his early 20s walking towards a suburban house...
--iw 2.0 --ar 9:16 --v 7 --cref [ANCHOR_URL] --cw 30
```

**문제**:
- 구도 유지 지시어 없음
- 캐릭터 디테일 부족 ("Korean man in his early 20s"만)
- 배경 변환 없음 ("suburban house" 그대로)

### After (개선 버전)
```markdown
## 📍 Scene 01: 설레는 발걸음

**[Image 1: COMPOSITION]** [scene_01.png]
**[Image 2: CHARACTER FACE]** [MALE_ANCHOR.png]

**From Image 1**: Copy exact composition, lighting, camera angle, character positions.
**From Image 2**: Copy the Korean man's face (black bowl cut, monolid eyes, shy smile).

[📋 COPY] NanoBanana Pro:
걷는 동작만 추가, 한 손에 붉은 장미 꽃다발. 배경은 1990s 한국 주택가로 변환.

[📋 COPY] Midjourney V7:
Walking towards camera, holding red roses.
--iw 2.0 --ar 9:16 --v 7 --style raw
--oref [MALE_ANCHOR_URL] --ow 120
--stylize 250
--no western features, caucasian skin, blonde hair, modern cars, running
```

**개선**:
- ✅ 듀얼 레퍼런스 명확화
- ✅ 변경점만 기술 (간결)
- ✅ 캐릭터 디테일 앵커에서 참조
- ✅ 배경 문화권 변환 명시
- ✅ V7 파라미터 적용 (--oref, --ow)
- ✅ 강력한 --no
