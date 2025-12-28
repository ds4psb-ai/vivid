# Auteur Data Collection Protocol (CODEX v38)

**작성**: 2025-12-29  
**대상**: Engineering / Data / Ops  
**목표**: 거장 영상 데이터 수집 → NotebookLM 적재 → Source Pack 생성까지의 E2E 프로토콜 정의

---

## 0) Canonical Anchors

- 철학/원칙: `20_CREBIT_ARCHITECTURE_EVOLUTION_CODEX.md`
- NotebookLM 프로토콜: `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md`
- 영상 구조화: `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md`
- NotebookLM 출력 규격: `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md`
- 리서치 소스: `04_RESEARCH_SOURCES_2025-12.md`

---

## 1) Protocol Invariants (Non-negotiable)

1. **저작권 준수**: Fair Use / Educational Purpose 범위 내에서만 수집
2. **출처 명시**: 모든 수집 데이터는 `source_manifest`에 원본 URL/권리 상태 기록
3. **DB SoR**: 수집 → Sheets Bus → DB 승격 순서 고수
4. **No Direct Upload**: 원본 영상 파일은 NotebookLM에 직접 업로드하지 않음 (자막/텍스트만)
5. **Phase-locked Pack**: 캡슐 승격은 반드시 `{cluster_id, temporal_phase}` 단위로 진행

---

## 2) 수집 대상 (Target Sources)

### 2.1 Tier 1: 자막/텍스트 추출 가능 (우선순위 높음)

| 소스 유형 | 예시 | 추출 방식 | 비고 |
|----------|------|----------|------|
| **YouTube 인터뷰** | MasterClass, 영화제 Q&A | yt-dlp + 자막 | 공개 영상만 |
| **YouTube 마스터클래스** | 감독 분석 영상 | yt-dlp + 자막 | 자동자막 포함 |
| **Vimeo 클립** | 단편/BTS | Playwright + API | 제한적 접근 |
| **공개 팟캐스트** | 감독 인터뷰 오디오 | Whisper 전사 | MP3 다운로드 |

### 2.2 Tier 2: 텍스트 기반 (보조)

| 소스 유형 | 예시 | 추출 방식 | 비고 |
|----------|------|----------|------|
| **영화 리뷰/분석** | Sight & Sound, Cahiers | Playwright/Fetch | 인용 범위 준수 |
| **학술 논문** | Google Scholar PDF | PDF Parser | 저작권 확인 필수 |
| **감독 에세이** | 저서 발췌 | 수동 입력 | 인용 표시 필수 |
| **영화 스크립트** | 공개 대본 | 텍스트 파싱 | 정식 배포본만 |

### 2.3 Tier 3: 직접 분석 필요 (후순위)

| 소스 유형 | 예시 | 추출 방식 | 비고 |
|----------|------|----------|------|
| **영화 본편** | 샷 분석용 | 로컬 분석 | 업로드 금지 |
| **BTS/메이킹** | DVD 부록 | 로컬 분석 | 개인 소장본 |

---

## 3) 크롤링 파이프라인

### 3.1 YouTube 수집 (yt-dlp)

```bash
# 자막만 추출 (영상 다운로드 없음)
yt-dlp --skip-download --write-auto-sub --sub-lang ko,en,ja \
  --sub-format vtt --output "%(id)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID"

# 메타데이터 추출
yt-dlp --skip-download --print-json \
  "https://youtube.com/watch?v=VIDEO_ID" > metadata.json
```

**자동화 스크립트**: `backend/scripts/crawl_youtube_subtitles.py`

