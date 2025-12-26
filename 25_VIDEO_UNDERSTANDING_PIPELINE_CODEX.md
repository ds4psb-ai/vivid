# Video Understanding Pipeline (CODEX v25)

**작성**: 2025-12-24  
**대상**: Product / Data / Engineering  
**목표**: 명장면/레퍼런스 영상을 Gemini 3 Pro로 구조화 데이터화하고 DB SoR에 축적하는 표준 파이프라인

---

## 0) 최신 기준 (2025-12)

- Gemini 3 Pro는 멀티모달(문서/공간/스크린/비디오) 이해에서 최고 성능을 표방.
- Gemini API는 **Video Understanding**과 **Structured Outputs(JSON Schema)**를 공식 지원.
- 최신 파이프라인은 **ASR + 키프레임/샷 분할 + 구조화 출력**이 가장 효율적.

참고:
- https://ai.google.dev/gemini-api/docs/video-understanding (Last updated 2025-12-18)
- https://ai.google.dev/gemini-api/docs/structured-output (Last updated 2025-12-18)
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding (Last updated 2025-12-22)
- https://blog.google/technology/developers/gemini-3-pro-vision/ (2025-12-05)

---

## 1) 파이프라인 개요

```
Raw Video
  → Shot Boundary / Keyframe
  → ASR Transcript
  → Gemini 3 Pro (Structured Output)
  → DB SoR (Scene/Shot Schema)
  → NotebookLM (Guide Layer)
```

핵심 원칙:
- 영상 자체는 NotebookLM에 직접 넣지 않는다.
- **Gemini 구조화 출력(JSON)**을 DB SoR에 먼저 적재한다.
- NotebookLM은 **DB에서 파생된 텍스트/요약**을 소스로 사용한다.

---

## 2) 전처리 (Preprocess)

- **Shot Boundary Detection**: 장면/샷 분할
- **Keyframe Extraction**: 정보 밀도가 높은 프레임 추출
- **ASR**: 대사/나레이션 텍스트 추출
- (옵션) **OCR**: 화면 내 텍스트 인식

---

## 3) Gemini 3 Pro 구조화 호출

- **responseMimeType**: `application/json`
- **responseJsonSchema**: 명장면 분석용 JSON Schema 적용
- **timestamps**: shot/scene 단위 time range 포함

권장 모델:
- **Gemini 3 Pro**: 최고 품질, 명장면 분석
- **Gemini 3 Flash**: 대량 처리/저비용 배치

---

## 4) 구조화 출력 스키마 (요약)

```json
{
  "source_id": "...",
  "work_id": "...",
  "sequence_id": "...",
  "scene_id": "...",
  "shot_id": "...",
  "segment_id": "...",
  "time_start": "00:01:12.120",
  "time_end": "00:01:24.880",
  "keyframes": ["kf_001", "kf_002"],
  "transcript": "...",
  "visual_schema": {
    "composition": "...",
    "lighting": "...",
    "color_palette": ["#102A43", "#334E68"],
    "camera_motion": "...",
    "blocking": "...",
    "pacing": "..."
  },
  "audio_schema": {
    "sound_design": "...",
    "music_mood": "..."
  },
  "motifs": ["stairs", "mirror_symmetry"],
  "confidence": 0.78,
  "prompt_version": "gemini-video-v1",
  "model_version": "gemini-3-pro-2025-12",
  "generated_at": "2025-12-24T10:00:00Z"
}
```

**API 검증 규칙 (MVP)**
- `work_id`, `scene_id`, `shot_id`는 필수
- `visual_schema` 허용 키: composition, lighting, color_palette, camera_motion, blocking, pacing
- `audio_schema` 허용 키: sound_design, music_mood
- 허용 키 외 데이터는 Reject
- `keyframes/motifs/evidence_refs`는 **비어 있지 않은 문자열 리스트**여야 함 (없으면 생략)
- `keyframes`는 `VIDEO_KEYFRAME_PATTERN`를 따름 (backend/.env)
- `evidence_refs`는 `VIDEO_EVIDENCE_REF_PATTERN`를 따름 (backend/.env, 예: `source:00:00:10.000-00:00:12.500`)

---

## 5) 저장 규칙 (DB SoR)

- `video_segments` 테이블(또는 유사)에 **segment 단위로 저장**
- `visual_schema` / `audio_schema`는 JSONB로 보관
- `evidence_refs`는 **timecode + keyframe id**를 포함

---

## 6) NotebookLM 연동

- NotebookLM에는 **DB에서 요약된 텍스트**만 제공
- guide_type은 `summary / persona / synapse / homage / variation`으로 분리
- 원본 영상 또는 내부 JSON은 **NotebookLM에 직접 노출하지 않는다**

---

## 7) 운영 체크리스트

- 타임코드 누락 방지
- keyframe 수 과다 방지 (샷당 1~3장 권장)
- ASR 텍스트 품질 확인
- JSON Schema 검증 실패 시 재실행

---

## 8) 연동 문서

- `08_SHEETS_SCHEMA_V1.md`
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- `14_INGEST_RUNBOOK_V1.md`
- `01_NODE_CANVAS_TECHNICAL_SPECIFICATION.md`
- `20_VIVID_ARCHITECTURE_EVOLUTION_CODEX.md`
- `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`
