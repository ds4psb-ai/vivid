# Video Pipeline Flow: Metadata & Comment Extraction to VDG Analysis

**작성**: 2026-01-22
**버전**: v1.1.0
**목표**: 숏폼 영상(TikTok/YouTube Shorts/Instagram Reels) 등록 → 댓글 게이트 → VDG 분석 → DB 저장 전체 흐름

> [!IMPORTANT]
> **VDG 기술 스펙**: [`02_VDG.md`](./02_VDG.md)
> **패턴 클러스터링**: [`26_PATTERN_CLUSTERING.md`](./26_PATTERN_CLUSTERING.md)
> **VDG 운영 런북**: [`23_VDG_OPS_RUNBOOK.md`](./23_VDG_OPS_RUNBOOK.md)

---

## 1. 전체 파이프라인 개요

```mermaid
flowchart TD
    subgraph ENTRY["진입점"]
        M["수동 입력<br/>/items/manual"]
        C["크롤러 승격<br/>/items/{id}/promote"]
    end

    M --> METADATA
    C --> VDG

    subgraph METADATA["메타데이터 추출"]
        MT["TikTok<br/>extract_tiktok_complete"]
        MY["YouTube<br/>YouTubeCrawler"]
        MI["Instagram<br/>extract_social_metadata"]
    end

    METADATA --> GATE["댓글 게이트<br/>comment_count 체크"]
    GATE -->|pass| DB1["OutlierItem 저장"]
    GATE -->|fail + skip_comments=false| ERR["HTTPException 400<br/>COMMENT_*"]
    GATE -->|fail + skip_comments=true| DB1

    ERR -->|"사용자 선택"| SKIP["skip_comments=true<br/>재전송"]
    SKIP --> DB1

    DB1 --> VDG["VDG 분석<br/>_run_vdg_analysis_with_comments"]

    VDG --> COMMENTS["댓글 추출<br/>(skip_comments면 건너뜀)"]
    COMMENTS --> GEMINI["Gemini VDG 분석"]
    GEMINI --> DB2["RemixNode 저장"]
    DB2 --> CLUSTER["패턴 클러스터링"]
    CLUSTER --> NOTEBOOK["NotebookLM 저장"]
```

---

## 2. 진입점별 상세 흐름

### 2.1 수동 입력 (`POST /api/v1/outliers/items/manual`)

| 단계 | 함수/서비스 | 위치 | 설명 |
|------|------------|------|------|
| **1. URL 정규화** | `normalize_url_async()` | `outliers.py:L520` | 단축 URL 확장, 플랫폼별 canonical URL |
| **2. 메타데이터 추출** | 플랫폼별 (섹션 3 참조) | `outliers.py:L554-724` | view_count, like_count, comment_count 등 |
| **3. 댓글 게이트** | 플랫폼별 체크 | `outliers.py:L598-719` | `comment_count == 0` → HTTPException |
| **4. DB 저장** | `OutlierItem` 생성 | `outliers.py:L825-848` | status=PENDING or PROMOTED |
| **5. VDG 분석 시작** | `background_tasks.add_task()` | `outliers.py:L905-913` | 백그라운드 실행 |

#### 요청 스키마

```python
class OutlierItemManualCreate(BaseModel):
    video_url: str
    platform: str
    category: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    like_count: Optional[int] = None
    share_count: Optional[int] = None
    skip_comments: bool = False  # 댓글 없이 VDG 분석 진행 옵션
```

### 2.2 크롤러 승격 (`POST /api/v1/outliers/items/{id}/promote`)

| 단계 | 함수/서비스 | 위치 | 설명 |
|------|------------|------|------|
| **1. 아이템 조회** | `OutlierItem` select | `outliers.py:L1593-1596` | 기존 크롤링 데이터 |
| **2. AI 정책 검증** | `ai_policy.can_promote()` | `outliers.py:L1610` | AI 영상 승격 정책 체크 |
| **3. RemixNode 생성** | `RemixNode` 생성 | `outliers.py:L1640` | 부모 노드 생성 |
| **4. 상태 업데이트** | status=PROMOTED | `outliers.py:L1660-1672` | 승격 완료 |
| **5. VDG 분석 시작** | `background_tasks.add_task()` | `outliers.py:L1677-1692` | 백그라운드 실행 |

#### 요청 스키마