```python
"""YouTube 자막 수집 스크립트 (예정)"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict

def crawl_youtube_subtitles(
    video_urls: List[str],
    output_dir: Path,
    languages: List[str] = ["ko", "en", "ja"]
) -> List[Dict]:
    """
    YouTube 영상에서 자막만 추출.
    
    Args:
        video_urls: YouTube URL 리스트
        output_dir: 출력 디렉토리
        languages: 추출할 자막 언어 코드
    
    Returns:
        추출된 자막 메타데이터 리스트
    """
    results = []
    for url in video_urls:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang", ",".join(languages),
            "--sub-format", "vtt",
            "--print-json",
            "--output", str(output_dir / "%(id)s"),
            url
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            metadata = json.loads(proc.stdout)
            results.append({
                "video_id": metadata["id"],
                "title": metadata["title"],
                "channel": metadata.get("channel"),
                "duration": metadata.get("duration"),
                "subtitles_path": output_dir / f"{metadata['id']}.vtt",
                "source_url": url,
                "rights_status": "public_youtube"
            })
    return results
```

### 3.2 웹 스크래핑 (Playwright MCP)

```python
"""웹 아티클 스크래핑 (Playwright 활용)"""
from playwright.async_api import async_playwright

async def scrape_article(url: str) -> dict:
    """
    영화 리뷰/분석 아티클 텍스트 추출.
    
    Returns:
        {"title": str, "body": str, "source_url": str, "rights_status": str}
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        
        title = await page.title()
        # 본문 추출 (사이트별 셀렉터 조정 필요)
        body = await page.inner_text("article, .article-body, .entry-content")
        
        await browser.close()
        
        return {
            "title": title,
            "body": body[:50000],  # 50K words 제한
            "source_url": url,
            "rights_status": "web_scrape_citation"
        }
```

### 3.3 오디오 전사 (Whisper)

```python
"""오디오 파일 전사 (OpenAI Whisper)"""
import whisper

def transcribe_audio(audio_path: str, language: str = "ko") -> dict:
    """
    오디오 파일을 텍스트로 전사.
    
    NotebookLM은 오디오 업로드 시 자동 전사하지만,
    사전 처리가 필요한 경우 Whisper 사용.
    """
    model = whisper.load_model("large-v3")
    result = model.transcribe(audio_path, language=language)
    
    return {
        "text": result["text"],
        "segments": result["segments"],
        "language": result["language"],
        "source_path": audio_path,
        "rights_status": "audio_transcription"
    }
```

---

## 4) 저작권 가이드라인

### 4.1 허용 범위

| 사용 유형 | 허용 여부 | 조건 |
|----------|----------|------|
| 자막 텍스트 분석 | ✅ 허용 | Fair Use (교육/연구) |
| 인터뷰 인용 | ✅ 허용 | 출처 명시, 분량 제한 |
| 샷 분석 (로컬) | ✅ 허용 | 업로드 금지 |
| 전체 대본 복사 | ⚠️ 조건부 | 공식 배포본만 |
| 영화 클립 업로드 | ❌ 금지 | 저작권 침해 |
| BTS 영상 공유 | ❌ 금지 | 저작권 침해 |

### 4.2 출처 표시 형식

```json
{
  "source_manifest": [
    {
      "source_id": "yt_abc123",
      "type": "youtube_subtitle",
      "title": "봉준호 감독 마스터클래스",
      "url": "https://youtube.com/watch?v=abc123",
      "channel": "MasterClass",
      "duration_sec": 3600,
      "rights_status": "public_youtube",
      "collection_date": "2025-12-29",
      "usage_scope": "subtitle_text_only"
    }
  ]
}
```

### 4.3 Rights Status 코드

| 코드 | 의미 | 사용 가능 범위 |
|------|------|--------------|
| `public_youtube` | 공개 YouTube 영상 | 자막/메타데이터만 |
| `creative_commons` | CC 라이선스 | 라이선스 조건 준수 |
| `fair_use_education` | 교육 목적 Fair Use | 인용 범위 내 |
| `official_press` | 공식 보도자료 | 전문 사용 가능 |
| `licensed` | 정식 라이선스 | 계약 범위 내 |
| `restricted` | 제한적 접근 | 분석만, 재배포 금지 |

---

## 5) NotebookLM 적재 프로토콜

