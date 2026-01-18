# Vivid RAG 데이터 파이프라인 SPEC (2026-01-18)

> **목적**: Vivid RAG 데이터 수집/검증/인덱싱의 단일 운영 스펙
> **범위**: 1D~6D, AD, QC, AI Persona, Character
> **상태**: 쉬운 작업 완료 + 고위험/고비용 작업 남음

---

## ✅ 완료된 작업 요약 (확인됨)

### 디렉토리 및 데이터 파일
- `backend/data/rag_docs/prompt/prompt_patterns.json` — 플랫폼별 프롬프트 패턴
- `backend/data/rag_docs/story/story_structures.json` — 서사 구조
- `backend/data/rag_docs/ambience/sound_design_principles.json` — 사운드 디자인 원칙
- `backend/data/rag_docs/veo/veo_camera_movements.json` — VEO 카메라 무브먼트
- `data/source_packs/logic_math/schema.json` — logic_vector 스키마
- `data/source_packs/logic_math/vectors/*.json` — 샘플 3개 (bong/nolan/wong)

### 시딩 스크립트
- `backend/scripts/seed_prompt_rag.py` — 1D (Prompt Alchemy)
- `backend/scripts/seed_story_rag.py` — Story/2D
- `backend/scripts/seed_all_dimension_rag.py` — 5D/6D rag_docs 지원 확장

### 실행 명령어
```bash
cd backend && source venv/bin/activate

python scripts/seed_prompt_rag.py
python scripts/seed_story_rag.py

python scripts/seed_all_dimension_rag.py --dimension 4D
python scripts/seed_all_dimension_rag.py --dimension 5D
python scripts/seed_all_dimension_rag.py --dimension 6D
```

### 정합성 검증 완료 항목
1. **VEO app_key 정합성**: `veo.video.generate` 일치
2. **logic_math 벡터 연동**: `dataset_id=video_ref` 라우팅 정합
3. **Story/Storyboard 컬렉션 공유**: 2D 컬렉션 공유 명시
4. **Sound는 6D 컬렉션 사용** (별도 SOUND 컬렉션 없음)

---

## 📚 앱별 코퍼스 설계 (구체 리스트)

> **원칙**: “외부 소스는 라이선스 확인 후 추가”
> **표기**: EXT-*는 외부 문서/논문/데이터셋, 내부는 경로 표기

### AD (Aesthetic Director)
- **데이터셋/논문**
  - EXT-MOVIENET: 영화 샷/씬/캐릭터/트레일러 주석 데이터셋 (촬영·색감·편집 스타일 기반) 
- **내부 시드**
  - `data/source_packs/{auteur}/visual_dna/*`

### 1D (Prompt Generator) / Prompt Alchemy
- **문서/가이드**
  - EXT-VEO: Veo 모델 & Vertex AI API 레퍼런스
  - EXT-RUNWAY: Runway Gen‑3 Prompting Guide
  - EXT-SORA: OpenAI Sora 2 공식 소개
- **내부 시드**
  - `backend/data/rag_docs/prompt/prompt_patterns.json`

### 2D (Story Architect / Storyboard)
- **데이터셋/논문**
  - EXT-LSMDC: 문장↔영상 클립 정렬 데이터셋 (서사/자막/장면 매핑)
  - EXT-MOVIENET: 스크립트/샷/씬 메타데이터 활용
- **내부 시드**
  - `backend/data/rag_docs/story/story_structures.json`
- **정책**: Story/Storyboard는 2D 컬렉션 공유 (분리 필요 시 dataset_id 분리)

### 3D (Image Generator)
- **데이터셋/논문**
  - EXT-MOVIENET: 프레임/샷 기반 구도·조명·색감 힌트
- **내부 시드**
  - `data/source_packs/{auteur}/cinematography/*`

### 4D (Reference Analyzer)
- **데이터셋/논문**
  - EXT-MOVIENET, EXT-LSMDC (영상-서사 분석 기반)
- **수학 로직 벡터**
  - `data/source_packs/logic_math/vectors/*.json` (dataset_id=video_ref)

### 5D (Video Generation / Veo)
- **문서/가이드**
  - EXT-VEO: Veo 모델 & Vertex AI API 레퍼런스
- **데이터셋/논문**
  - EXT-MOVIENET: 카메라 무브먼트/시각적 리듬 참고
- **내부 시드**
  - `backend/data/rag_docs/veo/veo_camera_movements.json`

### 6D (Sound Designer / Suno)
- **데이터셋/논문**
  - EXT-AUDIOSET: 대규모 오디오 이벤트 데이터셋
