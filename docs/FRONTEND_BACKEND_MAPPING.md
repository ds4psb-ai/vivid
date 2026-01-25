# Frontend-Backend Mapping Document

> 전수조사 결과: 모든 Dimension Panel UI 버튼 → 백엔드 API 매핑
> **Last Updated**: 2026-01-25

---

## Summary

| 항목 | 수량 |
|------|------|
| Frontend Panels | 15개 |
| Backend Endpoints (Active) | 60+ |
| API Client 방식 | 2가지 (direct fetch, mirrorApi) |
| 검증 결과 | ✅ 모든 UI 버튼 정상 연결 |

---

## Panel-Endpoint 매핑 상세

### 1. PromptGeneratorPanel (1D)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Generate Prompt | `POST /api/dimension/1d/generate` | ✅ |

**Frontend**: `frontend/src/components/dimension/PromptGeneratorPanel.tsx:247`
**Backend**: `backend/app/routers/dimension/classic.py:342`

---

### 2. ReferenceDecoderPanel (4D)

| 분석 모드 | UI 버튼 | Backend Endpoint | 상태 |
|-----------|---------|------------------|------|
| text | Analyze | `POST /api/dimension/4d/analyze` | ✅ |
| style | Extract Style | `POST /api/dimension/4d/extract-style` | ✅ |
| video | Analyze Video | `POST /api/dimension/4d/analyze-video` | ✅ |
| image | Analyze Image | `POST /api/dimension/4d/analyze-image` | ✅ |

**Frontend**: `frontend/src/components/dimension/ReferenceDecoderPanel.tsx`
- text: line 517-521
- style: line 540-544
- video: line 563-567
- image: line 586-590

**Backend**: `backend/app/routers/dimension/classic.py`
- /4d/analyze: line 778
- /4d/extract-style: line 926
- /4d/analyze-video: line 1012
- /4d/analyze-image: line 1105

---

### 3. VisualRealizerPanel (3D)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Generate | `POST /api/dimension/3d/generate` | ✅ |

**Backend**: `backend/app/routers/dimension/classic.py:686`

---

### 4. StoryboardPanel (2D)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Create Storyboard | `POST /api/dimension/2d/create` | ✅ |

**Backend**: `backend/app/routers/dimension/classic.py:592`

---

### 5. VeoVideoPanel (VEO)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Generate Video | `POST /api/dimension/veo/generate/stream` | ✅ |

**Backend**: `backend/app/routers/dimension/veo.py:261` (non-stream)
**Backend**: `backend/app/routers/dimension/veo.py:336` (stream)

---

### 6. KlingPanel (KLING)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Generate Video | `POST /api/dimension/kling/generate` | ✅ |

**Backend**: `backend/app/routers/dimension/kling.py:434`

---

### 7. SunoPanel (SUNO)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Generate Music | `POST /api/dimension/suno/generate` | ✅ |

**Backend**: `backend/app/routers/dimension/suno.py:343`

---

### 8. QualityDirectorPanel (QC)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Quality Check | `POST /api/dimension/quality/check` | ✅ |

**Backend**: `backend/app/routers/dimension/quality.py:415`

---

### 9. CreativeEditorPanel

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Edit | `POST /api/dimension/quality/editor` | ✅ |

**Backend**: `backend/app/routers/dimension/quality.py:583`

---

### 10. StoryArchitectPanel (Story)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Generate Scenario | `POST /api/dimension/story/architect` | ✅ |
| Refine Story | `POST /api/dimension/story/refine` | ✅ |

**Backend**: `backend/app/routers/dimension/story.py:235` (architect)
**Backend**: `backend/app/routers/dimension/story.py:351` (refine)

---

### 11. SoundCrafterPanel (Sound)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Create Moodboard | `POST /api/dimension/sound/moodboard` | ✅ |
| Craft Sound | `POST /api/dimension/sound/craft` | ✅ |

**Backend**: `backend/app/routers/dimension/sound.py:428` (moodboard)
**Backend**: `backend/app/routers/dimension/sound.py:260` (craft)

---

### 12. PromptAlchemyPanel (Prompt)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Translate | `POST /api/dimension/prompt/translate` | ✅ |
| Batch Translate | `POST /api/dimension/prompt/translate/batch` | ✅ |