```python
class OutlierPromoteRequest(BaseModel):
    campaign_eligible: bool = False
    matched_rule_id: Optional[UUID] = None
    rule_followed: Optional[bool] = None
    notes: Optional[str] = None
    skip_comments: bool = False  # 댓글 없이 VDG 분석 진행 옵션
```

---

## 3. 플랫폼별 메타데이터 추출

### 3.1 TikTok

```
경로: outliers.py L554-612

1. extract_tiktok_complete(url, include_comments=False)
   ├── TikTokUnifiedExtractor._extract_with_playwright()
   │   ├── Playwright로 페이지 로드
   │   ├── UNIVERSAL_DATA JSON 파싱
   │   └── XHR API 응답 캡처
   └── 반환: view_count, like_count, share_count, comment_count, author, upload_date

2. oEmbed 썸네일 (L584-596)
   └── https://www.tiktok.com/oembed?url={canonical_url}

3. 댓글 게이트 (L598-606)
   └── tiktok_data.comment_count == 0 && !skip_comments
       → HTTPException(400, "COMMENT_EXTRACTION_FAILED_TIKTOK")
```

### 3.2 YouTube

```
경로: outliers.py L614-681

1. YouTubeCrawler._get_video_details([video_id])
   └── YouTube Data API v3 호출
       └── snippet + statistics

2. statistics 추출 (L631-655)
   ├── viewCount, likeCount
   └── commentCount 체크
       └── 없으면 && !skip_comments
           → HTTPException(400, "COMMENT_DISABLED_YOUTUBE")

3. 썸네일 추출 (L662-669)
   └── maxres > high > medium 우선순위
```

### 3.3 Instagram

```
경로: outliers.py L683-724

1. extract_social_metadata(url)
   └── yt-dlp 기반 추출
       └── view_count, like_count, comment_count, author

2. 댓글 게이트 (L711-719)
   └── ig_comment_count == 0 && !skip_comments
       → HTTPException(400, "COMMENT_EXTRACTION_FAILED_INSTAGRAM")
```

---

## 3.4 YouTube 영상 다운로드 (2026-01 업데이트)

> [!IMPORTANT]
> **Railway/Datacenter 환경에서 YouTube 봇 감지 우회를 위한 3단계 폴백 전략**

### 다운로드 전략 (3-Stage Fallback)

```mermaid
flowchart TD
    A["YouTube URL"] --> B["1. JSON Parsing"]
    B -->|실패| C["2. yt-dlp + Residential Proxy<br/>YOUTUBE_PROXY"]
    C -->|실패| D["3. yt-dlp without Proxy"]
    B -->|성공| E["✅ Download Complete"]
    C -->|성공| E
    D -->|성공| E
    D -->|실패| F["❌ RuntimeError"]
```

| 단계 | 방법 | 환경 | 성공률 |
|------|------|------|--------|
| **1** | JSON parsing (빠른 실패) | 로컬/Railway | ~10% (signatureCipher) |
| **2** | yt-dlp + `YOUTUBE_PROXY` | Railway | ~80% ✅ |
| **3** | yt-dlp without proxy | 로컬 only | ~90% (로컬) |

### yt-dlp 2026-01 최적화 설정

```python
# video_downloader.py - _download_youtube_with_ytdlp()
ydl_opts = {
    'format': 'best[ext=mp4]/best[height<=720]/best',  # SABR 우회: 합쳐진 포맷
    'fragment_retries': 5,                              # 재시도 증가 (3→5)
    'skip_unavailable_fragments': True,                 # 손상된 fragment 스킵
    'sleep_interval': 1,
    'max_sleep_interval': 3,
    'extractor_args': {
        'youtube': {
            'formats': 'missing_pot',  # ✅ 문자열! (리스트 아님)
            # ❌ player_client 제거됨 - ios/android 차단 (2024)
        }
    },
}
```

### 주요 수정 사항 (2026-01-23)

| 항목 | 변경 전 ❌ | 변경 후 ✅ |
|------|-----------|-----------|
| `formats` | `['missing_pot']` (리스트) | `'missing_pot'` (문자열) |
| `player_client` | `['android_sdkless','ios','tv']` | **제거됨** (자동 관리) |
| `fragment_retries` | 3 | 5 |
| `skip_unavailable_fragments` | N/A | `True` |
| **예상 안정성** | 70-75% | 75-80% |