- **내부 시드**
  - `backend/data/rag_docs/ambience/sound_design_principles.json`

### QC (Quality Controller)
- **문서/논문**
  - EXT-VMAF: 영상 품질 평가 지표(VMAF) 공식 레퍼런스
  - (추가 예정) SSIM/LPIPS/FID 등 품질 지표

### Character Consistency
- **데이터셋/논문**
  - EXT-MOVIENET: 멀티샷 캐릭터/장면 메타데이터
- **인덱싱 전략**
  - Qdrant Named Vectors 기반 다중 임베딩 저장

### AI Persona / Mirror
- **문서/논문**
  - 내부 심리학 자료 (`backend/data/rag_docs/psychology/*.json`)
- **상태**: P1은 LLM-only (RAG 비활성)

---

## 🧭 데이터 수집 프로토콜 (RAG Corpus Pipeline)

```
Discovery → License Check → Normalize → Chunk → Embed → Index → Evaluate → Monitor
```

1. **Discovery (Tavily)**: 후보 소스 수집
2. **License Check**: 상업 사용 가능 여부 확인
3. **Normalize**: 텍스트 정제/중복 제거
4. **Semantic Chunking**: 의미 단위 청킹
5. **Embedding**: 텍스트/이미지/오디오별 임베딩
6. **Index**: Qdrant Hybrid + NotebookLM 업로드
7. **Evaluate**: RAGAS 기반 품질 평가
8. **Monitor**: 품질 저하 시 격리/재인덱싱

---

## 🔶 남은 고위험/복잡 작업 (업데이트)

### 1) Gemini 영상 분석 파이프라인 (VideoLogicExtractor)
- **핵심 포인트**
  - Gemini Video Understanding 기준 샘플링(기본 1FPS) 적용
  - 1M 컨텍스트 입력에서 약 1시간(기본), 저해상도면 ~3시간 처리
  - File API/YouTube URL 모두 지원

```python
# backend/app/rag/video_logic_extractor.py (신규)
class VideoLogicExtractor:
    async def analyze_video(self, video_path: str) -> LogicVector:
        # TODO: File API 업로드
        # TODO: Gemini video prompt 설계
        # TODO: 1 FPS 샘플링 기반 분석
        # TODO: 결과 파싱/검증
        pass
```

### 2) NotebookLM 자동화 (Playwright)
- **Enterprise 사용 한도 참고**
  - 노트북 수, 소스 수, 쿼리/일 제한은 Enterprise 기준 문서로 확인
  - 개인/Plus 플랜은 별도 확인 필요 (공식 페이지 확인 후 업데이트)

### 3) 대규모 코퍼스 수집 + 저작권 검토
- **프로세스**: Tavily Search (no raw) → Conditional Extract (query+chunks) → Dedup/License → source_packs → NotebookLM/Qdrant
- **법적 고려**: 공정이용/교육용/상업적 이용 여부 확인

### 4) Qdrant Named Vectors (Character 앱)
- 동일 포인트에 여러 벡터 저장 가능, 검색 시 특정 벡터 선택 가능

### 5) 품질 게이트 (RAGAS 기반)
- Faithfulness / Answer Relevancy / Context Precision / Context Recall
- 품질 미달 데이터는 격리 후 재인덱싱

---

## ✅ 실행 순서 (권장)

### Phase 1: 기반 확정
1. NotebookLM 플랜/한도 확정
2. Gemini 모델 ID 및 비용 확정

### Phase 2: 파이프라인 구축
1. VideoLogicExtractor 구현
2. NotebookLM 세션 안정화
3. Tavily 기반 코퍼스 자동 수집 파이프라인 확장

### Phase 3: 코퍼스 확장
1. 라이선스 검증된 소스만 추가
2. Qdrant 재인덱싱
3. 품질 리포트 기준 미달 데이터 격리

---

## 🔗 외부 레퍼런스 (요약)
- EXT-MOVIENET: MovieNet dataset
- EXT-LSMDC: Large Scale Movie Description Challenge
- EXT-AUDIOSET: AudioSet
- EXT-VMAF: Netflix VMAF
- EXT-VEO: Veo 모델 레퍼런스 (Vertex AI)
- EXT-RUNWAY: Runway Gen-3 Prompting Guide
- EXT-SORA: OpenAI Sora 2
- EXT-QDRANT-NAMED: Qdrant Named Vectors
- EXT-RAGAS: RAGAS metrics
- EXT-GEMINI-VIDEO: Gemini Video Understanding
- EXT-GEMINI-EMBED: Gemini/Vertex AI Multimodal Embeddings

---

*Last Updated: 2026-01-18*