**Backend**: `backend/app/routers/dimension/prompt.py:462` (translate)
**Backend**: `backend/app/routers/dimension/prompt.py:654` (batch)

---

### 13. AestheticDirectorPanel (AD)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Direct | `POST /api/dimension/aesthetic/direct` | ✅ |

**Backend**: `backend/app/routers/dimension/aesthetic.py:293`

---

### 14. CharacterConsistencyPanel (Character)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Create Character | `POST /api/dimension/character/create` | ✅ |
| Get Character | `GET /api/dimension/character/{id}` | ✅ |
| Delete Character | `DELETE /api/dimension/character/{id}` | ✅ |
| List Characters | `GET /api/dimension/character/list` | ✅ |
| Add Reference | `POST /api/dimension/character/{id}/add-reference` | ✅ |
| Upload Reference | `POST /api/dimension/character/{id}/upload-reference` | ✅ |

**Backend**: `backend/app/routers/dimension/character.py`

---

### 15. AbyssMirrorPanel (Mirror/AI)

| UI 버튼 | Backend Endpoint | 상태 |
|---------|------------------|------|
| Start Analysis | `POST /api/dimension/mirror/init` | ✅ |
| Send Message | `POST /api/dimension/mirror/chat` | ✅ |
| (Streaming) | `POST /api/dimension/mirror/chat/stream` | ✅ |

**Frontend**: `frontend/src/lib/mirrorApi.ts`
- initMirror: line 94-127
- chatMirror: line 129-156
- chatMirrorStream: line 182-254

**Backend**: `backend/app/routers/dimension/mirror.py`
- /mirror/init: line 561
- /mirror/chat: line 692
- /mirror/chat/stream: line 837

---

## 미사용 Backend Endpoints (참고용)

다음 엔드포인트들은 백엔드에 구현되어 있지만 프론트엔드에서 현재 사용하지 않음.
향후 기능 확장 또는 정리 시 참고.

### classic.py
| Endpoint | 설명 |
|----------|------|
| `POST /1d/multi-generate` | 다중 프롬프트 생성 |
| `POST /1d/multi-generate/stream` | 다중 프롬프트 스트리밍 |

### storyboard.py
| Endpoint | 설명 |
|----------|------|
| `POST /storyboard/refine` | 스토리보드 수정 |
| `POST /storyboard/export` | 스토리보드 내보내기 |
| `POST /storyboard/consistency/check` | 일관성 검사 |

### aesthetic.py
| Endpoint | 설명 |
|----------|------|
| `POST /aesthetic/moodboard` | 무드보드 생성 |
| `POST /aesthetic/character-dna` | 캐릭터 DNA |
| `POST /persona/analyze` | 페르소나 분석 |

### story.py
| Endpoint | 설명 |
|----------|------|
| `POST /story/shot-list` | 샷 리스트 생성 |

### sound.py
| Endpoint | 설명 |
|----------|------|
| `POST /sound/lyrics` | 가사 생성 |

### suno.py / kling.py
| Endpoint | 설명 |
|----------|------|
| `GET /suno/pricing` | Suno 가격 정보 |
| `GET /kling/pricing` | Kling 가격 정보 |

### prompt.py
| Endpoint | 설명 |
|----------|------|
| `GET /prompt/platforms` | 플랫폼 목록 |

---

## API Client 패턴

### 패턴 1: Direct Fetch (대부분의 패널)

```typescript
// useAsyncOperation hook + fetch
const { execute } = useAsyncOperation<Response>({...});
await execute(
  `${API_BASE}/api/dimension/1d/generate`,
  { topic, style, mood },
  getBYOKHeaders(byokKey)
);
```

### 패턴 2: 전용 API 모듈 (AbyssMirrorPanel)

```typescript
// mirrorApi.ts 사용
import { initMirror, chatMirror } from '@/lib/mirrorApi';

const response = await initMirror(request, byokKey);
const chatResponse = await chatMirror(chatRequest, byokKey);
```

---

## 검증 방법

```bash
# Frontend 빌드 확인
cd frontend && npm run build

# Backend 라우터 확인
cd backend && python -c "from app.main import app; print([r.path for r in app.routes])"
```

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-01-25 | 초기 전수조사 완료 |