### 환경변수 설정 (Railway)

```bash
# Residential Proxy (DataImpulse 예시)
railway variables set YOUTUBE_PROXY="socks5://user:pass@gw.dataimpulse.com:823"
```

> [!TIP]
> **TikTok은 프록시 불필요** - Datacenter IP 차단 없음. `TIKTOK_PROXY`는 설정하지 않거나 삭제.

### 의존성 추가

```
# requirements.txt
ffmpeg-python>=0.2.0,<1.0.0  # VDG 프레임 추출용
```

---

## 4. 댓글 게이트 (Comment Gate)

### 4.1 제출 시점 체크

| 플랫폼 | 체크 위치 | 조건 | 에러 코드 |
|--------|----------|------|-----------|
| YouTube | L646-654 | `commentCount` 없음 | `COMMENT_DISABLED_YOUTUBE` |
| TikTok | L598-606 | `comment_count == 0` | `COMMENT_EXTRACTION_FAILED_TIKTOK` |
| Instagram | L711-719 | `comment_count == 0` | `COMMENT_EXTRACTION_FAILED_INSTAGRAM` |

### 4.2 Skip Comments 옵션

사용자가 댓글 없이 분석을 원하면 `skip_comments=true`로 재전송:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend

    User->>Frontend: 영상 URL 제출
    Frontend->>Backend: POST /items/manual
    Backend-->>Frontend: 400 COMMENT_EXTRACTION_FAILED_*
    Frontend->>User: "댓글 없이 분석?" 버튼 표시
    User->>Frontend: 버튼 클릭
    Frontend->>Backend: POST /items/manual (skip_comments=true)
    Backend-->>Frontend: 201 Created
    Frontend->>User: 등록 완료 (댓글 없이)
