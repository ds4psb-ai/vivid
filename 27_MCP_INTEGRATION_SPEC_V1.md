# MCP Integration Specification (SPEC v36)

**Date**: 2025-12-28  
**Status**: SoR (MCP 통합 가이드라인)  
**Author**: Antigravity Agent  
**Goal**: Crebit 프로젝트에 적합한 MCP(Model Context Protocol) 서버 선정 및 통합 전략 정의

---

## 0) 개요

MCP(Model Context Protocol)는 LLM과 외부 데이터/도구를 연결하는 **오픈 표준**이다.  
Anthropic이 2024년 11월 오픈소스화했으며, 2025년 현재 OpenAI, Google, Amazon 등 주요 AI 기업이 채택 중이다.

**핵심 가치**:
- AI 에이전트가 실시간 데이터/도구에 접근 가능
- 표준화된 인터페이스로 도구 교체 용이
- "USB-C for AI" 비유 - 범용 연결 규격

**참조**:
- 공식 레지스트리: `https://registry.modelcontextprotocol.io`
- GitHub: `https://github.com/modelcontextprotocol`
- 스펙 문서: `https://modelcontextprotocol.io`

---

## 1) Crebit MCP 스택 권장안

### Tier 1: 즉시 적용 (공식/안정)

| MCP 서버 | 용도 | 상태 | 비용 | 소스 |
|----------|------|------|------|------|
| **Playwright MCP** | E2E 테스트, 브라우저 자동화 | ✅ 공식 (Microsoft) | 무료 | [GitHub](https://github.com/microsoft/playwright-mcp) |
| **Filesystem MCP** | 로컬 파일 읽기/쓰기 | ✅ 공식 레퍼런스 | 무료 | [MCP Servers](https://modelcontextprotocol.io/examples) |
| **Git MCP** | 버전 관리 자동화 | ✅ 공식 레퍼런스 | 무료 | [MCP Servers](https://modelcontextprotocol.io/examples) |
| **Fetch MCP** | 웹 콘텐츠 가져오기 | ✅ 공식 레퍼런스 | 무료 | [MCP Servers](https://modelcontextprotocol.io/examples) |
| **Tavily MCP** | LLM 최적화 웹 검색 | ✅ 공식 레퍼런스 | 1,000 credits/월 무료 | [tavily-mcp](https://github.com/tavily-ai/tavily-mcp) |

### Tier 2: 프로덕션급 (유료 또는 Free Tier)

| MCP 서버 | 용도 | 상태 | 비용 | 소스 |
|----------|------|------|------|------|
| **Google Sheets MCP** | Sheets Bus 연동 | ✅ 공식 출시 (Dec 2025) | 무료 (쿼터) | [GitHub](https://github.com/anthropics/mcp-google-sheets) |
| **Google Drive MCP** | 파일 관리 | ✅ 공식 출시 (Dec 2025) | 무료 (쿼터) | [GitHub](https://github.com/anthropics/mcp-google-drive) |
| **Qdrant MCP** | 벡터 시맨틱 검색 | ✅ 오픈소스 + Managed | Free tier | [GitHub](https://github.com/qdrant/mcp-server-qdrant) |

### Tier 3: 조건부/비권장

| MCP 서버 | 상태 | 이유 | 대안 |
|----------|------|------|------|
| **PostgreSQL MCP** | ⚠️ 아카이브됨 | 공식 레퍼런스 deprecated | SQLAlchemy 직접 사용 |
| **Gemini MCP** | ⚠️ 커뮤니티 | 공식 아님, 범용 LLM 연결 | Gemini API 직접 호출 |
| **Memory MCP** | ⚠️ 오해 주의 | KG 아님, pgvector 기반 | Qdrant 사용 |
| **Perplexity Sonar** | ❌ 무료 티어 없음 | 유료만 제공 | Tavily 사용 |
| **Exa AI** | ⚠️ 비용 복잡 | 결과수별 차등 과금 | Tavily 사용 |

---

## 2) 상세 스펙

### 2.1 Playwright MCP (✅ 권장)

**개요**: Microsoft 공식, LLM이 브라우저와 상호작용할 수 있게 해주는 MCP 서버

**기능**:
- Accessibility 스냅샷 기반 (픽셀 아님)
- 결정론적, 빠름, AI 호환성 높음
- AI 기반 테스트 생성
- 크로스 브라우저 지원 (Chrome, Firefox, WebKit)

**Crebit 활용**:
```python
# E2E 테스트 자동화
# Canvas UI 검증
# 스크린샷/녹화 기반 문서화
```

**설치**:
```bash
npm install @playwright/mcp
```

**설정**:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

---

### 2.2 Tavily MCP Server (✅ 권장)

**개요**: LLM/RAG용 AI 네이티브 웹 검색 API를 위한 공식 MCP 서버

**기능**:
- Web Search optimized for LLMs (광고 제거, 메타데이터 풍부)
- 답변 생성에 필요한 Context만 추출
- RAG 파이프라인 최적화

**설치 및 설정 (Dual Mode)**:
안정성을 위해 **Local**을 기본으로 하고, **Remote**를 백업으로 설정합니다.

```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": { "TAVILY_API_KEY": "..." }
    },
    "tavily-remote": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.tavily.com/mcp/?tavilyApiKey=..."]
    }
  }
}
```

**비용**:
- Free Tier: 월 1,000 크레딧
- 비용 효율성: Exa 대비 단순한 과금 체계

**Crebit 활용**:
```python
from tavily import TavilyClient

client = TavilyClient(api_key="YOUR_KEY")
results = client.search(
    query="봉준호 감독 영화 촬영 기법",
    search_depth="advanced",
    max_results=5
)
```

**MCP 설정**:
```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["tavily-mcp"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

---

### 2.3 Qdrant MCP (✅ 벡터 검색용)

**개요**: 오픈소스 벡터 DB + MCP 브릿지

**기능**:
- 시맨틱 메모리 for AI 에이전트
- billion-scale 벡터 검색
- Managed Cloud (SSO/RBAC 2025 출시)

**Crebit 활용**:
```python
# PatternCandidate 시맨틱 검색
# EvidenceRecord 유사도 매칭
# Template 추천 시스템
```

**설정**:
```json
{
  "mcpServers": {
    "qdrant": {
      "command": "npx",
      "args": ["@qdrant/mcp-server"],
      "env": {
        "QDRANT_URL": "http://localhost:6333"
      }
    }
  }
}
```

---

### 2.4 Google Sheets MCP (⏳ 출시 대기)

**개요**: Google 공식 Managed MCP 서버 (2025.12 발표)

**현재 상태**:
- 커뮤니티 서버 존재
- 공식 Managed 서버 출시 예정 (Cloud Storage, Cloud SQL 포함)

**Crebit 활용**:
```python
# Sheets Bus (CREBIT_DERIVED_INSIGHTS) 직접 연동
# promote_from_sheets.py 자동화 강화
```

**임시 대안** (공식 출시 전):
- 기존 Google Sheets API 직접 사용
- `gspread` 라이브러리 유지

---

## 3) 비적용 항목 상세

### 3.1 PostgreSQL MCP ❌

**상태**: 공식 레퍼런스 **아카이브됨**

**근거**:
- `github.com/modelcontextprotocol/servers/README.md` 에서 archived 분류
- Azure Postgres MCP는 **Preview** 단계

**Crebit 대책**:
```python
# SQLAlchemy AsyncSession 유지
from app.database import get_db
```

> [!WARNING]
> PostgreSQL MCP를 즉시 적용 안전하다고 판단하면 안 됨

---

### 3.2 Gemini MCP ❌

**상태**: 커뮤니티 수준 (공식 아님)

**근거**:
- `mcp-server-gemini` 등 커뮤니티 프로젝트 존재
- 공식 MCP 레지스트리에 **등재되지 않음**
- "Video Understanding 핵심"으로 보기 어려움

**Crebit 대책**:
```python
# Gemini API 직접 호출 유지
from app.generation_client import GeminiClient
```

---

### 3.3 Exa AI ⚠️

**상태**: 유료, 비용 구조 복잡

**가격표** (2025.12 기준):
| 항목 | 비용 |
|------|------|
| Search (1-25 results) | $5 / 1,000 req |
| Search (26-100 results) | $25 / 1,000 req |
| Contents | $5-25 / 1,000 req |
| Deep Search | $15 / 1,000 req |

**결론**: Tavily로 대체 권장

---

## 4) 통합 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Crebit MCP Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Playwright  │   │   Tavily    │   │   Qdrant    │       │
│  │    MCP      │   │    MCP      │   │    MCP      │       │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
│         │                 │                 │               │
│         └────────────┬────┴────────────────┘               │
│                      │                                      │
│              ┌───────▼───────┐                             │
│              │   MCP Client  │                             │
│              │  (Claude CLI) │                             │
│              └───────┬───────┘                             │
│                      │                                      │
│  ════════════════════╪══════════════════════════════════   │
│                      │                                      │
│         ┌────────────▼────────────┐                        │
│         │    Crebit Backend        │                        │
│         │   (FastAPI + Gemini)    │                        │
│         └────────────┬────────────┘                        │
│                      │                                      │
│    ┌─────────┬───────┼───────┬─────────┐                   │
│    ▼         ▼       ▼       ▼         ▼                   │
│ Gemini   PostgreSQL  Sheets   S3    NotebookLM             │
│  API     (직접연결)  Bus    Storage   (직접)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5) 구현 로드맵

### Phase 1: 즉시 (Week 1)
- [ ] Playwright MCP 설정 및 E2E 테스트 연동
- [ ] Tavily API 키 발급 및 테스트

### Phase 2: 단기 (Week 2-3)
- [ ] Qdrant MCP 로컬 셋업
- [ ] PatternCandidate 시맨틱 검색 POC

### Phase 3: 중기 (Month 2)
- [ ] Google Sheets MCP 공식 출시 시 마이그레이션
- [ ] 전체 MCP 스택 프로덕션 배포

---

## 6) 검증된 사실 (웹서치 근거)

| 항목 | 사실 | 출처 |
|------|------|------|
| Exa 유료 | 결과수/콘텐츠별 차등 과금 | exa.ai/pricing |
| Tavily 무료 | 1,000 credits/월 | help.tavily.com |
| Brave Search 무료 | 2,000 req/월 | api-dashboard.search.brave.com |
| Serper 무료 | 2,500 queries | serper.dev |
| Firecrawl 무료 | 500 credits | firecrawl.dev/pricing |
| Perplexity 유료만 | 무료 티어 없음 | docs.perplexity.ai/pricing |
| YouTube API 쿼터 | 요청당 1+ 포인트 | developers.google.com |
| PostgreSQL MCP | 아카이브됨 | github.com/modelcontextprotocol |
| Playwright MCP | Microsoft 공식 | github.com/microsoft/playwright-mcp |

---

## 7) 참조 문서

- `27_AUTEUR_PIPELINE_E2E_CODEX.md` - 파이프라인 정의
- `05_CAPSULE_NODE_SPEC.md` - 캡슐 노드 계약
- `25_VIDEO_UNDERSTANDING_PIPELINE_CODEX.md` - Gemini 영상 분석
- `21_DOCUMENTATION_AUDIT_REPORT_V1.md` - 문서 감사 현황

---

## 8) 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2025-12-28 | 초기 작성 |
