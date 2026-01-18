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

> **원칙**: 외부 소스는 라이선스/robots 확인 후 추가  
> **수집 방식**: (A) 공식 데이터셋 직접 다운로드, (B) Tavily Search → Filter → Extract, (C) 문서 사이트는 Crawl/Map (향후)  
> **표기**: EXT-*는 외부 문서/논문/데이터셋, 내부는 경로 표기

### AD (Aesthetic Director)
- **문서/교재 (우선 수집)**  
  - *Cinematography: Theory and Practice* (Blain Brown)  
  - *The Visual Story* (Bruce Block)  
  - *The Filmmaker’s Eye* (Gustavo Mercado)  
  - *Film Art: An Introduction* (Bordwell/Thompson)
- **논문/데이터셋**  
  - EXT-MOVIENET: MovieNet (shots/scenes/trailer annotations)
- **영상 코퍼스**  
  - MovieNet 트레일러 클립 + 키프레임 (공식 배포)
- **수집 방식**  
  - 데이터셋 직접 다운로드, 교재는 요약/리뷰 페이지만 Extract (저작권 유의)

### 1D (Prompt Generator) / Prompt Alchemy
- **문서/가이드**  
  - EXT-VEO: Veo 모델 + Vertex AI API 레퍼런스  
  - EXT-RUNWAY: Runway Gen‑3/Gen‑4 Prompting Guide  
  - EXT-SORA: OpenAI Sora 공식 문서
- **내부 시드**  
  - `backend/data/rag_docs/prompt/prompt_patterns.json`
- **수집 방식**  
  - 공식 문서/가이드는 Tavily Search → Extract (query + chunks_per_source)

### 2D (Story Architect / Storyboard)
- **문서/교재**  
  - *Save the Cat!* (Blake Snyder)  
  - *Story* (Robert McKee)  
  - *The Anatomy of Story* (John Truby)  
  - *The Hero with a Thousand Faces* (Joseph Campbell)
- **논문/데이터셋**  
  - EXT-LSMDC: LSMDC (sentence ↔ clip alignment)  
  - EXT-MOVIENET: script/synopsis metadata
- **영상 코퍼스**  
  - LSMDC 클립, MovieNet 트레일러/씬 메타
- **내부 시드**  
  - `backend/data/rag_docs/story/story_structures.json`
- **정책**  
  - Story/Storyboard는 2D 컬렉션 공유 (필요 시 dataset_id 분리)

### 3D (Image Generator)
- **문서/교재**  
  - *Cinematography: Theory and Practice*  
  - *The Filmmaker’s Eye*  
  - Color/Lighting 교재 (추가 예정)
- **논문/데이터셋**  
  - EXT-MOVIENET: shot/frame 기반 시각 스타일 힌트
- **내부 시드**  
  - `data/source_packs/{auteur}/cinematography/*`
- **수집 방식**  
  - MovieNet 프레임/샷 메타 직접 수집

### 4D (Reference Analyzer)
- **문서/논문**  
  - *Film Art: An Introduction*  
  - *Narration in the Fiction Film* (Bordwell)  
  - Film Theory/미학 논문 (추가 예정)
- **논문/데이터셋**  
  - EXT-MOVIENET, EXT-LSMDC (영상‑서사 분석)
- **수학 로직 벡터**  
  - `data/source_packs/logic_math/vectors/*.json` (dataset_id=video_ref)

### 5D (Video Generation / Veo)
- **문서/가이드**  
  - EXT-VEO: Veo 모델/Vertex AI API  
  - EXT-GEMINI-VIDEO: Gemini Video Understanding (분석용)
- **논문/데이터셋**  
  - EXT-MOVIENET: 카메라 무브먼트/리듬 참고
- **내부 시드**  
  - `backend/data/rag_docs/veo/veo_camera_movements.json`
- **수집 방식**  
  - 공식 문서는 Extract, 데이터셋은 직접 다운로드

### 6D (Sound Designer / Suno)
- **문서/교재**  
  - *Designing Sound* (Andy Farnell)  
  - *The Sound Effects Bible* (Ric Viers)
- **논문/데이터셋**  
  - EXT-AUDIOSET: AudioSet
- **내부 시드**  
  - `backend/data/rag_docs/ambience/sound_design_principles.json`