### 5.1 Source Pack 생성 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                   Auteur Data Collection                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │ YouTube  │    │ Articles │    │  Audio   │               │
│  │ Subtitles│    │  (Web)   │    │(Podcast) │               │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘               │
│       │               │               │                      │
│       └───────────────┼───────────────┘                      │
│                       ▼                                      │
│              ┌────────────────┐                              │
│              │  raw_assets DB  │                              │
│              │ (source_manifest)│                             │
│              └────────┬────────┘                              │
│                       │                                      │
│                       ▼                                      │
│              ┌────────────────┐                              │
│              │  Sheets Bus     │                              │
│              │ CREBIT_NOTEBOOK │                              │
│              │    _LIBRARY     │                              │
│              └────────┬────────┘                              │
│                       │                                      │
│                       ▼                                      │
│              ┌────────────────┐                              │
│              │  NotebookLM     │                              │
│              │  Source Upload  │                              │
│              │ (Manual/API*)   │                              │
│              └────────┬────────┘                              │
│                       │                                      │
│                       ▼                                      │
│              ┌────────────────┐                              │
│              │  Source Pack    │                              │
│              │  {cluster_id,   │                              │
│              │   temporal_phase}│                             │
│              └─────────────────┘                              │
└─────────────────────────────────────────────────────────────┘

* NotebookLM API는 2025년 현재 제한적 제공
```

### 5.2 Source Pack 생성 규칙

```python
"""Source Pack 생성 로직"""
from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class SourcePackConfig:
    cluster_id: str          # 예: "CL_BONG"
    temporal_phase: str      # 예: "HOOK"
    max_sources: int = 50    # NotebookLM 제한
    max_words_per_source: int = 500_000

def create_source_pack(
    cluster_id: str,
    temporal_phase: str,
    sources: List[dict]
) -> dict:
    """
    Source Pack 생성.
    
    50개 source 초과 시 자동 sharding.
    """
    base_bundle_id = f"sp_{cluster_id}_{temporal_phase}_{datetime.now():%Y%m%d}"
    
    packs = []
    for i in range(0, len(sources), 50):
        shard = sources[i:i+50]
        shard_id = f"p{(i//50)+1:02d}" if len(sources) > 50 else ""
        
        packs.append({
            "bundle_id": f"{base_bundle_id}_{shard_id}".strip("_"),
            "cluster_id": cluster_id,
            "temporal_phase": temporal_phase,
            "source_count": len(shard),
            "sources": shard,
            "source_hash": compute_hash(shard),
            "created_at": datetime.utcnow().isoformat()
        })
    
    return packs
```

### 5.3 NotebookLM Enterprise API 연동

> [!NOTE]
> NotebookLM Enterprise API는 **Gemini Enterprise 라이선스**가 필요하며,
> Crebit 프로젝트는 `arkain.info@gmail.com` 계정으로 라이선스 활성화됨.
> **Project Number**: `239259013228` | **Project ID**: `vivid-canvas-482303`

#### 5.3.1 API 베이스 URL

```
https://{ENDPOINT_LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/{LOCATION}/notebooks
```

| 변수 | 값 | 설명 |
|------|-----|------|
| `ENDPOINT_LOCATION` | `global-` | 멀티 리전 (us-, eu-, global-) |
| `PROJECT_NUMBER` | GCP 프로젝트 번호 | 숫자 ID |
| `LOCATION` | `global` | 데이터 스토어 위치 |

#### 5.3.2 인증

```bash
# gcloud 인증 (Google Drive 접근 포함)
gcloud auth login --enable-gdrive-access

# 액세스 토큰 발급
gcloud auth print-access-token
```

#### 5.3.3 노트북 생성 API

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/global/notebooks" \
  -d '{
    "title": "CL_BONG_HOOK_20251229"
  }'
```