```

### 4.3 VDG 분석 시점 게이트 (Tier 기반)

| 조건 | 동작 | HTTP 코드 |
|------|------|-----------|
| `skip_comments=true` | 빈 댓글로 진행 | 200 |
| S/A tier + 댓글 실패 | `comments_pending_review` 상태 → 수동 리뷰 대기 | 202 |
| B/C tier + 댓글 실패 | `comments_failed` 상태 → VDG 차단 | 503 |

---

## 5. VDG 분석 파이프라인

### 5.1 함수 시그니처

```python
async def _run_vdg_analysis_with_comments(
    item_id: str,
    node_id: str,
    video_url: str,
    platform: str,
    user_id: str = None,
    skip_comments: bool = False,  # 댓글 없이 분석 옵션
):
```

### 5.2 파이프라인 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│  _run_vdg_analysis_with_comments(item_id, node_id, video_url)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RLS 컨텍스트 설정                                            │
│     └── app.current_user_id, app.is_admin                       │
│                                                                 │
│  2. 기존 댓글 확인 (OutlierItem.best_comments)                  │
│     └── 있으면 댓글 추출 스킵                                    │
│                                                                 │
│  3. 댓글 추출                                                   │
│     ├── TikTok: extract_tiktok_complete(include_comments=True)  │
│     │   └── top_comments 반환                                   │
│     └── YouTube/IG: extract_best_comments()                     │
│         └── comment_extractor.py 사용                           │
│                                                                 │
│  4. 댓글 체크 게이트                                             │
│     ├── skip_comments=True → 빈 댓글로 진행                     │
│     │   └── comments_missing_reason = "skip_comments_requested" │
│     ├── S/A tier → comments_pending_review (202)                │
│     └── B/C tier → comments_failed (503)                        │
│                                                                 │
│  5. Gemini VDG 분석                                             │
│     └── gemini_pipeline.analyze_video_v4(url, comments)         │
│                                                                 │
│  6. VDG Meta 플래그 설정                                        │
│     ├── meta.comments_analyzed = len(comments) > 0              │
│     └── meta.analysis_type = "outlier_skip" | "outlier_full"    │
│                                                                 │
│  7. DB 저장                                                     │
│     ├── RemixNode.gemini_analysis = vdg_snapshot                │
│     ├── OutlierItem.best_comments = best_comments               │
│     └── OutlierItem.analysis_status = "completed"               │
│                                                                 │
│  8. 후속 처리                                                   │
│     ├── DirectorPack 캐시 계산                                   │
│     ├── CurationDecision 업데이트                                │
│     ├── VDG Quality 검증                                        │
│     ├── 패턴 클러스터링                                          │
│     └── NotebookLibrary 저장                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. DB 테이블 관계

```mermaid
erDiagram
    OutlierItem {
        uuid id PK
        string video_url UK
        string platform
        int view_count
        int like_count
        int comment_count
        json best_comments
        string analysis_status
        string comments_missing_reason
        bool skip_comments
        uuid promoted_to_node_id FK
        uuid cluster_id FK
    }

    RemixNode {
        uuid id PK
        string node_id UK
        string source_video_url
        json gemini_analysis
        string platform
        uuid parent_node_id FK
    }

    PatternCluster {
        uuid id PK
        string cluster_id UK
        json aggregated_dna
        json centroid_embedding
        int member_count
    }

    NotebookLibraryEntry {
        uuid id PK
        uuid parent_node_id FK
        string cluster_id FK
        json analysis_schema
        string temporal_phase
        float novelty_decay_score
    }

    EvidenceSnapshot {
        uuid id PK
        uuid parent_node_id FK
        json depth1_summary
        string period
        float confidence
    }

    OutlierItem ||--o| RemixNode : "promoted_to"
    OutlierItem }o--o| PatternCluster : "cluster"
    RemixNode ||--o{ NotebookLibraryEntry : "library"
    RemixNode ||--o{ EvidenceSnapshot : "evidence"
    PatternCluster ||--o{ NotebookLibraryEntry : "cluster"
```

---

## 7. 주요 필드 설명

### 7.1 OutlierItem

| 필드 | 타입 | 소스 | 설명 |
|------|------|------|------|
| `video_url` | string | 입력 | 정규화된 canonical URL |
| `view_count` | int | 메타데이터 추출 | 조회수 |
| `like_count` | int | 메타데이터 추출 | 좋아요 수 |
| `comment_count` | int | 메타데이터 추출 | 댓글 수 (게이트용) |
| `best_comments` | json | VDG 파이프라인 | 상위 10개 바이럴 댓글 |
| `analysis_status` | string | VDG 파이프라인 | pending/analyzing/completed/comments_failed/comments_pending_review |
| `comments_missing_reason` | string | 댓글 게이트 | 댓글 없는 이유 (skip_comments_requested, blocked, timeout 등) |
| `skip_comments` | bool | 사용자 선택 | 댓글 없이 분석 플래그 |
| `outlier_score` | float | 메타데이터 계산 | 아웃라이어 점수 |
| `outlier_tier` | string | 메타데이터 계산 | S/A/B/C 등급 |

### 7.2 RemixNode

| 필드 | 타입 | 소스 | 설명 |
|------|------|------|------|
| `gemini_analysis` | json | VDG 분석 | 전체 VDG v4 결과 |
| `source_video_url` | string | OutlierItem | 원본 영상 URL |
| `director_pack_cache` | json | 캐시 계산 | 프리컴파일된 DirectorPack |

### 7.3 VDG Meta 플래그

| 필드 | 타입 | 설명 |
|------|------|------|
| `meta.comments_analyzed` | bool | 댓글 분석 포함 여부 |
| `meta.analysis_type` | string | `outlier_full` (댓글 포함) / `outlier_skip` (댓글 제외) / `lab` (Lab 분석) |
| `meta.schema_version` | string | VDG 스키마 버전 (현재 4.0.2) |

---

## 8. 에러 코드 및 대응

| 코드 | HTTP | 의미 | 프론트엔드 대응 |
|------|------|------|----------------|
| `COMMENT_DISABLED_YOUTUBE` | 400 | YouTube 댓글 비활성화 | Skip comments 옵션 표시 |
| `COMMENT_EXTRACTION_FAILED_TIKTOK` | 400 | TikTok 댓글 추출 실패 | Skip comments 옵션 표시 |
| `COMMENT_EXTRACTION_FAILED_INSTAGRAM` | 400 | Instagram 댓글 추출 실패 | Skip comments 옵션 표시 |

### 8.1 i18n 메시지

**한국어** (`messages/ko.json`):
```json
{
  "outliers": {
    "manual": {
      "errors": {
        "COMMENT_DISABLED_YOUTUBE": "이 YouTube 영상은 댓글이 비활성화되어 있습니다...",
        "COMMENT_EXTRACTION_FAILED_TIKTOK": "이 TikTok 영상은 댓글을 추출할 수 없습니다...",
        "COMMENT_EXTRACTION_FAILED_INSTAGRAM": "이 Instagram 영상은 댓글을 추출할 수 없습니다..."
      }
    }
  }
}
```

---

## 9. 댓글 추출기 분류

| 플랫폼 | 메타데이터 추출기 | 댓글 추출기 |
|--------|------------------|------------|
| **TikTok** | `tiktok_extractor.extract_tiktok_complete(include_comments=False)` | `extract_tiktok_complete(include_comments=True)` |
| **YouTube** | `YouTubeCrawler._get_video_details()` | `comment_extractor.extract_best_comments()` |
| **Instagram** | `social_metadata.extract_social_metadata()` | `comment_extractor.extract_best_comments()` |

---

## 10. 확장 파이프라인 (VDG 분석 이후)

```mermaid
flowchart TD
    VDG["VDG 분석 완료<br/>gemini_analysis"]

    VDG --> QUALITY["VDG Quality 검증<br/>vdg_quality_validator"]
    QUALITY --> CURATION["CurationDecision 업데이트"]

    VDG --> CLUSTER["패턴 클러스터링<br/>PatternClusteringService"]
    CLUSTER --> DNA["DNA 집계<br/>IncrementalDNAAggregator"]

    VDG --> NOTEBOOK["NotebookLM 저장<br/>NotebookLibraryEntry"]
    NOTEBOOK --> EVIDENCE["Evidence 생성<br/>EvidenceSnapshot"]

    subgraph FORK["Fork 생성 시"]
        FORK_CREATE["Fork 생성"] --> NEO4J["Neo4j EVOLVED_TO<br/>가계도 엣지"]
        FORK_CREATE --> VDGEDGE["VDGEdge (PG)<br/>듀얼 기록"]
    end
```

---

## 11. 서비스 의존성 맵

| 서비스 | 파일 | 역할 |
|--------|------|------|
| `TikTokUnifiedExtractor` | `tiktok_extractor.py` | TikTok 메타데이터 + 댓글 추출 |
| `YouTubeCrawler` | `youtube.py` | YouTube Data API v3 |
| `extract_social_metadata` | `social_metadata.py` | Instagram yt-dlp 추출 |
| `extract_best_comments` | `comment_extractor.py` | YouTube/Instagram 댓글 추출 |
| `gemini_pipeline` | `gemini_pipeline.py` | VDG v4 분석 |
| `PatternClusteringService` | `clustering.py` | 하이브리드 클러스터링 |
| `IncrementalDNAAggregator` | `incremental_dna_aggregator.py` | 클러스터 DNA 집계 |
| `compute_and_cache_director_pack` | `director_pack_cache.py` | DirectorPack 프리컴파일 |
| `validate_vdg_quality` | `vdg_quality_validator.py` | VDG 품질 검증 |

---

## 12. 관련 문서

| 문서 | 설명 |
|------|------|
| [02_VDG.md](./02_VDG.md) | VDG 2-Pass 기술 스펙 |
| [23_VDG_OPS_RUNBOOK.md](./23_VDG_OPS_RUNBOOK.md) | VDG 운영 런북 |
| [26_PATTERN_CLUSTERING.md](./26_PATTERN_CLUSTERING.md) | 패턴 클러스터링 |
| [09_NOTEBOOKLM_INTEGRATION.md](./09_NOTEBOOKLM_INTEGRATION.md) | NotebookLM 통합 |

---

## Changelog

- **v1.1.0** (2026-01-23): YouTube 다운로드 파이프라인 개선
  - 3단계 폴백 전략 추가 (JSON parsing → yt-dlp+Proxy → yt-dlp)
  - yt-dlp extractor_args 수정: `formats` 리스트→문자열, `player_client` 제거
  - `ffmpeg-python` 의존성 추가 (VDG 프레임 추출)
  - Railway 환경변수: `YOUTUBE_PROXY`, `TIKTOK_PROXY` 삭제
- **v1.0.0** (2026-01-22): 초기 작성
  - 댓글 게이트 시스템 문서화
  - skip_comments 옵션 추가
  - 플랫폼별 메타데이터 추출 흐름 정리
  - VDG 분석 파이프라인 상세 흐름 추가