### QC (Quality Controller)
- **문서/논문**  
  - EXT-VMAF: VMAF (Netflix)  
  - SSIM/PSNR/LPIPS/FID 등 품질 지표 (필요 시 추가)
- **수집 방식**  
  - 공용 지표 문서 + 내부 테스트 영상 세트

### Character Consistency
- **데이터셋/논문**  
  - EXT-MOVIENET: 캐릭터/멀티샷 메타데이터
- **인덱싱 전략**  
  - EXT-QDRANT-NAMED: Qdrant Named Vectors 기반 다중 임베딩 저장

### AI Persona / Mirror
- **문서/논문**  
  - IPIP Big Five markers (오픈 접근)  
  - Attachment/Enneagram/MBTI 공식 소스 (라이선스 확인)
- **상태**  
  - P1은 LLM-only (RAG 비활성)

---

## 🧭 데이터 수집 프로토콜 (RAG Corpus Pipeline)

```
Discovery → Filter → Extract/Crawl/Direct → Normalize → Chunk → Embed → Index → Evaluate → Monitor
```

1. **Discovery (Tavily Search/Map)**: 후보 URL/도메인 수집
2. **Filter**: score/도메인/robots/라이선스 기준으로 1차 필터
3. **Extract/Crawl/Direct**:
   - **Extract**: 상위 URL 대상, `query + chunks_per_source`로 타깃 추출
   - **Crawl**: 문서 사이트/다중 페이지(추가 예정)
   - **Direct**: MovieNet/AudioSet 등 공식 데이터셋 직접 다운로드
4. **Normalize**: 텍스트 정제/중복 제거 + 원본 링크 보존
5. **Semantic Chunking**: 의미 단위 청킹
6. **Embedding**: 텍스트/이미지/오디오별 임베딩  
   - 기본 텍스트 임베딩: `gemini-embedding-001`
7. **Index**: Qdrant Hybrid + NotebookLM 업로드
8. **Evaluate**: RAGAS 기반 품질 평가
9. **Monitor**: 품질 저하 시 격리/재인덱싱

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
- **프로세스**: Tavily Search → Filter(점수/도메인/라이선스) →  
  (A) Extract(타깃 URL) / (B) Crawl(문서 사이트) / (C) Direct(공식 데이터셋)  
  → Dedup/License → source_packs → NotebookLM/Qdrant
- **법적 고려**: 공정이용/교육용/상업적 이용 여부 확인, paywall/구독 페이지 제외

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
4. 코퍼스 인제스트/품질 게이트 자동화

```bash
# Tavily research output → Qdrant 인제스트
python scripts/ingest_research_corpus.py \
  --input data/source_packs/research/ \
  --dimension 4D \
  --dataset-id film_analysis \
  --app-key teaching.reference.analyze

# 품질 게이트 (기본 threshold 적용)
python scripts/run_rag_quality_gate.py --no-llm
```

### Phase 3: 코퍼스 확장
1. 라이선스 검증된 소스만 추가
2. Qdrant 재인덱싱
3. 품질 리포트 기준 미달 데이터 격리

---

## 🔗 외부 레퍼런스 (요약)
- EXT-MOVIENET: https://movienet.github.io/
- EXT-LSMDC: https://arxiv.org/abs/1605.03705
- EXT-AUDIOSET: https://research.google.com/audioset/
- EXT-VMAF: https://github.com/Netflix/vmaf
- EXT-VEO: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation
- EXT-RUNWAY: https://help.runwayml.com/hc/en-us/articles/30586818553107-Gen-3-Alpha-Prompting-Guide
- EXT-SORA: https://openai.com/sora/
- EXT-QDRANT-NAMED: https://qdrant.tech/documentation/concepts/vectors/
- EXT-RAGAS: https://github.com/explodinggradients/ragas
- EXT-GEMINI-VIDEO: https://ai.google.dev/gemini-api/docs/video-understanding
- EXT-GEMINI-EMBED: https://ai.google.dev/gemini-api/docs/embeddings
- EXT-TAVILY-EXTRACT: https://docs.tavily.com/documentation/best-practices/best-practices-extract
- EXT-TAVILY-API: https://docs.tavily.com/documentation/api-reference/endpoint/extract
