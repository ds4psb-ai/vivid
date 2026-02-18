# Preview 재생 실패 체인 Postmortem

> 2026-02-06 | Academy 영상 업로드 → 프리뷰 재생 실패

---

## 증상

영상 업로드 후 Chrome에서 프리뷰 영상이 재생되지 않음.
콘솔에 405 Method Not Allowed, DECODER_ERROR_NOT_SUPPORTED 등 복합 에러.

## 실패 체인

```
백엔드 preview_id를 메모리 dict에서만 조회
  → 멀티워커/재시작 시 dict 유실
    → HEAD /preview/{id} → 404
      → 프론트 HEAD 사전검사가 즉시 serverFailed=true
        → blob(HEVC 원본)으로 fallback
          → Chrome HEVC 디코딩 불가 → DECODER_ERROR_NOT_SUPPORTED
            → 영상 깨짐
```

## 노이즈 (재생 실패와 무관)

| 에러 | 원인 | 조치 |
|------|------|------|
| zustand deprecated default export | `@xyflow/react` 내부 + 외부 instrument.js | 무시 |
| 405 HEAD | CORS에 HEAD 미포함 + `@router.head` 누락 | 수정했지만 이것만으론 해결 안 됨 |

## 근본 원인 3개

### 1. 프론트: HEAD 사전검사가 조기 fallback 유발
- `DetectionResults.tsx`에 `useEffect`로 `HEAD /preview/{id}` 요청
- 404 한 번이면 즉시 `serverFailed=true` → blob fallback
- blob = HEVC 원본이므로 Chrome에서 깨짐

### 2. 백엔드: preview 조회가 인메모리 dict 전용
- `_preview_store: dict[str, tuple[str, float]]`에만 의존
- Railway 멀티워커, 재배포 시 dict 유실 → 항상 404

### 3. 코덱 현실
- Safari: HEVC 재생 가능 (하드웨어 디코더)
- Chrome: HEVC 취약 → `DECODER_ERROR_NOT_SUPPORTED`
- blob fallback = HEVC 원본 = Chrome 깨짐

## 수정 내역

### 프론트 (`DetectionResults.tsx`)
```diff
- useEffect(() => {
-   if (!serverVideoUrl || serverFailed) return;
-   fetch(serverVideoUrl, { method: "HEAD" })
-     .then((res) => { if (!res.ok) markServerFailed(); })
-     .catch(() => { markServerFailed(); });
- }, [serverVideoUrl, serverFailed, markServerFailed]);
```
- HEAD 사전검사 삭제 → 실제 `<video>` onError 때만 blob fallback

### 백엔드 (`scene_detect.py`)
```python
def _preview_file_path(preview_id: str) -> str:
    """deterministic temp path"""
    return os.path.join(tempfile.gettempdir(), f"preview_{preview_id}.mp4")

def _resolve_preview_path(preview_id: str) -> str | None:
    """1순위 메모리 store, 2순위 파일 경로 복구"""
    record = _preview_store.get(preview_id)
    if record:
        path, created_at = record
    else:
        path = _preview_file_path(preview_id)
        if not os.path.exists(path):
            return None
        created_at = os.path.getmtime(path)
        _preview_store[preview_id] = (path, created_at)
    # TTL 체크, 파일 존재 체크...
```

### CORS + HEAD 라우트 (`main.py`, `scene_detect.py`)
```python
CORS_ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

@router.head("/preview/{preview_id}")
@router.get("/preview/{preview_id}")
async def get_preview(preview_id: str, request: Request): ...
```

## 회귀 테스트

`backend/tests/routers/test_scene_detect_preview.py`:
- CORS에 HEAD 포함 확인
- HEAD /preview/{없는ID} → 404 (not 405)
- HEAD /preview/{존재하는ID} → 200 + Accept-Ranges
- 메모리 store 비어도 temp 파일 있으면 → 200

## 교훈

| 잘못된 접근 | 올바른 접근 |
|------------|-----------|
| 에러 로그 하나(405) 보고 바로 고침 | 사용자가 뭘 못하는지(영상 안 보임)에서 역추적 |
| 405 고쳤으니 끝 | 405 고친 뒤에도 영상이 보이는지 확인 |
| 증상별 개별 패치 | 실패 체인 전체 그림 그리고 동시 수정 |
| 노이즈(zustand)에 시간 소모 | 재생 실패와 무관한 경고 즉시 제외 |

## 잔여 리스크

- 멀티 인스턴스 간 temp 파일 비공유 → 인스턴스 A에서 생성, 인스턴스 B에서 서빙 시 여전히 404
- 완전한 해결: preview를 공유 스토리지(S3/Redis-backed mapping)로 이동 필요