**응답**:
```json
{
  "title": "CL_BONG_HOOK_20251229",
  "notebookId": "abc123xyz",
  "metadata": {
    "userRole": "PROJECT_ROLE_OWNER",
    "isShared": false
  },
  "name": "projects/123456/locations/global/notebooks/abc123xyz"
}
```

#### 5.3.4 소스 추가 API (3가지 방식)

**방법 1: 텍스트 직접 입력**
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/global/notebooks/{NOTEBOOK_ID}/sources:batchCreate" \
  -d '{
    "userContents": [{
      "textContent": {
        "sourceName": "봉준호 마스터클래스 자막",
        "content": "자막 텍스트 내용..."
      }
    }]
  }'
```

**방법 2: 웹 URL**
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/global/notebooks/{NOTEBOOK_ID}/sources:batchCreate" \
  -d '{
    "userContents": [{
      "webContent": {
        "url": "https://example.com/bong-interview",
        "sourceName": "봉준호 인터뷰 기사"
      }
    }]
  }'
```

**방법 3: Google Drive 문서**
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/global/notebooks/{NOTEBOOK_ID}/sources:batchCreate" \
  -d '{
    "userContents": [{
      "googleDriveContent": {
        "documentId": "GOOGLE_DOC_ID",
        "mimeType": "application/vnd.google-apps.document",
        "sourceName": "봉준호 분석 문서"
      }
    }]
  }'
```

**방법 4: 파일 업로드 (PDF, TXT, MD, 오디오)**
```bash
curl -X POST --data-binary "@/path/to/subtitle.txt" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-Upload-File-Name: bong_masterclass_01.txt" \
  -H "X-Goog-Upload-Protocol: raw" \
  -H "Content-Type: text/plain" \
  "https://global-discoveryengine.googleapis.com/upload/v1alpha/projects/{PROJECT_NUMBER}/locations/global/notebooks/{NOTEBOOK_ID}/sources:uploadFile"
```

**지원 콘텐츠 유형**:
- 문서: `application/pdf`, `text/plain`, `text/markdown`, `.docx`, `.pptx`, `.xlsx`
- 오디오: `audio/mpeg`, `audio/wav`, `audio/m4a`, `audio/ogg` 등
- 이미지: `image/png`, `image/jpeg`

#### 5.3.5 AI 오디오 오버뷰 생성

```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://global-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_NUMBER}/locations/global/notebooks/{NOTEBOOK_ID}/audioOverviews" \
  -d '{
    "sourceIds": [{"id": "SOURCE_ID_1"}, {"id": "SOURCE_ID_2"}],
    "episodeFocus": "봉준호 감독의 미장센과 사회 비평",
    "languageCode": "ko"
  }'
```

**응답**:
```json
{
  "audioOverview": {
    "status": "AUDIO_OVERVIEW_STATUS_IN_PROGRESS",
    "audioOverviewId": "audio123",
    "name": "projects/.../notebooks/.../audioOverviews/audio123"
  }
}
```

#### 5.3.6 Python 클라이언트 (구현 예정)

```python
"""NotebookLM Enterprise API 클라이언트"""
import httpx
from typing import List, Optional
from google.auth import default
from google.auth.transport.requests import Request

class NotebookLMEnterpriseClient:
    """NotebookLM Enterprise API 클라이언트."""
    
    BASE_URL = "https://global-discoveryengine.googleapis.com/v1alpha"
    
    def __init__(self, project_number: str, location: str = "global"):
        self.project_number = project_number
        self.location = location
        self._credentials = None
    
    def _get_access_token(self) -> str:
        """Google Cloud 액세스 토큰 발급."""
        if not self._credentials:
            self._credentials, _ = default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        self._credentials.refresh(Request())
        return self._credentials.token
    
    async def create_notebook(self, title: str) -> dict:
        """새 노트북 생성."""
        url = f"{self.BASE_URL}/projects/{self.project_number}/locations/{self.location}/notebooks"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                json={"title": title}
            )
            resp.raise_for_status()
            return resp.json()
    
    async def add_text_source(
        self, notebook_id: str, name: str, content: str
    ) -> dict:
        """텍스트 소스 추가."""
        url = f"{self.BASE_URL}/projects/{self.project_number}/locations/{self.location}/notebooks/{notebook_id}/sources:batchCreate"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                json={
                    "userContents": [{
                        "textContent": {
                            "sourceName": name,
                            "content": content
                        }
                    }]
                }
            )
            resp.raise_for_status()
            return resp.json()
    
    async def add_web_source(
        self, notebook_id: str, name: str, url: str
    ) -> dict:
        """웹 URL 소스 추가."""
        api_url = f"{self.BASE_URL}/projects/{self.project_number}/locations/{self.location}/notebooks/{notebook_id}/sources:batchCreate"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                api_url,
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                json={
                    "userContents": [{
                        "webContent": {
                            "url": url,
                            "sourceName": name
                        }
                    }]
                }
            )
            resp.raise_for_status()
            return resp.json()
    
    async def create_audio_overview(
        self,
        notebook_id: str,
        source_ids: Optional[List[str]] = None,
        focus: str = "",
        language: str = "ko"
    ) -> dict:
        """AI 오디오 오버뷰 생성."""
        url = f"{self.BASE_URL}/projects/{self.project_number}/locations/{self.location}/notebooks/{notebook_id}/audioOverviews"
        payload = {
            "episodeFocus": focus,
            "languageCode": language
        }
        if source_ids:
            payload["sourceIds"] = [{"id": sid} for sid in source_ids]
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {self._get_access_token()}"},
                json=payload
            )
            resp.raise_for_status()
            return resp.json()
```

#### 5.3.7 API 참조 문서

- [노트북 만들기 및 관리](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks?hl=ko)
- [데이터 소스 추가](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources?hl=ko)
- [AI 오디오 오버뷰](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-audio-overview?hl=ko)

---

## 6) 거장 리스트 (Phase 1 MVP)

### 6.1 Tier 1: 즉시 수집 (한국)

| 거장 | cluster_id | 대표작 | 수집 우선 소스 |
|------|-----------|-------|--------------|
| **봉준호** | `CL_BONG` | 기생충, 살인의 추억 | 마스터클래스, 영화제 Q&A |
| **박찬욱** | `CL_PARK_CW` | 올드보이, 헤어질 결심 | 인터뷰, BFI 강연 |
| **이창동** | `CL_LEE_CD` | 버닝, 오아시스 | 칸 인터뷰, 평론 |
| **김지운** | `CL_KIM_JW` | 악마를 보았다, 밀정 | 유튜브 인터뷰 |
| **나홍진** | `CL_NA` | 곡성, 황해 | 영화제 Q&A |

### 6.2 Tier 2: 확장 (해외)

| 거장 | cluster_id | 대표작 | 수집 우선 소스 |
|------|-----------|-------|--------------|
| **쿠엔틴 타란티노** | `CL_TARANTINO` | 펄프픽션, 킬빌 | 마스터클래스, 인터뷰 |
| **크리스토퍼 놀란** | `CL_NOLAN` | 인셉션, 테넷 | BAFTA 강연 |
| **데이비드 핀처** | `CL_FINCHER` | 세븐, 소셜네트워크 | 다큐멘터리 |
| **데니스 빌뇌브** | `CL_VILLENEUVE` | 듄, 어라이벌 | 영화제 인터뷰 |
| **왕가위** | `CL_WONG` | 화양연화, 중경삼림 | 칸 인터뷰 |

### 6.3 수집 진행 상태 추적

```json
{
  "auteur_collection_status": {
    "CL_BONG": {
      "status": "in_progress",
      "sources_collected": 12,
      "sources_target": 30,
      "phases_covered": ["HOOK", "BUILD"],
      "last_updated": "2025-12-29"
    },
    "CL_PARK_CW": {
      "status": "not_started",
      "sources_collected": 0,
      "sources_target": 25
    }
  }
}
```

---

## 7) 수집 자동화 스크립트

### 7.1 디렉토리 구조

```
backend/
├── scripts/
│   ├── crawl_youtube_subtitles.py   # YouTube 자막 수집
│   ├── crawl_web_articles.py        # 웹 아티클 스크래핑
│   ├── transcribe_audio.py          # 오디오 전사
│   ├── create_source_pack.py        # Source Pack 생성
│   └── upload_to_drive.py           # Google Drive 업로드
├── data/
│   ├── subtitles/                   # 수집된 자막
│   ├── articles/                    # 스크랩된 아티클
│   ├── transcripts/                 # 전사된 텍스트
│   └── source_packs/                # 생성된 Source Pack
```

### 7.2 수집 커맨드 (예정)

```bash
# 봉준호 YouTube 자막 수집
python scripts/crawl_youtube_subtitles.py \
  --auteur "CL_BONG" \
  --playlist "https://youtube.com/playlist?list=..."

# 웹 아티클 스크랩
python scripts/crawl_web_articles.py \
  --urls "urls.txt" \
  --output "data/articles/bong/"

# Source Pack 생성
python scripts/create_source_pack.py \
  --cluster "CL_BONG" \
  --phase "HOOK" \
  --input "data/subtitles/bong/"
```

---

## 8) 품질 게이트

### 8.1 수집 품질 기준

| 항목 | 최소 요건 | 검증 시점 |
|------|----------|----------|
| 자막 길이 | 1,000자 이상 | 수집 직후 |
| 언어 일치 | 지정 언어 90%+ | 전사 후 |
| 중복 체크 | source_hash 중복 없음 | DB 저장 전 |
| 권리 상태 | restricted 아닌 것 | Pack 생성 전 |

### 8.2 Source Pack 품질 기준

| 항목 | 최소 요건 | 검증 시점 |
|------|----------|----------|
| source_count | 5개 이상 | Pack 생성 시 |
| temporal_phase 커버리지 | 1개 이상 | Pack 완성 시 |
| metrics_snapshot 존재 | 필수 | NotebookLM 전송 전 |

---

## 9) 운영 메트릭스

### 9.1 대시보드 지표

```python
@dataclass
class CollectionMetrics:
    total_auteurs: int
    auteurs_started: int
    auteurs_completed: int
    total_sources: int
    sources_by_type: Dict[str, int]  # youtube, web, audio
    source_packs_created: int
    average_sources_per_auteur: float
```

### 9.2 알림 조건

| 이벤트 | 조건 | 알림 방법 |
|--------|-----|----------|
| 수집 실패 | 3회 연속 실패 | Slack |
| 저작권 경고 | restricted 비율 > 30% | Email |
| Pack 완성 | 신규 Pack 생성 | Slack |

---

## 10) 롤아웃 계획

### Phase 1 (Week 1-2): 봉준호 MVP
- [ ] YouTube 마스터클래스 자막 수집 (10개)
- [ ] 영화제 Q&A 인터뷰 수집 (5개)
- [ ] Source Pack 1개 생성 (HOOK phase)
- [ ] NotebookLM 수동 업로드

### Phase 2 (Week 3-4): 한국 거장 확장
- [ ] 박찬욱, 이창동 자막 수집
- [ ] 웹 아티클 스크래핑 자동화
- [ ] Source Pack 3개 생성

### Phase 3 (Month 2): 해외 거장 + 자동화
- [ ] 타란티노, 놀란 수집
- [ ] 크롤링 스크립트 완성
- [ ] Drive 업로드 자동화

---

## 11) Reference

- `33_NOTEBOOKLM_SOURCE_PACK_AND_PROMPT_PROTOCOL_CODEX.md` - Source Pack 규격
- `09_NOTEBOOKLM_OUTPUT_SPEC_V1.md` - 출력 규격
- `11_DB_PROMOTION_RULES_V1.md` - 승격 규칙
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
